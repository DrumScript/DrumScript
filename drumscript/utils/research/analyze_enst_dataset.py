# drumscript/utils/research/analyze_enst_dataset.py

"""
Utility script to diagnose DrumScript classification against the ENST-Drums dataset.

Full-kit coverage: Like MDB-Drums, ENST-Drums annotates toms, ride and crash, so
this script reports on every class the adapter exposes rather than on one
instrument. It mirrors analyze_mdb_dataset.py so the two outputs line up.

ENST specifics: Three drummers (drummer_1/2/3), each with a wet_mix and a
dry_mix drum recording, and four recording types (hits / phrase / solo /
minus-one). Recording type is the bucket; the drummer is the prefix of the
track id, so --tracks drummer_2 selects one drummer.

Stage attribution: For every reference onset of every class, the script reports
which pipeline stage lost it (no_onset / gated / misclassified / ok), and for
misclassified hits, what the classifier labelled it instead.

Feature profiling: For onsets carrying exactly one reference class, the script
reports the distribution of every physics feature. Comparing those distributions
against the live thresholds shows why a rule never fires.

Adapter-driven: Instrument codes and their DrumScript labels are read from the
ENST adapter, not hardcoded here, so the script follows the adapter if it changes.

Standardised imports: All import statements are separated onto individual lines.

Sphinx documentation: Standard reST docstrings are applied to all functions.

Usage:

## FLAGS
uv run --extra dev python drumscript/utils/research/analyze_enst_dataset.py benchmarks/datasets/ENST-drums-public
--audio dry_mix
--subset minus-one
--tracks drummer_2
--limit 5
--instrument ride
--profile-csv outputs/benchmarks/enst/diagnostics/<stamp>/onset_features.csv

## PREVIOUS PATH (before datasets kept their native folder names)
## uv run --extra dev python drumscript/utils/research/analyze_enst_dataset.py benchmarks/datasets/ENST
"""

import argparse
import csv
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import numpy as np

# --- Make the repo root importable when run as a plain script ---
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from drumscript.audio_processor.audio_loader import load_audio, normalise_audio
from drumscript.audio_processor.onset_detector import detect_onsets
from drumscript.datasets import enst as enst_adapter
from drumscript.drum_classifier.classify import classify_events
from drumscript.notation_generator import constants
from drumscript.notation_generator.constants import SAMPLE_RATE

# --- Diagnosis constants ---
ONSET_WINDOW = 0.050  # 50 ms, matches benchmarks/run.py
FEATURE_KEYS = ("peak_freq", "lfer", "hfer", "hfer_5k", "centroid", "decay")
STAGES = ("ok", "misclassified", "gated", "no_onset")

HIT_FIELDS = ["track", "bucket", "code", "ref_time", "stage", "offset_ms", "labelled_as", *FEATURE_KEYS]
SUMMARY_FIELDS = ["track", "bucket", "code", "n_ref", *STAGES]
ONSET_FIELDS = ["track", "bucket", "event_time", "labelled_as", "ref_codes", "n_ref_codes", *FEATURE_KEYS]
PROFILE_FIELDS = ["code", "n", "feature", "min", "p05", "p25", "median", "p75", "p95", "max"]

# Live thresholds worth seeing beside the feature distributions. Names are read
# from constants where they exist; the crash/ride centroid split is a literal
# inside classify_events, so it is listed explicitly.
THRESHOLD_NAMES = (
    "KICK_FREQ_MIN",
    "KICK_FREQ_MAX",
    "KICK_LFER_MIN",
    "SNARE_FREQ_MIN",
    "SNARE_FREQ_MAX",
    "SNARE_HFER_MIN",
    "TOM_MIN_DECAY",
    "TOM_FREQ_LOW_MAX",
    "TOM_FREQ_MID_MAX",
    "IDIOPHONE_MIN_HFER_5K",
    "HAT_CLOSED_MAX_DECAY",
    "HAT_OPEN_MAX_DECAY",
    "CYMBAL_MIN_DECAY",
    "CYMBAL_CENTROID_THRESHOLD",
)
LIVE_CRASH_RIDE_CENTROID = 2500.0  # Hardcoded inside classify_events, not read from constants.


# ── helpers ──────────────────────────────────────────────────────────────────


