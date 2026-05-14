import glob
import os
from datetime import datetime
from pathlib import Path

import librosa
import numpy as np
import scipy.signal

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f"\ndate/time: {datetimestamp}")


def analyze_snare_physics(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

    # 1. Peak Frequency (The "Body" or "Donk" of the snare)
    # Snare fundamentals are usually 150-250Hz, distinct from Kicks (40-100Hz)
    freqs, psd = scipy.signal.welch(y, sr, nperseg=2048)
    peak_idx = np.argmax(psd)
    peak_freq = freqs[peak_idx]

    # 2. High Frequency Energy Ratio (HFER) (The "Wires" or "Crispness")
    # Energy > 2000Hz vs Total Energy.
    # Kicks usually have very little here; Snares have a lot.
    high_band_limit = 2000
    high_energy = np.sum(psd[freqs > high_band_limit])
    total_energy = np.sum(psd)
    hfer = high_energy / (total_energy + 1e-9)

    # 3. Spectral Flatness (Noise-likeness)
    # A sine wave has flatness near 0. White noise has flatness near 1.
    # Snare wires are closer to white noise.
    flatness = librosa.feature.spectral_flatness(y=y)
    mean_flatness = np.mean(flatness)

    # 4. Spectral Centroid
    # Included for comparison with the Gillet model
    centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

    return {"file": os.path.basename(file_path), "peak_freq": peak_freq, "hfer": hfer, "mean_flatness": mean_flatness, "centroid": centroid}


def main():
    # Robust path finding
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    # Match your folder structure
    audio_path = project_root / "test_audio" / "snare_*.wav"

    print(f"Looking for audio in: {audio_path}")
    files = glob.glob(str(audio_path))
    files.sort()

    if not files:
        print("No files found! Check that your folder is named 'test_audio' and contains snare_*.wav files.")
        return

    print(f"Found {len(files)} files. Analyzing Snare Physics...")
    print("-" * 115)
    print(f"{'File':<15} | {'Peak Freq (Hz)':<15} | {'High Energy %':<15} | {'Flatness':<15} | {'Centroid (Hz)':<15}")
    print("-" * 115)

    results = []
    for f in files:
        res = analyze_snare_physics(f)
        if res:
            results.append(res)
            print(f"{res['file']:<15} | {res['peak_freq']:.2f}| {res['hfer'] * 100:.1f}%| {res['mean_flatness']:.4f} | {res['centroid']:.0f}")

    if results:
        avg_peak = np.mean([r["peak_freq"] for r in results])
        avg_hfer = np.mean([r["hfer"] for r in results])
        avg_flat = np.mean([r["mean_flatness"] for r in results])
        avg_cent = np.mean([r["centroid"] for r in results])

        print("-" * 115)
        print(f"AVERAGES        | {avg_peak:.2f}           | {avg_hfer * 100:.1f}%           | {avg_flat:.4f}          | {avg_cent:.0f}")
        print("-" * 115)


if __name__ == "__main__":
    main()
