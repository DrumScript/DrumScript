# drumscript/utils/research/analyze_idmt_dataset.py

"""
Utility script to extract frequency metrics and core physical specifications
from the IDMT-SMT-DRUMS-V2 dataset.

Targeted extraction: The script filters for the isolated drum stems (#KD, #SD, #HH)
to measure the precise physics of each instrument without background noise.

Aligned metrics: It calculates peak frequency, decay time, spectral centroid,
and energy ratios to mirror the logic used in the classification engine.

Kick diagnosis (--diagnose-kick): Runs the live DrumScript pipeline on the #MIX
files and reports, for every reference kick, which stage lost it
(no_onset / gated / misclassified / ok), which kick-rule condition failed,
and the features the classifier actually saw. It also captures every detected
onset (kick-bearing or not) and sweeps candidate KICK_LFER_MIN values, so a
threshold change can be judged against false positives rather than recall alone.

Standardised imports: All import statements are separated onto individual lines.

Sphinx documentation: Standard reST docstrings are applied to all functions.

Usage:

## FLAGS
uv run --extra dev python drumscript/utils/research/analyze_idmt_dataset.py benchmarks/datasets/IDMT --group --sort
--group --sort
--group
--sort
--diagnose-kick
--diagnose-kick --tracks WaveDrum02_37 WaveDrum02_39
--diagnose-kick --top 30
--sweep-csv outputs/benchmarks/idmt/diagnostics/<stamp>/onset_features.csv
"""

import argparse
import csv
import glob
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import librosa
import numpy as np
import scipy.signal

# --- Kick diagnosis: make the repo root importable when run as a plain script ---
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from drumscript.audio_processor.audio_loader import load_audio, normalise_audio
from drumscript.audio_processor.onset_detector import detect_onsets
from drumscript.datasets import idmt as idmt_adapter
from drumscript.drum_classifier.classify import classify_events
from drumscript.notation_generator.constants import KICK_FREQ_MAX, KICK_FREQ_MIN, KICK_LFER_MIN, SAMPLE_RATE

# --- Kick diagnosis constants ---
ONSET_WINDOW = 0.050  # 50 ms, matches benchmarks/run.py
KICK_FEATURE_KEYS = ("peak_freq", "lfer", "hfer", "hfer_5k", "centroid", "decay")
KICK_STAGES = ("ok", "misclassified", "gated", "no_onset")
KICK_HIT_FIELDS = ["track", "bucket", "ref_time", "stage", "offset_ms", "labelled_as", "failed_conditions", *KICK_FEATURE_KEYS]
KICK_SUMMARY_FIELDS = ["track", "bucket", "kd_n_ref", "n_onsets", "n_events", *KICK_STAGES]
ONSET_FIELDS = ["track", "bucket", "event_time", "labelled_as", "ref_classes", "has_kick_ref", "kick_rule_pass", *KICK_FEATURE_KEYS]
REF_CLASSES = ("KD", "SD", "HH")
# Candidate KICK_LFER_MIN values for the threshold sweep.
LFER_SWEEP = (0.12, 0.15, 0.18, 0.20, 0.22, 0.25, 0.28, 0.30, 0.32, 0.35)

# --- Grid sweep: candidate values for all three kick thresholds together ---
FREQ_MIN_GRID = (0.0, 15.0, 20.0, 30.0, 40.0)
FREQ_MAX_GRID = (120.0, 140.0, 160.0, 180.0, 200.0, 220.0, 250.0)
LFER_MIN_GRID = (0.04, 0.06, 0.08, 0.10, 0.12, 0.14, 0.16, 0.18, 0.20, 0.24, 0.28, 0.32)
PRECISION_FLOORS = (0.95, 0.90, 0.85, 0.80, 0.75)