def nearest_time(times, target):
    """
    Finds the time closest to a target.

    :param times: Sequence of times in seconds.
    :type times: list[float]
    :param target: Target time in seconds.
    :type target: float
    :return: Tuple of (index, distance in seconds), or (None, inf) if times is empty.
    :rtype: tuple
    """
    if len(times) == 0:
        return None, float("inf")
    arr = np.asarray(times, dtype=float)
    idx = int(np.argmin(np.abs(arr - target)))
    return idx, float(abs(arr[idx] - target))


def copy_features(row, features):
    """
    Copies the tracked feature values from a debug_features dict into a row.

    :param row: The output row being built.
    :type row: dict
    :param features: The debug_features dict returned by classify_events.
    :type features: dict
    """
    for key in FEATURE_KEYS:
        if key in features:
            row[key] = round(float(features[key]), 4)


def adapter_namespace(root, audio=None, subset=None):
    """
    Builds the argparse namespace the ENST adapter expects.

    The adapter declares its own CLI flags, so they are parsed here rather than
    assumed. Any flag not passed keeps the adapter's own default.

    :param root: Path to the ENST dataset root folder.
    :type root: str
    :param audio: Optional audio folder (wet_mix or dry_mix).
    :type audio: str
    :param subset: Optional recording type (hits, phrase, solo or minus-one).
    :type subset: str
    :return: Namespace suitable for enst_adapter.iter_items.
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(add_help=False)
    enst_adapter.add_cli_args(parser)
    argv = ["--root", str(root)]
    if audio:
        argv += ["--audio", audio]
    if subset:
        argv += ["--subset", subset]
    return parser.parse_args(argv)


def print_live_thresholds():
    """Prints the live classification thresholds, for comparison against the profiles."""
    print("\n-- Live thresholds --")
    for name in THRESHOLD_NAMES:
        value = getattr(constants, name, None)
        if value is not None:
            print(f"  {name:<28}{value}")
    print(f"  {'crash/ride centroid split':<28}{LIVE_CRASH_RIDE_CENTROID}  (literal in classify_events)")


# ── per-track diagnosis ──────────────────────────────────────────────────────


def reference_codes_at(item, event_time):
    """
    Returns every reference code with an annotated onset near an event.

    :param item: A BenchmarkItem from the ENST adapter.
    :type item: drumscript.datasets.base.BenchmarkItem
    :param event_time: Event time in seconds.
    :type event_time: float
    :return: Sorted list of matching reference codes.
    :rtype: list[str]
    """
    codes = []
    for code, times in item.references.items():
        _, dist = nearest_time(times, event_time)
        if dist <= ONSET_WINDOW:
            codes.append(code)
    return sorted(codes)


def diagnose_track(item, code_to_labels):
    """
    Attributes every reference onset in one track to the stage that lost it.

    :param item: A BenchmarkItem from the ENST adapter.
    :type item: drumscript.datasets.base.BenchmarkItem
    :param code_to_labels: Mapping of dataset code to DrumScript label list.
    :type code_to_labels: dict
    :return: Tuple of (hit rows, onset rows, summary rows).
    :rtype: tuple
    """
    audio, sr = load_audio(str(item.audio_path), sr=SAMPLE_RATE)
    audio = normalise_audio(audio)
    onsets = detect_onsets(audio, sr)
    events = classify_events(audio, sr, onsets)
    event_times = [e["time_sec"] for e in events]

    hit_rows = []
    summary_rows = []

    for code, ref_times in item.references.items():
        labels = code_to_labels.get(code, [code])
        rows = []
        for ref_time in ref_times:
            row = {"track": item.track_id, "bucket": item.bucket, "code": code, "ref_time": round(float(ref_time), 4)}

            _, onset_dist = nearest_time(onsets, ref_time)
            ev_idx, ev_dist = nearest_time(event_times, ref_time)

            if onset_dist > ONSET_WINDOW:
                row["stage"] = "no_onset"
            elif ev_dist > ONSET_WINDOW:
                row["stage"] = "gated"
            else:
                event = events[ev_idx]
                row["offset_ms"] = round((event["time_sec"] - ref_time) * 1000, 1)
                row["labelled_as"] = "+".join(event["instruments"])
                copy_features(row, event.get("debug_features", {}))
                row["stage"] = "ok" if any(label in event["instruments"] for label in labels) else "misclassified"
            rows.append(row)

        counts = Counter(r["stage"] for r in rows)
        summary_rows.append(
            {
                "track": item.track_id,
                "bucket": item.bucket,
                "code": code,
                "n_ref": len(rows),
                **{stage: counts.get(stage, 0) for stage in STAGES},
            }
        )
        hit_rows.extend(rows)

    onset_rows = []
    for event in events:
        event_time = float(event["time_sec"])
        codes = reference_codes_at(item, event_time)
        row = {
            "track": item.track_id,
            "bucket": item.bucket,
            "event_time": round(event_time, 4),
            "labelled_as": "+".join(event["instruments"]),
            "ref_codes": "+".join(codes),
            "n_ref_codes": len(codes),
        }
        copy_features(row, event.get("debug_features", {}))
        onset_rows.append(row)

    return hit_rows, onset_rows, summary_rows


# ── reporting ────────────────────────────────────────────────────────────────


def print_stage_table(hit_rows, codes):
    """
    Prints stage attribution totals per instrument code.

    :param hit_rows: Per-reference rows from diagnose_track.
    :type hit_rows: list[dict]
    :param codes: Instrument codes, in display order.
    :type codes: tuple
    """
    print("\n-- Where reference hits were lost, by class --")
    print(f"  {'code':<16}{'n_ref':>8}{'ok':>8}{'miscl':>8}{'gated':>8}{'no_on':>8}{'ok %':>8}")
    print("  " + "-" * 64)
    for code in codes:
        rows = [r for r in hit_rows if r["code"] == code]
        if not rows:
            continue
        counts = Counter(r["stage"] for r in rows)
        ok_pct = 100.0 * counts.get("ok", 0) / len(rows)
        cells = f"{counts.get('ok', 0):>8}{counts.get('misclassified', 0):>8}"
        cells += f"{counts.get('gated', 0):>8}{counts.get('no_onset', 0):>8}"
        print(f"  {code:<16}{len(rows):>8}{cells}{ok_pct:>8.1f}")


def print_confusion(hit_rows, codes, top=4):
    """
    Prints, per class, what the classifier labelled its misclassified hits instead.

    :param hit_rows: Per-reference rows from diagnose_track.
    :type hit_rows: list[dict]
    :param codes: Instrument codes, in display order.
    :type codes: tuple
    :param top: How many alternative labels to show per class.
    :type top: int
    """
    print("\n-- Misclassified hits: what they were labelled instead --")
    for code in codes:
        wrong = [r for r in hit_rows if r["code"] == code and r["stage"] == "misclassified"]
        if not wrong:
            continue
        print(f"  {code} ({len(wrong)} misclassified)")
        for label, n in Counter(r.get("labelled_as", "(none)") for r in wrong).most_common(top):
            print(f"      {label:<34}{n}")


def describe_values(values):
    """
    Returns min, percentiles, median and max for one list of feature values.

    :param values: Feature values.
    :type values: list[float]
    :return: Dictionary of summary statistics.
    :rtype: dict
    """
    arr = np.asarray(values, dtype=float)
    return {
        "min": round(float(arr.min()), 4),
        "p05": round(float(np.percentile(arr, 5)), 4),
        "p25": round(float(np.percentile(arr, 25)), 4),
        "median": round(float(np.median(arr)), 4),
        "p75": round(float(np.percentile(arr, 75)), 4),
        "p95": round(float(np.percentile(arr, 95)), 4),
        "max": round(float(arr.max()), 4),
    }


def build_profiles(onset_rows, codes):
    """
    Builds per-class feature distributions from onsets carrying one reference class.

    Onsets with several simultaneous reference classes are excluded, because their
    features describe the mixture rather than the instrument.

    :param onset_rows: Per-onset rows from diagnose_track.
    :type onset_rows: list[dict]
    :param codes: Instrument codes, in display order.
    :type codes: tuple
    :return: One row per class per feature.
    :rtype: list[dict]
    """
    profiles = []
    for code in codes:
        isolated = [r for r in onset_rows if r["ref_codes"] == code]
        if not isolated:
            continue
        for feature in FEATURE_KEYS:
            values = [r[feature] for r in isolated if feature in r]
            if not values:
                continue
            profiles.append({"code": code, "n": len(values), "feature": feature, **describe_values(values)})
    return profiles


def print_profiles(profiles):
    """
    Prints the per-class feature distributions.

    :param profiles: Rows from build_profiles.
    :type profiles: list[dict]
    """
    print("\n-- Feature distribution per class (onsets with exactly one reference class) --")
    if not profiles:
        print("  (no isolated onsets found)")
        return
    current = None
    for row in profiles:
        if row["code"] != current:
            current = row["code"]
            print(f"\n  {current}  (n={row['n']})")
            print(f"    {'feature':<12}{'min':>10}{'p05':>10}{'median':>10}{'p95':>10}{'max':>10}")
        cells = f"{row['min']:>10.3f}{row['p05']:>10.3f}{row['median']:>10.3f}{row['p95']:>10.3f}{row['max']:>10.3f}"
        print(f"    {row['feature']:<12}{cells}")


def print_never_fired(onset_rows, hit_rows, codes, code_to_labels):
    """
    Flags classes that have reference annotations but were never predicted at all.

    :param onset_rows: Per-onset rows from diagnose_track.
    :type onset_rows: list[dict]
    :param hit_rows: Per-reference rows from diagnose_track.
    :type hit_rows: list[dict]
    :param codes: Instrument codes, in display order.
    :type codes: tuple
    :param code_to_labels: Mapping of dataset code to DrumScript label list.
    :type code_to_labels: dict
    """
    predicted = Counter()
    for row in onset_rows:
        for label in row["labelled_as"].split("+"):
            predicted[label] += 1

    dead = []
    for code in codes:
        n_ref = sum(1 for r in hit_rows if r["code"] == code)
        if not n_ref:
            continue
        n_pred = sum(predicted.get(label, 0) for label in code_to_labels.get(code, [code]))
        if n_pred == 0:
            dead.append((code, n_ref))

    if dead:
        print("\n-- Classes never predicted --")
        for code, n_ref in dead:
            print(f"  [WARNING] {code}: {n_ref} reference hits, 0 predictions. This is an unreachable rule, not a threshold.")


# ── output ───────────────────────────────────────────────────────────────────


def write_dict_csv(path, fields, rows):
    """
    Writes a list of dicts to CSV, leaving missing fields blank.

    :param path: Output file path.
    :type path: pathlib.Path
    :param fields: Column names, in order.
    :type fields: list[str]
    :param rows: Rows to write.
    :type rows: list[dict]
    """
    with open(path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields, restval="")
        writer.writeheader()
        writer.writerows(rows)


def resolve_output_dir(output_dir):
    """
    Resolves the output directory, defaulting to a timestamped diagnostics folder.

    :param output_dir: Optional explicit output directory.
    :type output_dir: str
    :return: The directory to write the CSVs into.
    :rtype: pathlib.Path
    """
    if output_dir:
        return Path(output_dir)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return Path("outputs") / "benchmarks" / "enst" / "diagnostics" / stamp


def load_onset_rows(csv_path):
    """
    Reloads onset rows from a previously written onset_features.csv.

    Lets the feature profiles be rebuilt without re-processing any audio.

    :param csv_path: Path to onset_features.csv.
    :type csv_path: str
    :return: Per-onset rows in the shape diagnose_track produces.
    :rtype: list[dict]
    """
    rows = []
    with open(csv_path, newline="") as fh:
        for record in csv.DictReader(fh):
            row = dict(record)
            for key in FEATURE_KEYS:
                try:
                    row[key] = float(record[key])
                except (KeyError, TypeError, ValueError):
                    row.pop(key, None)
            rows.append(row)
    return rows


# ── main ─────────────────────────────────────────────────────────────────────


def diagnose(root_path, tracks=None, limit=None, instrument=None, output_dir=None, audio=None, subset=None):
    """
    Runs the full-kit diagnosis over the selected ENST tracks.

    :param root_path: Path to the ENST dataset root folder.
    :type root_path: str
    :param tracks: Optional list of substrings; only matching tracks are run.
    :type tracks: list[str]
    :param limit: Optional cap on the number of tracks processed.
    :type limit: int
    :param instrument: Optional single class code to report on.
    :type instrument: str
    :param output_dir: Optional output directory for the CSVs.
    :type output_dir: str
    :param audio: Optional audio folder (wet_mix or dry_mix).
    :type audio: str
    :param subset: Optional recording type (hits, phrase, solo or minus-one).
    :type subset: str
    """
    code_to_labels = dict(enst_adapter.DRUMSCRIPT_DICT)
    codes = tuple(enst_adapter.INSTRUMENT_CODES)
    if instrument:
        codes = tuple(c for c in codes if c == instrument)
        if not codes:
            print(f"Unknown instrument code: {instrument}. Known: {', '.join(enst_adapter.INSTRUMENT_CODES)}")
            return

    items = list(enst_adapter.iter_items(adapter_namespace(root_path, audio=audio, subset=subset)))
    if tracks:
        items = [i for i in items if any(t in i.track_id for t in tracks)]
    if limit:
        items = items[:limit]
    if not items:
        print("No matching tracks found.")
        return

    print(f"\nAudio   : {audio or 'adapter default'}")
    print(f"Subset  : {subset or 'all'}")
    print(f"Window  : {int(ONSET_WINDOW * 1000)} ms")
    print(f"Tracks  : {len(items)}")
    print(f"Classes : {', '.join(codes)}")
    print_live_thresholds()

    all_hits = []
    all_onsets = []
    all_summaries = []
    print("\n-- Processing --")
    for item in items:
        try:
            hits, onset_rows, summaries = diagnose_track(item, code_to_labels)
        except Exception as e:
            print(f"  {item.track_id:<64}[ERROR] {e}")
            continue
        if instrument:
            hits = [h for h in hits if h["code"] in codes]
            summaries = [s for s in summaries if s["code"] in codes]
        all_hits.extend(hits)
        all_onsets.extend(onset_rows)
        all_summaries.extend(summaries)
        print(f"  {item.track_id:<64}onsets={len(onset_rows):<6}refs={len(hits)}")

    if not all_hits:
        print("\nNo reference hits scored.")
        return

    print_stage_table(all_hits, codes)
    print_confusion(all_hits, codes)
    print_never_fired(all_onsets, all_hits, codes, code_to_labels)

    profiles = build_profiles(all_onsets, codes)
    print_profiles(profiles)

    out_dir = resolve_output_dir(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    write_dict_csv(out_dir / "instrument_hits.csv", HIT_FIELDS, all_hits)
    write_dict_csv(out_dir / "instrument_summary.csv", SUMMARY_FIELDS, all_summaries)
    write_dict_csv(out_dir / "onset_features.csv", ONSET_FIELDS, all_onsets)
    write_dict_csv(out_dir / "feature_profile.csv", PROFILE_FIELDS, profiles)
    print(f"\nWritten to {out_dir}/:")
    print("  instrument_hits.csv, instrument_summary.csv, onset_features.csv, feature_profile.csv\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Diagnose DrumScript classification against ENST-Drums.")
    parser.add_argument("dataset_root", type=str, nargs="?", default=None, help="Path to the ENST dataset root folder")
    parser.add_argument("--tracks", nargs="*", default=None, help="Only run tracks whose name contains any of these")
    parser.add_argument("--limit", type=int, default=None, help="Process at most this many tracks")
    parser.add_argument("--instrument", default=None, help="Report on one class code only (e.g. ride)")
    parser.add_argument("--output", default=None, help="Output directory for the CSVs")
    parser.add_argument("--audio", default=None, choices=enst_adapter.AUDIO_CHOICES, help="Drum mix to analyse (adapter default: wet_mix)")
    parser.add_argument("--subset", default=None, choices=enst_adapter.SUBSETS, help="Recording type: hits, phrase, solo or minus-one")
    parser.add_argument("--profile-csv", default=None, help="Rebuild feature profiles from an existing onset_features.csv")

    args = parser.parse_args()

    if args.profile_csv:
        rows = load_onset_rows(args.profile_csv)
        seen = []
        for row in rows:
            if row["ref_codes"] and row["ref_codes"] not in seen and "+" not in row["ref_codes"]:
                seen.append(row["ref_codes"])
        print_live_thresholds()
        print_profiles(build_profiles(rows, tuple(sorted(seen))))
        print()
    elif not args.dataset_root:
        parser.error("dataset_root is required unless --profile-csv is used")
    else:
        diagnose(
            args.dataset_root,
            tracks=args.tracks,
            limit=args.limit,
            instrument=args.instrument,
            output_dir=args.output,
            audio=args.audio,
            subset=args.subset,
        )
