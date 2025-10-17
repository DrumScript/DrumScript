# DrumScript/drum_classifier/predict.py
import os
import json
import librosa
import numpy as np
from typing import List, Dict, Any

# --- Drum Mapping Dictionary for Enhanced Output ---
DRUM_METADATA = {
    'kick': { 'midi_pitch': 36, 'note_head_type': 'normal', 'staff_position': 'F2', 'display_name': 'Kick Drum' },
    'snare': { 'midi_pitch': 38, 'note_head_type': 'normal', 'staff_position': 'C3', 'display_name': 'Snare Drum' },
    'hi_hat_closed': { 'midi_pitch': 42, 'note_head_type': 'x', 'staff_position': 'F#3', 'display_name': 'Hi-Hat (Closed)' },
    'hi_hat_open': { 'midi_pitch': 46, 'note_head_type': 'x-open', 'staff_position': 'F#3', 'display_name': 'Hi-Hat (Open)' },
    'low_tom': { 'midi_pitch': 41, 'note_head_type': 'normal', 'staff_position': 'A2', 'display_name': 'Low Tom' },
    'mid_tom': { 'midi_pitch': 45, 'note_head_type': 'normal', 'staff_position': 'C3', 'display_name': 'Mid Tom' },
    'high_tom': { 'midi_pitch': 48, 'note_head_type': 'normal', 'staff_position': 'E3', 'display_name': 'High Tom' },
    'crash': { 'midi_pitch': 49, 'note_head_type': 'x', 'staff_position': 'A3', 'display_name': 'Crash Cymbal' },
    'ride': { 'midi_pitch': 51, 'note_head_type': 'x', 'staff_position': 'B3', 'display_name': 'Ride Cymbal' }
}

# --- Rule-based thresholds ---
KICK_SPECTRAL_CENTROID_MAX = 400
MID_TOM_CENTROID_MIN = 400
MID_TOM_CENTROID_MAX = 800
MID_TOM_ZCR_MAX = 0.05
HIGH_TOM_CENTROID_MIN = 800
HIGH_TOM_CENTROID_MAX = 1380
LOW_TOM_CENTROID_MIN = 1380
LOW_TOM_CENTROID_MAX = 1600
LOW_TOM_ZCR_MAX = 0.05
SNARE_CENTROID_MIN = 1600
SNARE_CENTROID_MAX = 4000
SNARE_ZCR_MIN = 0.09

# --- Define a shared Cymbal frequency space ---
CYMBAL_CENTROID_MIN = 4000
CYMBAL_CENTROID_MAX = 7000
CRASH_CENTROID_MIN = 4000
CRASH_CENTROID_MAX = 7000 # Cymbals are bright, but less than hi-hats.
RIDE_SUSTAIN_MIN = 0.4
RIDE_SUSTAIN_MAX = 0.8  # A ride has medium sustain
CRASH_SUSTAIN_MIN = 0.8  # Crashes have very high sustain.
HIHAT_CENTROID_MIN = 9000
HIHAT_ZCR_MIN = 0.2
HIHAT_SUSTAIN_THRESHOLD = 0.5

# --- Refractory period constants ---
OPEN_HIHAT_REFRACTORY_PERIOD_S = 0.6
TOM_REFRACTORY_PERIOD_S = 3.0
CRASH_REFRACTORY_PERIOD_S = 10.0 # ie crash test.wav duration
RIDE_REFRACTORY_PERIOD_S = 4.0 # Rides can be played faster than crashes

# --- Refractory period constants ---
OPEN_HIHAT_REFRACTORY_PERIOD_S = 0.6
TOM_REFRACTORY_PERIOD_S = 3.0 # Keep this long to handle all toms