def extract_core_specs(file_path):
    """
    Extracts core physical specifications from an audio file.

    :param file_path: Path to the audio file.
    :type file_path: str
    :return: Dictionary containing the extracted specifications, or None if loading fails.
    :rtype: dict
    """
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

    if len(y) == 0:
        return None

    # 1. Peak Frequency
    freqs, psd = scipy.signal.welch(y, sr, nperseg=2048)
    peak_idx = np.argmax(psd)
    peak_freq = float(freqs[peak_idx])

    # 2. Decay Time
    rms = librosa.feature.rms(y=y)[0]
    if len(rms) > 0:
        peak_rms_idx = np.argmax(rms)
        peak_amp = rms[peak_rms_idx]
        threshold = peak_amp * 0.1

        decay_frames = 0
        for i in range(peak_rms_idx, len(rms)):
            if rms[i] < threshold:
                break
            decay_frames += 1
        decay_time = float(librosa.frames_to_time(decay_frames, sr=sr))
    else:
        decay_time = 0.0

    # 3. Spectral Centroid
    centroid = float(np.mean(librosa.feature.spectral_centroid(y=y, sr=sr)))

    # 4. Low Frequency Energy Ratio
    low_band_limit = 150
    low_energy = np.sum(psd[freqs < low_band_limit])
    total_energy = np.sum(psd) + 1e-9
    lfer = float(low_energy / total_energy)

    # 5. High Frequency Energy Ratio (2kHz)
    high_band_limit_2k = 2000
    high_energy_2k = np.sum(psd[freqs > high_band_limit_2k])
    hfer_2k = float(high_energy_2k / total_energy)

    # 6. High Frequency Energy Ratio (5kHz)
    high_band_limit_5k = 5000
    high_energy_5k = np.sum(psd[freqs > high_band_limit_5k])
    hfer_5k = float(high_energy_5k / total_energy)

    return {
        "file": os.path.basename(file_path),
        "peak_freq": peak_freq,
        "decay_time": decay_time,
        "centroid": centroid,
        "lfer": lfer,
        "hfer_2k": hfer_2k,
        "hfer_5k": hfer_5k,
    }


# def analyze_dataset(root_path, group_by_instrument=False):
# def analyze_dataset(root_path, group_by_instrument=False, sort_metrics=False):
## sort by column in order peak, decay, centroid, lfer, hfer 2k and hfer 5k
def analyze_dataset(root_path, group_by_instrument=False, sort_metrics=False):
    """
    Scans the dataset for drum stems and analyzes their physics.

    :param root_path: Path to the dataset root folder.
    :type root_path: str
    :param group_by_instrument: Flag to sort the output by instrument type.
    :type group_by_instrument: bool
    :param sort_metrics: Flag to sort the output by sequential physics metrics.
    :type sort_metrics: bool
    """
    dataset_path = Path(root_path)
    if not dataset_path.exists():
        print(f"Directory not found: {dataset_path}")
        return

    search_pattern = str(dataset_path / "**" / "*#*.wav")
    files = glob.glob(search_pattern, recursive=True)

    target_files = [f for f in files if "#KD" in f or "#SD" in f or "#HH" in f]

    # target_files.sort()

    if group_by_instrument:

        def instrument_sort_key(filepath):
            if "#KD" in filepath:
                return 1
            elif "#SD" in filepath:
                return 2
            elif "#HH" in filepath:
                return 3
            return 4

        target_files.sort(key=lambda f: (instrument_sort_key(f), f))
    else:
        target_files.sort()

    if not target_files:
        print(f"No isolated stem files found in {dataset_path}")
        return

    print(f"Found {len(target_files)} stem files. Extracting core specifications...")
    print("-" * 120)
    print(f"{'File':<35} | {'Peak (Hz)':<10} | {'Decay (s)':<10} | {'Centroid':<10} | {'LFER %':<10} | {'HFER 2k %':<10} | {'HFER 5k %':<10}")
    print("-" * 120)

    # results = []
    # for f in target_files:
    #     res = extract_core_specs(f)
    #     if res:
    #         results.append(res)
    #         print(
    #             f"{res['file']:<35} | {res['peak_freq']:<10.1f} | {res['decay_time']:<10.3f} | "
    #             f"{res['centroid']:<10.0f} | {res['lfer'] * 100:<10.1f} | {res['hfer_2k'] * 100:<10.1f} | {res['hfer_5k'] * 100:<10.1f}"
    #         )

    results = []
    for f in target_files:
        res = extract_core_specs(f)
        if res:
            results.append(res)

    if sort_metrics:
        if group_by_instrument:

            def instrument_sort_key_res(res):
                if "#KD" in res["file"]:
                    return 1
                elif "#SD" in res["file"]:
                    return 2
                elif "#HH" in res["file"]:
                    return 3
                return 4

            results.sort(
                key=lambda x: (instrument_sort_key_res(x), x["peak_freq"], x["decay_time"], x["centroid"], x["lfer"], x["hfer_2k"], x["hfer_5k"])
            )
        else:
            results.sort(key=lambda x: (x["peak_freq"], x["decay_time"], x["centroid"], x["lfer"], x["hfer_2k"], x["hfer_5k"]))

    for res in results:
        print(
            f"{res['file']:<35} | {res['peak_freq']:<10.1f} | {res['decay_time']:<10.3f} | "
            f"{res['centroid']:<10.0f} | {res['lfer'] * 100:<10.1f} | {res['hfer_2k'] * 100:<10.1f} | {res['hfer_5k'] * 100:<10.1f}"
        )


