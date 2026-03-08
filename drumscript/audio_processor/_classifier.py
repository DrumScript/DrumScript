# DrumScript/audio_processor/_classifier.py
"""
This module deterministically classifies drum hits from audio slices
using pure DSP math and physical frequency constants.
"""
import os
import argparse
import librosa
import numpy as np
from drumscript.notation_generator.constants import SAMPLE_RATE, ONSET_SLICE_DURATION_MS, N_FFT, HOP_LENGTH, KICK_FREQ_MIN, KICK_FREQ_MAX, KICK_LFER_MIN, SNARE_FREQ_MIN, SNARE_FREQ_MAX, SNARE_HFER_MIN,IDIOPHONE_MIN_HFER_5K
from datetime import datetime

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f'\ndate/time: {datetimestamp}')

def get_audio_slice(audio_data: np.ndarray, onset_time: float, sr: int) -> np.ndarray:
    """
    Cuts a specific millisecond slice of audio starting exactly at the onset time.
    """
    start_sample = int(onset_time * sr)
    # Convert duration from ms to seconds, then to samples
    duration_secs = ONSET_SLICE_DURATION_MS / 1000.0 
    end_sample = start_sample + int(duration_secs * sr)
    
    # Pad with zeros if the slice goes past the end of the audio file
    if end_sample > len(audio_data):
        slice_data = audio_data[start_sample:]
        pad_length = end_sample - len(audio_data)
        slice_data = np.pad(slice_data, (0, pad_length), mode='constant')
        return slice_data
        
    return audio_data[start_sample:end_sample]

def extract_features(audio_slice: np.ndarray, sr: int) -> dict:
    """
    Analyses the audio slice and extracts the physical DSP features.
    """
    features = {}
    
    # 1. Compute the Frequency Spectrum (FFT)
    # We use magnitude (abs) of the Short-Time Fourier Transform
    stft = np.abs(librosa.stft(audio_slice, n_fft=N_FFT, hop_length=HOP_LENGTH))
    
    # Average the spectrum across the tiny time slice to get one master frequency profile
    spectrum = np.mean(stft, axis=1)
    frequencies = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
    
    # 2. Find the Peak Frequency (The strongest fundamental tone)
    peak_idx = np.argmax(spectrum)
    features['peak_freq'] = frequencies[peak_idx]
    
    # 3. Calculate Spectral Centroid (The "Center of Mass" or Brightness)
    centroid = librosa.feature.spectral_centroid(S=stft, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)
    features['centroid'] = np.mean(centroid)
    
    # 4. Calculate Energy Ratios (LFER & HFER)
    total_energy = np.sum(spectrum)
    if total_energy == 0: # Prevent division by zero on silent slices
        features['lfer'] = 0.0
        features['hfer'] = 0.0
        features['hfer_5k'] = 0.0
        return features

    # Low Frequency Energy Ratio (Energy below 150Hz)
    low_idx = np.where(frequencies <= 150.0)[0]
    features['lfer'] = np.sum(spectrum[low_idx]) / total_energy
    
    # Snare Wire Energy Ratio (Energy > 2000Hz)
    high_idx = np.where(frequencies > 2000.0)[0]
    features['hfer'] = np.sum(spectrum[high_idx]) / total_energy
    
    # Cymbal/Hat Energy Ratio (Energy > 5000Hz)
    metal_idx = np.where(frequencies > 5000.0)[0]
    features['hfer_5k'] = np.sum(spectrum[metal_idx]) / total_energy
    
    return features

def classify_onset(features: dict) -> list[str]:
    """
    Applies deterministic physics rules to classify the hit.
    Returns a list because multiple drums can hit simultaneously!
    """
    detected_instruments = []
    
    # RULE 1: KICK DRUM
    # Does it have sub-bass energy, and is the peak frequency in the kick zone?
    if features['lfer'] >= KICK_LFER_MIN and (KICK_FREQ_MIN <= features['peak_freq'] <= KICK_FREQ_MAX):
        detected_instruments.append('kick')
        
    # RULE 2: SNARE DRUM
    # Is the peak frequency in the snare body zone, AND does it have wire buzz (>2kHz)?
    if (SNARE_FREQ_MIN <= features['peak_freq'] <= SNARE_FREQ_MAX) and features['hfer'] >= SNARE_HFER_MIN:
        detected_instruments.append('snare')
        
    # RULE 3: METALS (Hi-Hats / Cymbals)
    # Does it have massive extreme high-frequency energy (>5kHz)?
    if features['hfer_5k'] >= IDIOPHONE_MIN_HFER_5K:
        # Note: We can expand this later using the decay constraints to split Hats vs Crashes
        if features['centroid'] > 4000:
            detected_instruments.append('hi_hat_closed')
        else:
            detected_instruments.append('ride') 
            
    # Fallback if the logic doesn't catch it
    if not detected_instruments:
        detected_instruments.append('unknown')
        
    return detected_instruments

