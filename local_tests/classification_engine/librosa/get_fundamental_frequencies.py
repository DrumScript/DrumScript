# local_tests/classification_engine/librosa/get_fundamental_frequencies.py
## Run from root using `uv run python local_tests/classification_engine/librosa/get_fundamental_frequencies.py
import pandas as pd
import librosa
import numpy as np
import os
import sys
import glob
import warnings
warnings.filterwarnings('ignore') # Suppress librosa warnings

# --- CONFIGURATION ---
METADATA_PATH = "test_audio/dataset/samples_metadata.csv" 
# AUDIO_DIR = "test_audio/dataset/samples" # only one folder of audio samples
SAMPLES_DIR = "test_audio/dataset/samples"
TOMS_DIR = "test_audio/the_dugg_funnie_private_reverse_toms"

OUTPUT_CSV = os.path.join(os.path.dirname(__file__), "fundamental_frequencies_report.csv")

# Map type_id to names (ignoring claps later)
TYPE_MAP = {
    0: "clap",
    1: "closed_hat",
    2: "kick",
    3: "open_hat",
    4: "snare"
}

def measure_fundamental_freq(y, sr, min_freq=20, max_freq=2000):
    """
    Calculates the dominant frequency using the Kick Rule method (STFT Masking).
    Window is widened to 20-2000Hz to ensure we capture Snares/Toms correctly.
    """
    # 1. Compute STFT (Same settings as Kick Rule)
    n_fft = 2048
    hop_length = 512
    S = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
    S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)

    # 2. Find the frame with the maximum energy (the "hit")
    max_energy_frame = np.argmax(np.max(S_db, axis=0))
    hit_spectrum = S_db[:, max_energy_frame]
    
    # 3. Get Frequencies
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    # 4. Filter for relevant frequencies (The "Mask")
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    
    if not np.any(mask):
        return 0.0
        
    masked_spectrum = hit_spectrum[mask]
    masked_freqs = freqs[mask]
    
    # 5. Find peak within that range
    peak_idx = np.argmax(masked_spectrum)
    peak_freq = masked_freqs[peak_idx]
    
    return peak_freq

def classify_tom(filename):
    """
    Determines tom type based on filename keywords.
    """
    fname = filename.lower()
    if "high" in fname:
        return "high_tom"
    elif "mid" in fname:
        return "mid_tom"
    elif "low" in fname or "floor" in fname:
        return "low_tom"
    return "tom_other"

def main():
    print("--- STARTING FUNDAMENTAL FREQUENCY ANALYSIS ---")
    results = []

    # =========================================================
    # PART 1: Process Metadata CSV (Kicks, Snares, Hats)
    # =========================================================
    if os.path.exists(METADATA_PATH):
        print(f"\nProcessing Standard Library: {METADATA_PATH}")
        df = pd.read_csv(METADATA_PATH)
        
        # Filter out Claps
        df = df[df['type_id'] != 0].copy()
        df['type_name'] = df['type_id'].map(TYPE_MAP)
        
        for _, row in df.iterrows():
            sample_name = row['sample_name']
            drum_type = row['type_name']
            
            file_path = os.path.join(SAMPLES_DIR, f"{sample_name}.wav")
            
            if os.path.exists(file_path):
                try:
                    y, sr = librosa.load(file_path, sr=None)
                    freq = measure_fundamental_freq(y, sr)
                    results.append({
                        "sample_name": sample_name,
                        "type": drum_type,
                        "freq_hz": round(freq, 2)
                    })
                except Exception:
                    pass
    else:
        print(f"Warning: Metadata file not found at {METADATA_PATH}")

    # =========================================================
    # PART 2: Process Toms Folder
    # =========================================================
    if os.path.exists(TOMS_DIR):
        print(f"\nProcessing Toms Library: {TOMS_DIR}")
        
        # Glob all .wav files in the toms directory
        wav_files = glob.glob(os.path.join(TOMS_DIR, "*.wav"))
        
        if not wav_files:
            print("   No .wav files found in Toms directory.")
            
        for file_path in wav_files:
            filename = os.path.basename(file_path)
            
            # Skip hidden files
            if filename.startswith('.'):
                continue
                
            drum_type = classify_tom(filename)
            
            try:
                y, sr = librosa.load(file_path, sr=None)
                freq = measure_fundamental_freq(y, sr)
                
                results.append({
                    "sample_name": filename,
                    "type": drum_type,
                    "freq_hz": round(freq, 2)
                })
            except Exception as e:
                print(f"   Error loading {filename}: {e}")
    else:
        print(f"Warning: Toms directory not found at {TOMS_DIR}")

    # =========================================================
    # OUTPUT AND REPORTING
    # =========================================================
    if not results:
        print("\nNo audio files were analyzed.")
        return

    # Create DataFrame
    out_df = pd.DataFrame(results)
    
    # Sort by Type then Name for the clean grouped look you requested
    out_df = out_df.sort_values(by=['type', 'sample_name'])

    # Print Report to Console
    print("\n" + "="*60)
    print(f"{'TYPE':<15} | {'SAMPLE NAME':<30} | {'FREQ (Hz)':<10}")
    print("="*60)
    
    current_type = None
    for _, row in out_df.iterrows():
        if row['type'] != current_type:
            print("-" * 60) # Separator between groups
            current_type = row['type']
            
        # Truncate long names for display
        display_name = (row['sample_name'][:27] + '..') if len(row['sample_name']) > 29 else row['sample_name']
        
        print(f"{row['type']:<15} | {display_name:<30} | {row['freq_hz']:.2f}")

    # Save to CSV
    out_df.to_csv(OUTPUT_CSV, index=False)
    print("\n" + "="*60)
    print(f"Analysis Complete. Full results saved to:\n{OUTPUT_CSV}")
    print("="*60)

if __name__ == "__main__":
    main()