# ==============================================================================
# KICK DIAGNOSIS
# Runs the live pipeline (same as benchmarks/run.py) on the #MIX files and
# reports where each reference kick was lost.
# ==============================================================================


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


def failed_kick_conditions(features):
    """
    Lists which conditions of the live kick rule (classify_events RULE 1) failed.

    :param features: The debug_features dict returned by classify_events.
    :type features: dict
    :return: List of failed condition names.
    :rtype: list[str]
    """
    failed = []
    if features.get("lfer", 0.0) < KICK_LFER_MIN:
        failed.append("lfer_low")
    if features.get("peak_freq", 0.0) < KICK_FREQ_MIN:
        failed.append("peak_freq_low")
    if features.get("peak_freq", 0.0) > KICK_FREQ_MAX:
        failed.append("peak_freq_high")
    return failed


def kick_rule_passes(features, lfer_min=KICK_LFER_MIN):
    """
    Evaluates the live kick rule against a candidate LFER threshold.

    :param features: The debug_features dict returned by classify_events.
    :type features: dict
    :param lfer_min: Candidate value for KICK_LFER_MIN.
    :type lfer_min: float
    :return: True if the kick rule would fire.
    :rtype: bool
    """
    peak_freq = features.get("peak_freq", 0.0)
    return features.get("lfer", 0.0) >= lfer_min and KICK_FREQ_MIN <= peak_freq <= KICK_FREQ_MAX


def reference_classes_near(references, event_time):
    """
    Lists which reference instrument classes sit within the tolerance window.

    :param references: Mapping of class name to list of onset times.
    :type references: dict
    :param event_time: Detected event time in seconds.
    :type event_time: float
    :return: List of matching class names, e.g. ['KD', 'HH'].
    :rtype: list[str]
    """
    matched = []
    for cls in REF_CLASSES:
        _, dist = nearest_time(references.get(cls, []), event_time)
        if dist <= ONSET_WINDOW:
            matched.append(cls)
    return matched