# --- Core Classification Logic ---
def predict_drum_hits(onset_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    classified_events = []
    last_open_hihat_time = -1.0
    last_tom_time = -1.0
    last_crash_time = -1.0
    last_ride_time = -1.0

    # ---- Classification Block ----

    for onset in onset_features:
        # ---- Refractory period checks ----
        if last_open_hihat_time > 0 and (onset['onset_time'] - last_open_hihat_time) < OPEN_HIHAT_REFRACTORY_PERIOD_S:
            print(f"\n--- Ignoring Onset at {onset['onset_time']:.2f}s (within refractory period of an open hi-hat) ---")
            continue
        if last_tom_time > 0 and (onset['onset_time'] - last_tom_time) < TOM_REFRACTORY_PERIOD_S:
            print(f"\n--- Ignoring Onset at {onset['onset_time']:.2f}s (within refractory period of a tom) ---")
            continue
        if last_crash_time > 0 and (onset['onset_time'] - last_crash_time) < CRASH_REFRACTORY_PERIOD_S:
            print(f"\n--- Ignoring Onset... (within crash refractory period) ---")
        if last_ride_time > 0 and (onset['onset_time'] - last_ride_time) < RIDE_REFRACTORY_PERIOD_S:
            print(f"\n--- Ignoring Onset... (within ride refractory period) ---")
            continue

        # ---- Debugging block ----
        print(f"\n--- Processing Onset at {onset['onset_time']:.2f}s ---")
        print(f"  - Spectral Centroid: {onset['spectral_centroid']:.2f}")
        print(f"  - Zero-Crossing Rate: {onset['zero_crossing_rate']:.4f}")
        print(f"  - Sustain Level: {onset['sustain_level']:.2f}")

        # ---- Rule-sets ----
        if onset['spectral_centroid'] < KICK_SPECTRAL_CENTROID_MAX:
            print("  - RESULT: Classified as KICK.")
            classified_events.extend(create_detailed_drum_events(['kick'], onset['onset_time']))
            continue

        elif MID_TOM_CENTROID_MIN < onset['spectral_centroid'] < MID_TOM_CENTROID_MAX and \
             onset['zero_crossing_rate'] < MID_TOM_ZCR_MAX:
            print("  - RESULT: Classified as MID TOM.")
            classified_events.extend(create_detailed_drum_events(['mid_tom'], onset['onset_time']))
            last_tom_time = onset['onset_time']
            continue

        elif HIGH_TOM_CENTROID_MIN < onset['spectral_centroid'] < HIGH_TOM_CENTROID_MAX and \
             onset['zero_crossing_rate'] < LOW_TOM_ZCR_MAX: # Using same ZCR for all toms?
            print("  - RESULT: Classified as HIGH TOM.")
            classified_events.extend(create_detailed_drum_events(['high_tom'], onset['onset_time']))
            last_tom_time = onset['onset_time']
            continue

        elif LOW_TOM_CENTROID_MIN < onset['spectral_centroid'] < LOW_TOM_CENTROID_MAX and \
             onset['zero_crossing_rate'] < LOW_TOM_ZCR_MAX:
            print("  - RESULT: Classified as LOW TOM.")
            classified_events.extend(create_detailed_drum_events(['low_tom'], onset['onset_time']))
            last_tom_time = onset['onset_time']
            continue

        # --- Ride Cymbal (check this BEFORE the crash) ---
        elif CYMBAL_CENTROID_MIN < onset['spectral_centroid'] < CYMBAL_CENTROID_MAX and \
             RIDE_SUSTAIN_MIN < onset['sustain_level'] < RIDE_SUSTAIN_MAX:
            print("  - RESULT: Classified as RIDE.")
            classified_events.extend(create_detailed_drum_events(['ride'], onset['onset_time']))
            last_ride_time = onset['onset_time'] # Trigger ride cooldown
            continue

        # --- Crash Cymbal Rule (now uses the shared CYMBAL constant) ---
        elif CYMBAL_CENTROID_MIN < onset['spectral_centroid'] < CYMBAL_CENTROID_MAX and \
             onset['sustain_level'] > CRASH_SUSTAIN_MIN:
            print("  - RESULT: Classified as CRASH.")
            classified_events.extend(create_detailed_drum_events(['crash'], onset['onset_time']))
            last_crash_time = onset['onset_time']
            continue

        elif SNARE_CENTROID_MIN < onset['spectral_centroid'] < SNARE_CENTROID_MAX and \
             onset['zero_crossing_rate'] >= SNARE_ZCR_MIN:
            print("  - RESULT: Classified as SNARE.")
            classified_events.extend(create_detailed_drum_events(['snare'], onset['onset_time']))
            continue

        elif onset['spectral_centroid'] > HIHAT_CENTROID_MIN and \
             onset['zero_crossing_rate'] >= HIHAT_ZCR_MIN:
            print("  - RESULT: Potentially a Hi-Hat...")
            if onset['sustain_level'] > HIHAT_SUSTAIN_THRESHOLD:
                print("    - Sustain is HIGH. Classified as OPEN HI-HAT.")
                classified_events.extend(create_detailed_drum_events(['hi_hat_open'], onset['onset_time']))
                last_open_hihat_time = onset['onset_time']
            else:
                print("    - Sustain is LOW. Classified as CLOSED HI-HAT.")
                classified_events.extend(create_detailed_drum_events(['hi_hat_closed'], onset['onset_time']))
            continue
        
        print("  - RESULT: No rule matched.")

    return classified_events

# This helper function is still very useful. It now takes a
# list of classified labels for a single onset (for now, just one label, but
# this supports concurrent hits in the future) and creates the detailed output.
def create_detailed_drum_events(predicted_drums: List[str], onset_time: float) -> List[Dict[str, Any]]:
    
    # Creates detailed drum event objects with metadata for a list of predicted drums.
    
    detailed_events = []
    for drum_type in predicted_drums:
        if drum_type in DRUM_METADATA:
            event = {
                'drum_type': drum_type,
                'onset_time_seconds': round(onset_time, 2),
                'midi_pitch': DRUM_METADATA[drum_type]['midi_pitch'],
                'note_head_type': DRUM_METADATA[drum_type]['note_head_type'],
                'staff_position': DRUM_METADATA[drum_type]['staff_position'],
            }
            detailed_events.append(event)
    return detailed_events

# --- Main execution block for testing ---
if __name__ == "__main__":
        # --- Project-Specific Imports ---
    # These functions are now imported from the audio_processor module,
    # creating a clear workflow: 1. Process Audio -> 2. Classify Features.
    # from DrumScriptimport audio_processor
    from audio_processor.audio_loader import load_audio
    from audio_processor.onset_detector import detect_onsets
    from audio_processor.feature_extractor import extract_features_for_onsets

    # This block now demonstrates the new, correct workflow:
    # 1. Load audio and find onsets using audio_processor.
    # 2. Extract features for those onsets using audio_processor.
    # 3. Classify the features using the rule-based system in this script.

    print("--- Running Rule-Based Drum Classifier Example ---")

    # Define paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) # Go up two levels
    # IMPORTANT: Place a test audio file in test_audio folder to run the example.
    test_audio_path = os.path.join(project_root, "test_audio", "test.wav")
    print(f'project_root: {project_root}')
    print(f'test_audio_path: {test_audio_path}')
    

    if not os.path.exists(test_audio_path):
        print(f"Error: Test audio file not found at {test_audio_path}")
        print("Please place a .wav file named 'test.wav' in the 'test_audio' directory.")
    else:
        # --- 1. Audio Processing ---
        print(f"Loading and processing audio file: {test_audio_path}")
        y, sr = load_audio(test_audio_path, sr=44100)
        onset_times = detect_onsets(y, sr)
        print(f"Detected {len(onset_times)} onsets.")

        # --- 2. Feature Extraction ---
        print("Extracting features for each onset...")
        all_onset_features = extract_features_for_onsets(y, sr, onset_times)
        print("Feature extraction complete.")

        # --- 3. Classification ---
        print("Classifying onsets using rule-based system...")
        classified_drum_events = predict_drum_hits(all_onset_features)
        # print(f"Classification complete. Found {len(classified_drum_events)} potential kick drum events.") # COMMENT OUT BUT KEEP FOR NOW. REMOVE LATER
        print(f"Classification complete. Found {len(classified_drum_events)} drum events.")

        # --- 4. Output Results ---
        if classified_drum_events:
            output_dir = os.path.dirname(__file__)
            output_filepath = os.path.join(output_dir, "prediction_output.json")

            try:
                with open(output_filepath, 'w') as f:
                    json.dump(classified_drum_events, f, indent=4)
                print(f"\nSuccessfully exported classified events to: {output_filepath}")
            except Exception as e:
                print(f"\nError exporting results to JSON file: {e}")

            print("\n--- First 10 Classified Events ---")
            for event in classified_drum_events[:10]:
                print(f"Time: {event['onset_time_seconds']:.2f}s, Type: {event['drum_type']}")
        else:
            print("\nNo drum events were classified based on the current rules.")
            print("-------------------------------------------------------------")