def process_track(audio_data: np.ndarray, onset_times: list[float], sr: int) -> list[dict]:
    """
    The main orchestrator. Takes the raw audio and the timestamps, 
    and returns a list of mapped dictionary events.
    """
    final_score = []
    
    for time in onset_times:
        # 1. Get the snapshot
        slice_data = get_audio_slice(audio_data, time, sr)
        
        # 2. Extract the physics math
        features = extract_features(slice_data, sr)
        
        # 3. Apply the rules
        instruments = classify_onset(features)
        
        # 4. Save to the final output list
        final_score.append({
            "time_sec": float(time),
            "instruments": instruments,
            "debug_features": features # Kept so we can see WHY it made its decision!
        })
        
    return final_score

if __name__ == "__main__":
    from drumscript.audio_processor.audio_loader import load_audio, normalise_audio
    from drumscript.audio_processor.onset_detector import detect_onsets
    from drumscript.audio_processor.tempo_detector import estimate_tempo
    from drumscript.notation_generator._midi_exporter import export_to_midi
    from drumscript.notation_generator.pdf_exporter import export_pdf
    
    parser = argparse.ArgumentParser(description="Classify detected onsets.")
    parser.add_argument("input_audio", help="Path to the input audio file")
    args = parser.parse_args()
    
    audio_path = os.path.abspath(args.input_audio)
    print(f"Loading: {audio_path}...")
    
    audio_data, sr = load_audio(audio_path, sr=SAMPLE_RATE)
    normalised_audio = normalise_audio(audio_data)
    
    print("Running Onset Detector...")
    onset_times = detect_onsets(normalised_audio, sr)
    
    print(f"Running Classifier on {len(onset_times)} events...")
    score_events = process_track(normalised_audio, onset_times, sr)

    #log_dir = "outputs/pdf_exporter" # Write the log to a text file
    events_log_dir = "outputs/_classifier/_events_log_dir" # Write the log to a text file
    os.makedirs(events_log_dir, exist_ok=True) # Ensure the directory exists
    log_file_path = os.path.join(events_log_dir, "classification_log.txt")
    
    print("\n--- FINAL CLASSIFICATION LOG ---")

        
    # Open the file in write mode ('w') so it refreshes cleanly on every run
    with open(log_file_path, "w") as log_file:
        log_file.write(f"--- FINAL CLASSIFICATION LOG ---\n")
        log_file.write(f"Source Audio: {audio_path}\n")
        log_file.write(f"Total Events Detected: {len(score_events)}\n\n")
        
        for event in score_events: 
            time_f = event["time_sec"]
            insts = ", ".join(event["instruments"])
            pf = event["debug_features"]["peak_freq"]
            hf = event["debug_features"]["hfer"]
            lf = event["debug_features"]["lfer"]
            
            # Format the line once
            log_line = f"Time: {time_f:.3f}s | Inst: [{insts}] | PeakF: {pf:.1f}Hz | LFER: {lf:.2f} | HFER: {hf:.2f}"
            
            # Print to terminal AND write to file
            print(log_line)
            log_file.write(log_line + "\n")
            
            # COMMENTED OUT TO PREVENT SPAMMING IN THE LOOP
            # print(f"\nSUCCESS: Classification log saved to -> {log_file_path}")
            
    # PRINTED ONCE OUTSIDE THE LOOP INSTEAD
    print(f"\nSUCCESS: Classification log saved to -> {log_file_path}")


    # COMMENTED OUT THE REDUNDANT SECOND LOOP SO IT DOESN'T PRINT TWICE
    #for event in score_events[:20]: # Print just the first 20 to avoid spamming terminal
    # for event in score_events: # Print ALL events and their stats/classifications
    #     time_f = event["time_sec"]
    #     insts = ", ".join(event["instruments"])
    #     pf = event["debug_features"]["peak_freq"]
    #     hf = event["debug_features"]["hfer"]
    #     lf = event["debug_features"]["lfer"]
    #     
    #     print(f"Time: {time_f:.3f}s | Inst: [{insts}] | PeakF: {pf:.1f}Hz | LFER: {lf:.2f} | HFER: {hf:.2f}")
    #     
    # if len(score_events) > 20:
    #      print(f"... and {len(score_events) - 20} more events.")

    # COMMENTED OUT REDUNDANT PROCESS TRACK CALL
    # print(f"Running Classifier on {len(onset_times)} events...")
    # score_events = process_track(normalised_audio, onset_times, sr)

    pass
        
    # estimate tempo


    detected_tempo = estimate_tempo(audio_data, SAMPLE_RATE) / 2

    # --- 1) Transform to MIDI ---
    #midi_dir = "outputs/midi_exporter"
    midi_dir = "outputs/_classifier/_midi_exporter"
    os.makedirs(midi_dir, exist_ok=True)
    output_file = os.path.join(midi_dir, "drumscript_transcription.mid")
    export_to_midi(score_events, output_file, tempo=detected_tempo)

    # --- 2) Transform to PDF ---
    pdf_dir = "outputs/_classifier/_classifier/_pdf_exporter"
    pdf_output = os.path.join(pdf_dir, "drumscript_score.pdf")
    #pdf_output = os.path.join(log_dir, "drumscript_score.pdf")
    #pdf_output = os.path.join(events_log_dir, "drumscript_score.pdf")
    export_pdf(score_events, pdf_output, detected_tempo)