def diagnose_kick_track(item):
    """
    Classifies every reference kick in one track by the pipeline stage that lost it,
    and captures the features of every detected onset.

    :param item: A BenchmarkItem from the IDMT adapter.
    :type item: drumscript.datasets.base.BenchmarkItem
    :return: Tuple of (per-kick rows, per-track summary dict, per-onset rows).
    :rtype: tuple
    """
    audio, sr = load_audio(str(item.audio_path), sr=SAMPLE_RATE)
    audio = normalise_audio(audio)
    onsets = detect_onsets(audio, sr)
    events = classify_events(audio, sr, onsets)
    event_times = [e["time_sec"] for e in events]

    rows = []
    for ref_time in item.references.get("KD", []):
        row = {"track": item.track_id, "bucket": item.bucket, "ref_time": round(float(ref_time), 4)}

        _, onset_dist = nearest_time(onsets, ref_time)
        ev_idx, ev_dist = nearest_time(event_times, ref_time)

        if onset_dist > ONSET_WINDOW:
            row["stage"] = "no_onset"
        elif ev_dist > ONSET_WINDOW:
            row["stage"] = "gated"
        else:
            event = events[ev_idx]
            feats = event.get("debug_features", {})
            row["offset_ms"] = round((event["time_sec"] - ref_time) * 1000, 1)
            row["labelled_as"] = "+".join(event["instruments"])
            for key in KICK_FEATURE_KEYS:
                if key in feats:
                    row[key] = round(float(feats[key]), 4)
            if "kick" in event["instruments"]:
                row["stage"] = "ok"
            else:
                row["stage"] = "misclassified"
                row["failed_conditions"] = "+".join(failed_kick_conditions(feats)) or "none"
        rows.append(row)

    # --- Every detected onset, kick-bearing or not ---
    onset_rows = []
    for event in events:
        feats = event.get("debug_features", {})
        ref_classes = reference_classes_near(item.references, event["time_sec"])
        onset_row = {
            "track": item.track_id,
            "bucket": item.bucket,
            "event_time": round(float(event["time_sec"]), 4),
            "labelled_as": "+".join(event["instruments"]),
            "ref_classes": "+".join(ref_classes) or "none",
            "has_kick_ref": "KD" in ref_classes,
            "kick_rule_pass": kick_rule_passes(feats),
        }
        for key in KICK_FEATURE_KEYS:
            if key in feats:
                onset_row[key] = round(float(feats[key]), 4)
        onset_rows.append(onset_row)

    counts = Counter(r["stage"] for r in rows)
    summary = {
        "track": item.track_id,
        "bucket": item.bucket,
        "kd_n_ref": len(rows),
        "n_onsets": len(onsets),
        "n_events": len(events),
        **{stage: counts.get(stage, 0) for stage in KICK_STAGES},
    }
    return rows, summary, onset_rows


def describe_lfer(label, values):
    """
    Prints a one-line distribution summary for a set of LFER values.

    :param label: Group name to print.
    :type label: str
    :param values: LFER values.
    :type values: list[float]
    """
    if not values:
        print(f"  {label:<22}n=0")
        return
    # arr = np.asarray(values, dtype=float)
    # print(f"  {label:<22}n={len(arr):<5}min={arr.min():.3f}  p25={np.percentile(arr, 25):.3f}  median={np.median(arr):.3f}  p75={np.percentile(arr,
    #    75):.3f}  max={arr.max():.3f}")
    arr = np.asarray(values, dtype=float)
    lo = f"min={arr.min():.3f}  p25={np.percentile(arr, 25):.3f}"
    mid = f"median={np.median(arr):.3f}"
    hi = f"p75={np.percentile(arr, 75):.3f}  max={arr.max():.3f}"
    print(f"  {label:<24}n={len(arr):<5} {lo}  {mid}  {hi}")


def print_threshold_sweep(onset_rows):
    """
    Sweeps candidate KICK_LFER_MIN values and reports recall against false positives.

    Only onsets whose peak_freq already sits inside the kick band are counted,
    since those are the ones the LFER threshold actually decides.

    :param onset_rows: Per-onset rows from diagnose_kick_track.
    :type onset_rows: list[dict]
    """
    in_band = [r for r in onset_rows if KICK_FREQ_MIN <= r.get("peak_freq", 0.0) <= KICK_FREQ_MAX]
    kick_rows = [r for r in in_band if r["has_kick_ref"]]
    other_rows = [r for r in in_band if not r["has_kick_ref"]]

    print("\n-- LFER distribution (onsets with peak_freq inside the kick band) --")
    describe_lfer("with a kick ref", [r.get("lfer", 0.0) for r in kick_rows])
    describe_lfer("without a kick ref", [r.get("lfer", 0.0) for r in other_rows])

    if not other_rows:
        print("\n  [WARNING] No in-band onsets without a kick reference in this sample.")
        print("  [WARNING] The false kick column below is structurally zero, not a good result.")

    print("\n-- KICK_LFER_MIN sweep --")
    print(f"  {'threshold':<12}{'kicks caught':>14}{'recall':>9}{'false kicks':>14}")
    for threshold in LFER_SWEEP:
        caught = sum(1 for r in kick_rows if r.get("lfer", 0.0) >= threshold)
        false_pos = sum(1 for r in other_rows if r.get("lfer", 0.0) >= threshold)
        recall = caught / len(kick_rows) if kick_rows else 0.0
        marker = "  <- current" if abs(threshold - KICK_LFER_MIN) < 1e-9 else ""
        print(f"  {threshold:<12.2f}{caught:>7}/{len(kick_rows):<6}{recall:>8.2f}{false_pos:>14}{marker}")


