# local_tests/classification_engine/librosa/get_fundamental_frequencies.py

import pandas as pd
import librosa
import numpy as np
import os
import sys

# --- CONFIGURATION ---
# Adjust these relative to where you run the script from (usually project root)
METADATA_PATH = "test_audio/dataset/samples_metadata.csv" 
AUDIO_DIR = "test_audio/dataset/samples"
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

def main():
    print("--- STARTING FUNDAMENTAL FREQUENCY ANALYSIS ---")
    
    # 1. Resolve Paths
    # If script is run from project root, these should work. 
    # If not, we try to resolve relative to this script.
    base_dir = os.getcwd()
    if not os.path.exists(METADATA_PATH):
        # Try finding it relative to project root if run from subfolder
        potential_path = os.path.join(base_dir, "../../../", METADATA_PATH)
        if os.path.exists(potential_path):
             # Update global paths
             print("Adjusting paths relative to script location...")
             pass # Logic handles itself if we just run from root usually
    
    if not os.path.exists(METADATA_PATH):
        print(f"ERROR: Could not find {METADATA_PATH}. Run this from the project root.")
        sys.exit(1)

    # 2. Load Data
    df = pd.read_csv(METADATA_PATH)
    
    # Filter: Remove Claps (id 0)
    df = df[df['type_id'] != 0].copy()
    
    # Map Names
    df['type_name'] = df['type_id'].map(TYPE_MAP)
    
    # 3. Processing
    results = []
    
    print(f"{'SAMPLE NAME':<20} | {'TYPE':<12} | {'FREQ (Hz)':<10}")
    print("-" * 50)

    # Grouping by type for display (DataFrame is already somewhat ordered, but let's ensure)
    df = df.sort_values(by=['type_name', 'sample_name'])
    
    current_type = None
    
    for _, row in df.iterrows():
        sample_name = row['sample_name']
        drum_type = row['type_name']
        
        # Header for new drum groups
        if drum_type != current_type:
            print(f"\n--- {drum_type.upper()} ---")
            current_type = drum_type
            
        file_path = os.path.join(AUDIO_DIR, f"{sample_name}.wav")
        
        if not os.path.exists(file_path):
            print(f"{sample_name:<20} | {drum_type:<12} | FILE NOT FOUND")
            continue
            
        try:
            y, sr = librosa.load(file_path, sr=None)
            freq = measure_fundamental_freq(y, sr)
            
            print(f"{sample_name:<20} | {drum_type:<12} | {freq:.2f}")
            
            results.append({
                "sample_name": sample_name,
                "type": drum_type,
                "fundamental_freq_hz": round(freq, 2)
            })
            
        except Exception as e:
            print(f"{sample_name:<20} | {drum_type:<12} | ERROR: {e}")

    # 4. Save CSV
    if results:
        out_df = pd.DataFrame(results)
        out_df.to_csv(OUTPUT_CSV, index=False)
        print(f"\nAnalysis Complete.")
        print(f"Results saved to: {OUTPUT_CSV}")
    else:
        print("\nNo results generated (check audio paths).")

if __name__ == "__main__":
    main()