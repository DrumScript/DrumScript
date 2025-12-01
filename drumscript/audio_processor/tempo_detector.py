# DrumScript/audio_processor/tempo_detector.py
# ------------------------------------------------------------------------------------------------------------
"""
This module contains functions for automatic tempo detection from audio data.
"""
# Import packages: ------------------------------------------------------------------------------------------------

import librosa
import numpy as np
import os
import argparse
# from datetime import datetime

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')
# --- Define function --------------------------------------------------------------------------------------------

def estimate_tempo(audio_data, sr):
    """
    Estimates tempo from the tempogram, but restricted to a plausible range.
    (Corrected to avoid INF and extreme BPM errors, ie 10500 BPM).
    """
    if audio_data.size == 0:
        return 0.0
    oenv = librosa.onset.onset_strength(y=audio_data, sr=sr, hop_length=256)
    tempogram = librosa.feature.tempogram(onset_envelope=oenv, sr=sr, hop_length=256)
    tempo_spectrum = np.sum(tempogram, axis=1)
    tempo_freqs = librosa.tempo_frequencies(tempogram.shape[0], sr=sr, hop_length=256)
    
    # --- FIX for extreme BPM error ---
    # Create a mask to only consider tempos in a plausible musical range (e.g., 60-240 BPM)
    plausible_tempos_mask = (tempo_freqs >= 60) & (tempo_freqs <= 240)
    
    # Find the index of the peak within the plausible range
    plausible_spectrum = tempo_spectrum[plausible_tempos_mask]
    if plausible_spectrum.size == 0:
        return 120.0 # Return default if no energy in plausible range
        
    peak_idx_in_plausible_range = np.argmax(plausible_spectrum)
    
    # Convert that index back to a BPM value
    plausible_tempo_freqs = tempo_freqs[plausible_tempos_mask]
    estimated_bpm = plausible_tempo_freqs[peak_idx_in_plausible_range]
    
    return estimated_bpm
# =====================================================================================================
# MAIN BLOCK - for local testing of this function

if __name__ == "__main__":
    from drumscript.audio_processor.audio_loader import load_audio, normalise_audio
    parser = argparse.ArgumentParser(description="Estimate the tempo of an audio file.")
    parser.add_argument("audio_file_path", type=str,
                        help="Path to the audio file to be processed.")
    args = parser.parse_args()
    actual_drum_recording_path = args.audio_file_path # audio_file_path, relative to ROOT, not the path of this script

    try:
        # Load and normalise the audio
        print(f"Attempting to load: {actual_drum_recording_path}")
        audio, sr = load_audio(actual_drum_recording_path, sr=44100)
        normalised_audio = normalise_audio(audio)
        
        # Estimate the tempo
        bpm = estimate_tempo(normalised_audio, sr)
        print(f"Estimated Tempo: {int(round(bpm))} BPM")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
# =====================================================================================================
# Uncomment to use, for clearer error logs
# print("\n# ------------------------------------------------------------------------------------")