def score_candidate_rule(onset_rows, freq_min, freq_max, lfer_min):
    """
    Scores one candidate kick rule against the reference kicks.

    The candidate fires when ``freq_min <= peak_freq <= freq_max`` and
    ``lfer >= lfer_min``. Precision, recall and F-measure are computed across
    every onset supplied, where a positive case is an onset with a kick reference.

    :param onset_rows: Per-onset rows from diagnose_kick_track.
    :type onset_rows: list[dict]
    :param freq_min: Candidate KICK_FREQ_MIN.
    :type freq_min: float
    :param freq_max: Candidate KICK_FREQ_MAX.
    :type freq_max: float
    :param lfer_min: Candidate KICK_LFER_MIN.
    :type lfer_min: float
    :return: Dictionary of thresholds, counts and precision/recall/F.
    :rtype: dict
    """
    true_pos = 0
    false_pos = 0
    total_kicks = 0

    for row in onset_rows:
        is_kick = bool(row.get("has_kick_ref"))
        if is_kick:
            total_kicks += 1
        peak_freq = row.get("peak_freq", 0.0)
        fires = freq_min <= peak_freq <= freq_max and row.get("lfer", 0.0) >= lfer_min
        if fires and is_kick:
            true_pos += 1
        elif fires:
            false_pos += 1

    precision = true_pos / (true_pos + false_pos) if (true_pos + false_pos) else 0.0
    recall = true_pos / total_kicks if total_kicks else 0.0
    f_measure = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0

    return {
        "freq_min": freq_min,
        "freq_max": freq_max,
        "lfer_min": lfer_min,
        "tp": true_pos,
        "fp": false_pos,
        "precision": precision,
        "recall": recall,
        "f": f_measure,
    }


def print_grid_header():
    """Prints the column header used by the grid sweep tables."""
    print(f"  {'freq (Hz)':<12}{'lfer':<8}{'TP':<8}{'FP':<8}{'prec':<8}{'recall':<9}{'F':<8}")
    print("  " + "-" * 60)


def print_grid_row(result, marker=""):
    """
    Prints one scored candidate rule as a fixed-width line.

    :param result: A result dict from score_candidate_rule.
    :type result: dict
    :param marker: Optional trailing note.
    :type marker: str
    """
    freqs = f"{result['freq_min']:.0f}-{result['freq_max']:.0f}"
    counts = f"{result['tp']:<8}{result['fp']:<8}"
    scores = f"{result['precision']:<8.3f}{result['recall']:<9.3f}{result['f']:<8.3f}"
    print(f"  {freqs:<12}{result['lfer_min']:<8.2f}{counts}{scores}{marker}")


