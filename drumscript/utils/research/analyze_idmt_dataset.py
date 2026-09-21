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
and the features the classifier actually saw.

Standardised imports: All import statements are separated onto individual lines.

Sphinx documentation: Standard reST docstrings are applied to all functions.

Usage:
uv run python drumscript/utils/research/analyze_idmt_dataset.py benchmarks/datasets/IDMT

## FLAGS

Example usage:
uv run --extra dev python drumscript/utils/research/analyze_idmt_dataset.py benchmarks/datasets/IDMT --group --sort

-- group
--sort
--diagnose-kick
--diagnose-kick --tracks WaveDrum02_37 WaveDrum02_39 # specify specific IDMT tracks to use
# `WaveDrum02_37 WaveDrum02_39` are examples
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


def diagnose_kick_track(item):
    """
    Classifies every reference kick in one track by the pipeline stage that lost it.

    :param item: A BenchmarkItem from the IDMT adapter.
    :type item: drumscript.datasets.base.BenchmarkItem
    :return: Tuple of (per-kick rows, per-track summary dict).
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

    counts = Counter(r["stage"] for r in rows)
    summary = {
        "track": item.track_id,
        "bucket": item.bucket,
        "kd_n_ref": len(rows),
        "n_onsets": len(onsets),
        "n_events": len(events),
        **{stage: counts.get(stage, 0) for stage in KICK_STAGES},
    }
    return rows, summary


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


def diagnose_kicks(root_path, subset=None, tracks=None, output_dir=None):
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
    summaries = []
    for item in items:
        try:
            hits, summary = diagnose_kick_track(item)
        except Exception as e:
            print(f"{item.track_id:<28}  [ERROR] {e}")
            continue
        all_hits.extend(hits)
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

    out_dir = Path(output_dir) if output_dir else Path("outputs") / "benchmarks" / "idmt" / "diagnostics" / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out_dir.mkdir(parents=True, exist_ok=True)
    write_dict_csv(out_dir / "kick_hits.csv", KICK_HIT_FIELDS, all_hits)
    write_dict_csv(out_dir / "kick_summary.csv", KICK_SUMMARY_FIELDS, summaries)
    # print(f"\nWritten: {out_dir}/kick_hits.csv and kick_summary.csv\n")
    print(f"\nWritten: {out_dir}/kick_hits.csv and {out_dir}/kkick_summary.csv\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frequencies and core specs from IDMT dataset.")
    parser.add_argument("dataset_root", type=str, help="Path to the IDMT dataset root folder")
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

    args = parser.parse_args()

    # analyze_dataset(args.dataset_root, group_by_instrument=args.group, sort_metrics=args.sort)
    if args.diagnose_kick:
        diagnose_kicks(args.dataset_root, subset=args.subset, tracks=args.tracks, output_dir=args.output)
    else:
        analyze_dataset(args.dataset_root, group_by_instrument=args.group, sort_metrics=args.sort)
