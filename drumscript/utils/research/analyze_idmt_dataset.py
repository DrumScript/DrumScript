# drumscript/utils/research/analyze_idmt_dataset.py

"""
Utility script to extract frequency metrics and core physical specifications
from the IDMT-SMT-DRUMS-V2 dataset.

Targeted extraction: The script filters for the isolated drum stems (#KD, #SD, #HH)
to measure the precise physics of each instrument without background noise.

Aligned metrics: It calculates peak frequency, decay time, spectral centroid,
and energy ratios to mirror the logic used in the classification engine.

Standardised imports: All import statements are separated onto individual lines.

Sphinx documentation: Standard reST docstrings are applied to all functions.

Usage:
uv run python drumscript/utils/research/analyze_idmt_dataset.py benchmarks/datasets/IDMT
uv run --extra dev python drumscript/utils/research/analyze_idmt_dataset.py benchmarks/datasets/IDMT --group-by-instrument

"""

import argparse
import glob
import os
from pathlib import Path

import librosa
import numpy as np
import scipy.signal


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


# def analyze_dataset(root_path):
def analyze_dataset(root_path, group_by_instrument=False):
    """
    Scans the dataset for drum stems and analyzes their physics.

    :param root_path: Path to the dataset root folder.
    :type root_path: str
    :param group_by_instrument: Flag to sort the output by instrument type.
    :type group_by_instrument: bool
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

    results = []
    for f in target_files:
        res = extract_core_specs(f)
        if res:
            results.append(res)
            print(
                f"{res['file']:<35} | {res['peak_freq']:<10.1f} | {res['decay_time']:<10.3f} | "
                f"{res['centroid']:<10.0f} | {res['lfer'] * 100:<10.1f} | {res['hfer_2k'] * 100:<10.1f} | {res['hfer_5k'] * 100:<10.1f}"
            )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Extract frequencies and core specs from IDMT dataset.")
    parser.add_argument("dataset_root", type=str, help="Path to the IDMT dataset root folder")
    parser.add_argument("--group-by-instrument", action="store_true", help="Group the printed results by instrument type")
    args = parser.parse_args()

    # analyze_dataset(args.dataset_root)
    analyze_dataset(args.dataset_root, args.group_by_instrument)