def print_grid_sweep(onset_rows, top=20):
    """
    Grid sweeps KICK_FREQ_MIN, KICK_FREQ_MAX and KICK_LFER_MIN together.

    The LFER sweep alone assumes the current frequency band is correct. This
    varies all three thresholds, so a change can be chosen on F-measure rather
    than on recall in isolation.

    :param onset_rows: Per-onset rows from diagnose_kick_track.
    :type onset_rows: list[dict]
    :param top: How many ranked combinations to print.
    :type top: int
    """
    if not onset_rows:
        print("\n-- Grid sweep: no onsets to score --")
        return

    if not any(not row.get("has_kick_ref") for row in onset_rows):
        print("\n  [WARNING] Every onset in this sample has a kick reference.")
        print("  [WARNING] No false positive is possible, so precision and F are meaningless here.")
        print("  [WARNING] Re-run across more tracks before trusting these numbers.")

    n_kick = sum(1 for row in onset_rows if row.get("has_kick_ref"))
    print(f"\n-- Scoring pool --\n  onsets={len(onset_rows)}  with a kick ref={n_kick}  without={len(onset_rows) - n_kick}")

    print("\n-- Current live rule --")
    print_grid_header()
    print_grid_row(score_candidate_rule(onset_rows, KICK_FREQ_MIN, KICK_FREQ_MAX, KICK_LFER_MIN))

    results = []
    for freq_min in FREQ_MIN_GRID:
        for freq_max in FREQ_MAX_GRID:
            for lfer_min in LFER_MIN_GRID:
                results.append(score_candidate_rule(onset_rows, freq_min, freq_max, lfer_min))

    results.sort(key=lambda r: r["f"], reverse=True)

    print(f"\n-- Top {top} candidate rules by F-measure --")
    print_grid_header()
    for result in results[:top]:
        print_grid_row(result)

    if results and results[0]["fp"] == 0:
        print("\n  [WARNING] The best candidate produces zero false positives.")
        print("  [WARNING] That usually means this sample holds no confusable non-kick onsets,")
        print("  [WARNING] not that the rule is perfect. Re-run across the full dataset.")

    print("\n-- Best candidate at each precision floor --")
    print_grid_header()
    for floor in PRECISION_FLOORS:
        eligible = [r for r in results if r["precision"] >= floor]
        if eligible:
            print_grid_row(eligible[0], marker=f"   prec >= {floor:.2f}")
        else:
            print(f"  (nothing reaches precision {floor:.2f})")


def load_onset_rows(csv_path):
    """
    Reloads onset rows from a previously written onset_features.csv.

    Lets the grid sweep be re-run on an existing diagnostics folder without
    re-processing any audio.

    :param csv_path: Path to onset_features.csv.
    :type csv_path: str
    :return: Per-onset rows in the same shape diagnose_kick_track produces.
    :rtype: list[dict]
    """
    rows = []
    with open(csv_path, newline="") as fh:
        for record in csv.DictReader(fh):
            row = dict(record)
            row["has_kick_ref"] = str(record.get("has_kick_ref", "")).strip().lower() == "true"
            for key in KICK_FEATURE_KEYS:
                try:
                    row[key] = float(record[key])
                except (KeyError, TypeError, ValueError):
                    row.pop(key, None)
            rows.append(row)
    return rows


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


