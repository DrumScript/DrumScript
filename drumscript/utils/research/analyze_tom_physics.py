# drumscript/utils/research/analyze_tom_physics.py

import glob
import os
from pathlib import Path

import librosa
import numpy as np
import scipy.signal


def analyze_tom_physics(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

    # 1. Peak Frequency (The "Note")
    # This is the primary way we will separate Low, Mid, and High Toms
    freqs, psd = scipy.signal.welch(y, sr, nperseg=4096)  # Higher res for finding the exact note
    peak_idx = np.argmax(psd)
    peak_freq = freqs[peak_idx]

    # 2. High Frequency Energy Ratio (HFER)
    # Toms have NO wires. They should have very low energy > 2000Hz.
    # If this is high, it's likely a Snare or Cymbal.
    high_energy = np.sum(psd[freqs > 2000])
    total_energy = np.sum(psd) + 1e-9
    hfer = high_energy / total_energy

    # 3. Spectral Flatness (Tonality)
    # Toms are "musical" (low flatness). Snares/Cymbals are "noisy" (high flatness).
    flatness = np.mean(librosa.feature.spectral_flatness(y=y))

    # 4. Decay (Resonance)
    # Toms usually ring out longer than a dampened Kick or Snare.
    rms = librosa.feature.rms(y=y)[0]
    peak_amp = np.max(rms)
    threshold = peak_amp * 0.05  # -26dB (Toms ring longer, so we check lower tail)

    decay_frames = 0
    peak_frame = np.argmax(rms)
    for i in range(peak_frame, len(rms)):
        if rms[i] < threshold:
            break
        decay_frames += 1
    decay_time = librosa.frames_to_time(decay_frames, sr=sr)

    return {"file": os.path.basename(file_path), "peak_freq": peak_freq, "hfer": hfer, "flatness": flatness, "decay_time": decay_time}


def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    # We will look for anything with "tom" in the name
    audio_path = project_root / "test_audio" / "*tom*.wav"

    print(f"Looking for audio in: {audio_path}")
    files = glob.glob(str(audio_path))
    files.sort()

    if not files:
        print("No files found! Please upload files named like 'tom_low_01.wav', 'tom_mid_01.wav', etc.")
        return

    print(f"Found {len(files)} files. Analyzing Tom Physics...")
    print("-" * 110)
    print(f"{'File':<25} | {'Note (Hz)':<10} | {'Treble %':<10} | {'Flatness':<10} | {'Decay (s)':<10}")
    print("-" * 110)

    results = []
    for f in files:
        res = analyze_tom_physics(f)
        if res:
            results.append(res)
            print(f"{res['file']:<25} | {res['peak_freq']:.1f}| {res['hfer'] * 100:.1f}% | {res['flatness']:.4f}     | {res['decay_time']:.3f}")

    print("-" * 110)


if __name__ == "__main__":
    # --------------------------------------------------------------------------uncomment during testing
    # from datetime import datetime
    # print("\n# ------------------------------------------------------------------------------------")
    # datetimestamp = datetime.now()
    # print(f'\ndate/time: {datetimestamp}')
    # --------------------------------------------------------------------------------------------------
    main()
