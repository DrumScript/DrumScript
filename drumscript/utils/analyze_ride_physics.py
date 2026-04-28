import glob
import os
from datetime import datetime
from pathlib import Path

import librosa
import numpy as np

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f"\ndate/time: {datetimestamp}")


def analyze_ride_physics(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

    # 1. Decay Time (The Long Tail)
    # Cymbals ring much longer than drums. We measure time to drop -20dB.
    rms = librosa.feature.rms(y=y)[0]
    peak_idx = np.argmax(rms)
    peak_amp = rms[peak_idx]
    threshold = peak_amp * 0.1  # -20dB

    decay_frames = 0
    for i in range(peak_idx, len(rms)):
        if rms[i] < threshold:
            break
        decay_frames += 1
    decay_time = librosa.frames_to_time(decay_frames, sr=sr)

    # 2. Spectral Centroid (Brightness)
    # Rides often have a 'gong' or 'body' frequency lower than a thin crash.
    centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))

    # 3. Bandwidth (Spread)
    # How wide is the frequency range?
    bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=sr))

    # 4. Spectral Flatness (Noise vs Tone)
    # A ride edge hit is noisy, but might retain some 'bell' tone compared to a crash.
    flatness = np.mean(librosa.feature.spectral_flatness(y=y))

    return {"file": os.path.basename(file_path), "decay_time": decay_time, "centroid": centroid, "bandwidth": bandwidth, "flatness": flatness}


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    audio_path = project_root / "test_audio" / "ride_*.wav"

    print(f"Looking for audio in: {audio_path}")
    files = glob.glob(str(audio_path))
    files.sort()

    if not files:
        print("No files found! Ensure files are in 'test_audio' and named 'ride_*.wav'")
        return

    print(f"Found {len(files)} files. Analyzing Ride Cymbal Physics...")
    print("-" * 130)
    print(f"{'File':<40} | {'Decay (s)':<10} | {'Centroid (Hz)':<15} | {'Flatness':<10} | {'Bandwidth':<10}")
    print("-" * 130)

    results = []
    for f in files:
        res = analyze_ride_physics(f)
        if res:
            results.append(res)
            print(
                f"{res['file']:<40} | {res['decay_time']:.3f}      | {res['centroid']:.0f}            | {res['flatness']:.4f}     | {res['bandwidth']:.0f}"
            )

    if results:
        avg_decay = np.mean([r["decay_time"] for r in results])
        avg_cent = np.mean([r["centroid"] for r in results])

        print("-" * 130)
        print(f"AVERAGES                                 | {avg_decay:.3f}      | {avg_cent:.0f}            | --         | --")
        print("-" * 130)


if __name__ == "__main__":
    main()