def diagnose_kicks(root_path, subset=None, tracks=None, output_dir=None, top=20):
    """
    Runs the kick diagnosis over the selected IDMT #MIX tracks.

    :param root_path: Path to the dataset root folder.
    :type root_path: str
    :param subset: Optional subset filter (RealDrum, WaveDrum, TechnoDrum).
    :type subset: str
    :param tracks: Optional list of substrings; only matching tracks are run.
    :type tracks: list[str]
    :param output_dir: Optional output directory for the CSVs.
    :type output_dir: str
    :param top: How many ranked grid-sweep combinations to print.
    :type top: int
    """
    items = list(idmt_adapter.iter_items(argparse.Namespace(root=root_path, subset=subset)))
    if tracks:
        items = [i for i in items if any(t in i.track_id for t in tracks)]
    if not items:
        print("No matching #MIX tracks found.")
        return

    print(f"\nKick rule : lfer >= {KICK_LFER_MIN} and {KICK_FREQ_MIN} <= peak_freq <= {KICK_FREQ_MAX}")
    print(f"Window    : {int(ONSET_WINDOW * 1000)} ms")
    print(f"Tracks    : {len(items)}\n")
    print(f"{'track':<28}{'ref':>5}{'ok':>5}{'miscl':>7}{'gated':>7}{'no_on':>7}")
    print("-" * 59)

    all_hits = []
    all_onsets = []
    summaries = []
    for item in items:
        try:
            hits, summary, onset_rows = diagnose_kick_track(item)
        except Exception as e:
            print(f"{item.track_id:<28}  [ERROR] {e}")
            continue
        all_hits.extend(hits)
        all_onsets.extend(onset_rows)
        summaries.append(summary)
        s = summary
        print(f"{s['track']:<28}{s['kd_n_ref']:>5}{s['ok']:>5}{s['misclassified']:>7}{s['gated']:>7}{s['no_onset']:>7}")

    stage_totals = Counter(h["stage"] for h in all_hits)
    failed_totals = Counter(h["failed_conditions"] for h in all_hits if h["stage"] == "misclassified")
    label_totals = Counter(h["labelled_as"] for h in all_hits if h["stage"] == "misclassified")

    print("\n-- Where kicks were lost --")
    for stage in KICK_STAGES:
        print(f"  {stage:<15}{stage_totals.get(stage, 0)}")
    print("\n-- Misclassified: which kick condition failed --")
    for cond, n in failed_totals.most_common():
        print(f"  {cond:<30}{n}")
    print("\n-- Misclassified: labelled as instead --")
    for label, n in label_totals.most_common(10):
        print(f"  {label:<30}{n}")

    print_threshold_sweep(all_onsets)
    print_grid_sweep(all_onsets, top=top)

    out_dir = Path(output_dir) if output_dir else Path("outputs") / "benchmarks" / "idmt" / "diagnostics" / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    write_dict_csv(out_dir / "kick_hits.csv", KICK_HIT_FIELDS, all_hits)
    write_dict_csv(out_dir / "kick_summary.csv", KICK_SUMMARY_FIELDS, summaries)
    write_dict_csv(out_dir / "onset_features.csv", ONSET_FIELDS, all_onsets)
    print(f"\nWritten: {out_dir}/kick_hits.csv, kick_summary.csv and onset_features.csv\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frequencies and core specs from IDMT dataset.")
    # parser.add_argument("dataset_root", type=str, help="Path to the IDMT dataset root folder")
    # Optional so --sweep-csv can be run on an existing CSV without a dataset path.
    parser.add_argument("dataset_root", type=str, nargs="?", default=None, help="Path to the IDMT dataset root folder")
    # parser.add_argument("--group-by-instrument", action="store_true", help="Group the printed results by instrument type")

    # parser.add_argument("--group", action="store_true", help="Group the printed results by instrument type")  # assumed default will be unsorted
    # args = parser.parse_args()
    # analyze_dataset(args.dataset_root)
    # analyze_dataset(args.dataset_root, args.group_by_instrument)
    # analyze_dataset(args.dataset_root, args.group)  # group by instrument

    parser.add_argument("--group", action="store_true", help="Group the printed results by instrument type")
    # sort by column in order peak, decay, centroid, lfer, hfer 2k and hfer 5k
    parser.add_argument("--sort", action="store_true", help="Sort the printed results by extracted metrics")

    # --- Kick diagnosis flags ---
    parser.add_argument(
        "--diagnose-kick", action="store_true", help="Run the live pipeline on #MIX files and report where each reference kick was lost"
    )
    parser.add_argument("--subset", default=None, help="Kick diagnosis only: RealDrum, WaveDrum or TechnoDrum")
    parser.add_argument("--tracks", nargs="*", default=None, help="Kick diagnosis only: run tracks whose name contains any of these")
    parser.add_argument("--output", default=None, help="Kick diagnosis only: output directory for the CSVs")
    parser.add_argument("--top", type=int, default=20, help="Kick diagnosis only: how many grid-sweep combinations to print")
    parser.add_argument("--sweep-csv", default=None, help="Grid sweep an existing onset_features.csv, without re-processing audio")

    args = parser.parse_args()

    # analyze_dataset(args.dataset_root, group_by_instrument=args.group, sort_metrics=args.sort)
    # if args.diagnose_kick:
    #     diagnose_kicks(args.dataset_root, subset=args.subset, tracks=args.tracks, output_dir=args.output)
    if args.sweep_csv:
        print_grid_sweep(load_onset_rows(args.sweep_csv), top=args.top)
        print()
    elif not args.dataset_root:
        parser.error("dataset_root is required unless --sweep-csv is used")
    elif args.diagnose_kick:
        diagnose_kicks(args.dataset_root, subset=args.subset, tracks=args.tracks, output_dir=args.output, top=args.top)
    else:
        analyze_dataset(args.dataset_root, group_by_instrument=args.group, sort_metrics=args.sort)
