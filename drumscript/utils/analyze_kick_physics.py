# 
# # uv run python drumscript/utils/analyze_kick_physics.py

import librosa
import numpy as np
import scipy.stats
import scipy.signal
import glob
import os
from pathlib import Path

def analyze_kick_physics(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None
    
    # 1. Spectral Centroid (Center of Mass of the sound)
    centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    mean_centroid = np.mean(centroid)
    
    # 2. Peak Frequency (The "Note" of the kick)
    # Welch's method for cleaner PSD
    freqs, psd = scipy.signal.welch(y, sr, nperseg=2048)
    peak_freq = freqs[np.argmax(psd)]
    
    # 3. Low Frequency Energy Ratio (LFER)
    # Energy < 150Hz vs Total Energy
    low_band_limit = 150
    low_energy = np.sum(psd[freqs < low_band_limit])
    total_energy = np.sum(psd)
    lfer = low_energy / (total_energy + 1e-9) # Safety epsilon
    
    # 4. Decay Time (Time to drop -20dB)
    rms = librosa.feature.rms(y=y)[0]
    peak_idx = np.argmax(rms)
    peak_amp = rms[peak_idx]
    threshold = peak_amp * 0.1 # -20dB
    
    decay_frames = 0
    for i in range(peak_idx, len(rms)):
        if rms[i] < threshold:
            break
        decay_frames += 1
    decay_time = librosa.frames_to_time(decay_frames, sr=sr)

    return {
        "file": os.path.basename(file_path),
        "mean_centroid": mean_centroid,
        "peak_freq": peak_freq,
        "lfer": lfer,
        "decay_time": decay_time
    }

def main():
    # Robust path finding using pathlib
    # This finds the directory where THIS script lives
    script_dir = Path(__file__).resolve().parent
    
    # Go up two levels: drumscript/utils/ -> drumscript/ -> Root
    project_root = script_dir.parent.parent
    
    # Define audio path
    audio_path = project_root / "test_audio" / "kick_*.wav"
    
    print(f"Looking for audio in: {audio_path}")
    files = glob.glob(str(audio_path))
    files.sort() # Ensure consistent order

    if not files:
        print("No files found! Check that your folder is named 'test_audio' and sits in the project root.")
        return

    print(f"Found {len(files)} files. Analyzing...")
    print("-" * 100)
    print(f"{'File':<15} | {'Centroid (Hz)':<15} | {'Peak Freq (Hz)':<15} | {'Low Energy %':<15} | {'Decay (s)':<15}")
    print("-" * 100)

    results = []
    for f in files:
        res = analyze_kick_physics(f)
        if res:
            results.append(res)
            print(f"{res['file']:<15} | {res['mean_centroid']:.2f}           | {res['peak_freq']:.2f}           | {res['lfer']*100:.1f}%           | {res['decay_time']:.3f}")

    # Calculate Averages for your Constants
    if results:
        avg_centroid = np.mean([r['mean_centroid'] for r in results])
        avg_peak = np.mean([r['peak_freq'] for r in results])
        avg_lfer = np.mean([r['lfer'] for r in results])
        
        print("-" * 100)
        print(f"AVERAGES        | {avg_centroid:.2f}           | {avg_peak:.2f}           | {avg_lfer*100:.1f}%           | --")
        print("-" * 100)

if __name__ == "__main__":
    main()