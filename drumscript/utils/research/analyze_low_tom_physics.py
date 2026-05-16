# drumscript/utils/research/analyze_low_tom_physics.py

# To determine the Frequency Floor (separating them from Kicks) and the Membranophone Signature
# (separating them from Cymbals) we need to analyse their physics.

# Phase 1: The Analysis Script (Low Tom)
# This script will extract the critical metrics:
# Peak Frequency: Where does the fundamental note sit? (Likely 60-100Hz).
# Decay Time: How long does it ring? (Toms usually sustain longer than Kicks).
# Spectral Flatness: Is it a tone (low flatness) or noise (high flatness)?
# High Frequency Energy: Verifying it lacks the "shimmer" of a cymbal.

import glob
import os
from pathlib import Path

import librosa
import numpy as np
import scipy.signal


def analyze_low_tom_physics(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

    # 1. Peak Frequency (The "Note")
    # We use a large window (nperseg=4096) for high bass resolution
    freqs, psd = scipy.signal.welch(y, sr, nperseg=4096)
    peak_idx = np.argmax(psd)
    peak_freq = freqs[peak_idx]

    # 2. Decay Time (Resonance)
    # Toms are the most resonant drums. We measure time to drop -20dB (10% amplitude).
    rms = librosa.feature.rms(y=y)[0]
    peak_rms_idx = np.argmax(rms)
    peak_amp = rms[peak_rms_idx]
    threshold = peak_amp * 0.1

    decay_frames = 0
    for i in range(peak_rms_idx, len(rms)):
        if rms[i] < threshold:
            break
        decay_frames += 1
    decay_time = librosa.frames_to_time(decay_frames, sr=sr)

    # 3. Spectral Flatness (Tone vs Noise)
    # Membranophones (Skins) have distinct harmonic peaks -> Low Flatness
    # Idiophones (Metals) have chaotic spectra -> High Flatness
    flatness = np.mean(librosa.feature.spectral_flatness(y=y))

    # 4. High Frequency Energy Ratio (HFER)
    # Energy > 5000Hz (Cymbal/Hi-Hat Territory)
    high_band_limit = 5000
    high_energy = np.sum(psd[freqs > high_band_limit])
    total_energy = np.sum(psd) + 1e-9
    hfer = high_energy / total_energy

    return {"file": os.path.basename(file_path), "peak_freq": peak_freq, "decay_time": decay_time, "flatness": flatness, "hfer": hfer}


def main():
    # --------------------------------------------------------------------------uncomment during testing
    # from datetime import datetime
    # print("\n# ------------------------------------------------------------------------------------")
    # datetimestamp = datetime.now()
    # print(f'\ndate/time: {datetimestamp}')
    # --------------------------------------------------------------------------------------------------
    # Setup path
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    audio_path = project_root / "test_audio" / "low_tom_*.wav"

    print(f"Looking for audio in: {audio_path}")
    files = glob.glob(str(audio_path))
    files.sort()

    if not files:
        print("No files found! Ensure files are in 'test_audio' and named 'low_tom_*.wav'")
        return

    print(f"Found {len(files)} files. Analyzing Low Tom Physics...")
    print("-" * 115)
    print(f"{'File':<25} | {'Note (Hz)':<10} | {'Decay (s)':<10} | {'Flatness':<10} | {'Treble >5k %':<12}")
    print("-" * 115)

    results = []
    for f in files:
        res = analyze_low_tom_physics(f)
        if res:
            results.append(res)
            print(f"{res['file']:<25} | {res['peak_freq']:.1f}| {res['decay_time']:.3f}| {res['flatness']:.5f}| {res['hfer'] * 100:.2f}%")

    # Calculate averages
    if results:
        avg_decay = np.mean([r["decay_time"] for r in results])
        avg_flat = np.mean([r["flatness"] for r in results])

        print("-" * 115)
        print(f"AVERAGES | -- | {avg_decay:.3f}  | {avg_flat:.5f}| --")
        print("-" * 115)


if __name__ == "__main__":
    # --------------------------------------------------------------------------uncomment during testing
    # from datetime import datetime
    # print("\n# ------------------------------------------------------------------------------------")
    # datetimestamp = datetime.now()
    # print(f'\ndate/time: {datetimestamp}')
    # --------------------------------------------------------------------------------------------------
    main()
