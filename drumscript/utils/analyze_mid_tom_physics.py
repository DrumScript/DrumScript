"""I have received the 5 Mid Tom audio files (mid_tom_phat.wav to mid_tom_yamaha_maple.wav).

Now we will determine exactly where the "Mid Tom" sits in the frequency spectrum. This is critical because, as we saw with the Low Toms, the boundaries between "Low", "Mid", and "High" can be subjective. We will use your data to make them objective.

Phase 1: The Analysis Script (Mid Tom)
This script is tuned to look at the 100Hz - 200Hz range where Mid Toms typically live. It will also double-check the "Membranophone Signature" (Decay & Purity) to ensure they match the Low Toms.

Action: Save this as drumscript/utils/analyze_mid_tom_physics.py."""

import glob
import os
from datetime import datetime
from pathlib import Path

import librosa
import numpy as np
import scipy.signal

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f'\ndate/time: {datetimestamp}')


def analyze_mid_tom_physics(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None

    # 1. Peak Frequency (The "Note")
    # Using 4096 ensures we can distinguish 118Hz from 125Hz accurately
    freqs, psd = scipy.signal.welch(y, sr, nperseg=4096)
    peak_idx = np.argmax(psd)
    peak_freq = freqs[peak_idx]

    # 2. Decay Time (Resonance)
    # Mid Toms should sing, but maybe slightly less than big floor toms.
    rms = librosa.feature.rms(y=y)[0]
    peak_rms_idx = np.argmax(rms)
    peak_amp = rms[peak_rms_idx]
    threshold = peak_amp * 0.1 # -20dB

    decay_frames = 0
    for i in range(peak_rms_idx, len(rms)):
        if rms[i] < threshold:
            break
        decay_frames += 1
    decay_time = librosa.frames_to_time(decay_frames, sr=sr)

    # 3. Spectral Flatness (Tone vs Noise)
    flatness = np.mean(librosa.feature.spectral_flatness(y=y))

    # 4. High Freq Energy (Purity check)
    high_band_limit = 5000
    high_energy = np.sum(psd[freqs > high_band_limit])
    total_energy = np.sum(psd) + 1e-9
    hfer = high_energy / total_energy

    return {
        "file": os.path.basename(file_path),
        "peak_freq": peak_freq,
        "decay_time": decay_time,
        "flatness": flatness,
        "hfer": hfer
    }

def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    audio_path = project_root / "test_audio" / "mid_tom_*.wav"

    print(f"Looking for audio in: {audio_path}")
    files = glob.glob(str(audio_path))
    files.sort()

    if not files:
        print("No files found! Ensure files are in 'test_audio' and named 'mid_tom_*.wav'")
        return

    print(f"Found {len(files)} files. Analyzing Mid Tom Physics...")
    print("-" * 115)
    print(f"{'File':<25} | {'Note (Hz)':<10} | {'Decay (s)':<10} | {'Flatness':<10} | {'Treble >5k %':<12}")
    print("-" * 115)

    results = []
    for f in files:
        res = analyze_mid_tom_physics(f)
        if res:
            results.append(res)
            print(f"{res['file']:<25} | {res['peak_freq']:.1f}       | {res['decay_time']:.3f}      | {res['flatness']:.5f}    | {res['hfer']*100:.2f}%")

    if results:
        avg_freq = np.mean([r['peak_freq'] for r in results])
        avg_decay = np.mean([r['decay_time'] for r in results])

        print("-" * 115)
        print(f"AVERAGES                  | {avg_freq:.1f}       | {avg_decay:.3f}      | --          | --")
        print("-" * 115)

if __name__ == "__main__":
    main()
