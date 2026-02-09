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


def analyze_open_hat_physics(file_path):
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return None
    
    # 1. Decay Time (Resonance)
    # This is the PRIMARY differentiator between Open and Closed Hats.
    rms = librosa.feature.rms(y=y)[0]
    peak_idx = np.argmax(rms)
    peak_amp = rms[peak_idx]
    threshold = peak_amp * 0.1 # -20dB point
    
    decay_frames = 0
    for i in range(peak_idx, len(rms)):
        if rms[i] < threshold:
            break
        decay_frames += 1
    decay_time = librosa.frames_to_time(decay_frames, sr=sr)
    
    # 2. Spectral Centroid (Brightness)
    # Metals are much brighter than drums.
    centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
    
    # 3. High Frequency Energy Ratio (HFER > 7000Hz)
    # Cymbals shine in the very high air band.
    freqs, psd = scipy.signal.welch(y, sr, nperseg=2048)
    high_band_limit = 7000
    high_energy = np.sum(psd[freqs > high_band_limit])
    total_energy = np.sum(psd) + 1e-9
    hfer_7k = high_energy / total_energy

    # 4. Zero Crossing Rate (Texture)
    # High ZCR indicates noisy, high-frequency content (metal).
    zcr = np.mean(librosa.feature.zero_crossing_rate(y))

    return {
        "file": os.path.basename(file_path),
        "decay_time": decay_time,
        "centroid": centroid,
        "hfer_7k": hfer_7k,
        "zcr": zcr
    }

def main():
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    audio_path = project_root / "test_audio" / "hatopen_*.wav"
    
    print(f"Looking for audio in: {audio_path}")
    files = glob.glob(str(audio_path))
    files.sort()

    if not files:
        print("No files found! Ensure files are in 'test_audio' and named 'hatopen_*.wav'")
        return

    print(f"Found {len(files)} files. Analyzing Open Hi-Hat Physics...")
    print("-" * 115)
    print(f"{'File':<30} | {'Decay (s)':<10} | {'Centroid':<10} | {'Air >7k %':<12} | {'ZCR':<10}")
    print("-" * 115)

    results = []
    for f in files:
        res = analyze_open_hat_physics(f)
        if res:
            results.append(res)
            print(f"{res['file']:<30} | {res['decay_time']:.3f}      | {res['centroid']:.0f}Hz      | {res['hfer_7k']*100:.1f}%        | {res['zcr']:.3f}")
            
    if results:
        avg_decay = np.mean([r['decay_time'] for r in results])
        avg_cent = np.mean([r['centroid'] for r in results])
        avg_hfer = np.mean([r['hfer_7k'] for r in results])
        
        print("-" * 115)
        print(f"AVERAGES                       | {avg_decay:.3f}      | {avg_cent:.0f}Hz      | {avg_hfer*100:.1f}%        | --")
        print("-" * 115)

if __name__ == "__main__":
    main()