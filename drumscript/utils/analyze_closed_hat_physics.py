import librosa
import numpy as np
import scipy.signal
import glob
import os
from pathlib import Path
from datetime import datetime

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f'\ndate/time: {datetimestamp}')

def analyze_closed_hat_physics(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None
    
    # 1. Decay Time (The primary differentiator)
    # Closed hats should be very tight.
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
    
    # 2. Spectral Centroid
    centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
    
    # 3. Air Band (>7k)
    freqs, psd = scipy.signal.welch(y, sr, nperseg=2048)
    high_band_limit = 7000
    high_energy = np.sum(psd[freqs > high_band_limit])
    total_energy = np.sum(psd) + 1e-9
    hfer_7k = high_energy / total_energy

    return {
        "file": os.path.basename(file_path),
        "decay_time": decay_time,
        "centroid": centroid,
        "hfer_7k": hfer_7k
    }

def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    audio_path = project_root / "test_audio" / "hatclosed_*.wav"
    
    print(f"Looking for audio in: {audio_path}")
    files = glob.glob(str(audio_path))
    files.sort()

    if not files:
        print("No files found! Ensure files are in 'test_audio' and named 'hatclosed_*.wav'")
        return

    print(f"Found {len(files)} files. Analyzing Closed Hi-Hat Physics...")
    print("-" * 100)
    print(f"{'File':<35} | {'Decay (s)':<10} | {'Centroid':<10} | {'Air >7k %':<12}")
    print("-" * 100)

    results = []
    for f in files:
        res = analyze_closed_hat_physics(f)
        if res:
            results.append(res)
            print(f"{res['file']:<35} | {res['decay_time']:.3f}      | {res['centroid']:.0f}Hz      | {res['hfer_7k']*100:.1f}%")
            
    if results:
        avg_decay = np.mean([r['decay_time'] for r in results])
        print("-" * 100)
        print(f"AVERAGES                            | {avg_decay:.3f}      | --          | --")
        print("-" * 100)

if __name__ == "__main__":
    main()