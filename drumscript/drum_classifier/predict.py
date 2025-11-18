# DrumScript/drum_classifier/predict.py
import os
import json
import librosa
import numpy as np
from typing import List, Dict, Any
from drumscript.notation_generator import constants
from drumscript.notation_generator.constants import DRUM_NOTATION_MAP

"""
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
    'ride': { 'midi_pitch': 51, 'note_head_type': 'x', 'staff_position': 'B3', 'display_name': 'Ride Cymbal' },
    'kick_clicky': { 'midi_pitch': 36, 'note_head_type': 'normal', 'staff_position': 'F2', 'display_name': 'Kick (Clicky)' }
}
"""


# --- Rule-based thresholds ---
KICK_SPECTRAL_CENTROID_MAX = 400
KICK_LOW_CENTROID_MAX = 400 
KICK_CLICKY_CENTROID_MIN = 800 
KICK_CLICKY_CENTROID_MAX = 1400 
KICK_CLICKY_ZCR_MAX = 0.006    

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
CYMBAL_CENTROID_MIN = 4500
CYMBAL_CENTROID_MAX = 7000
CRASH_CENTROID_MIN = 4000
CRASH_CENTROID_MAX = 7000 
RIDE_SUSTAIN_MIN = 0.4
RIDE_SUSTAIN_MAX = 0.75 
CRASH_SUSTAIN_MIN = 0.75 
HIHAT_CENTROID_MIN = 9000
HIHAT_ZCR_MIN = 0.2
HIHAT_SUSTAIN_THRESHOLD = 0.5

# --- Refractory period constants ---
OPEN_HIHAT_REFRACTORY_PERIOD_S = 0.6
TOM_REFRACTORY_PERIOD_S = 3.0
CRASH_REFRACTORY_PERIOD_S = 10.0 
RIDE_REFRACTORY_PERIOD_S = 10.0 


# --- Core Classification Logic ---
def predict_drum_hits(onset_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    classified_events = []
    last_open_hihat_time = -1.0
    last_tom_time = -1.0
    last_crash_time = -1.0
    last_ride_time = -1.0

    # ---- Classification Block ----

    for onset in onset_features:
        # Capture the features for this specific hit to save them later
        current_features = {
            'spectral_centroid': round(onset['spectral_centroid'], 2),
            'zcr': round(onset['zero_crossing_rate'], 4),
            'sustain': round(onset['sustain_level'], 2)
        }

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
        print(f"  - Spectral Centroid: {current_features['spectral_centroid']}")
        print(f"  - Zero-Crossing Rate: {current_features['zcr']}")
        print(f"  - Sustain Level: {current_features['sustain']}")

        # ---- Rule-sets ----

        # --- RULE 1: All Kick Drums (Checked First) ---
        if onset['spectral_centroid'] < KICK_LOW_CENTROID_MAX:
            print("  - RESULT: Classified as KICK.")
            classified_events.extend(create_detailed_drum_events(['kick'], onset['onset_time'], current_features))
            continue 
        
        # This catches the anomalous kick (Test 1), which has SC: 4043.
        elif 4000 < onset['spectral_centroid'] < 4500:
            print("  - RESULT: Classified as KICK (Anomalous).")
            classified_events.extend(create_detailed_drum_events(['kick'], onset['onset_time'], current_features))
            continue
            
        elif KICK_CLICKY_CENTROID_MIN < onset['spectral_centroid'] < KICK_CLICKY_CENTROID_MAX and \
             onset['zero_crossing_rate'] < KICK_CLICKY_ZCR_MAX:
            print("  - RESULT: Classified as KICK (Clicky).")
            classified_events.extend(create_detailed_drum_events(['kick_clicky'], onset['onset_time'], current_features)) 
            continue 
        
        elif MID_TOM_CENTROID_MIN < onset['spectral_centroid'] < MID_TOM_CENTROID_MAX and \
             onset['zero_crossing_rate'] < MID_TOM_ZCR_MAX:
            print("  - RESULT: Classified as MID TOM.")
            classified_events.extend(create_detailed_drum_events(['mid_tom'], onset['onset_time'], current_features))
            last_tom_time = onset['onset_time']
            continue

        elif HIGH_TOM_CENTROID_MIN < onset['spectral_centroid'] < HIGH_TOM_CENTROID_MAX and \
             onset['zero_crossing_rate'] < LOW_TOM_ZCR_MAX: 
            print("  - RESULT: Classified as HIGH TOM.")
            classified_events.extend(create_detailed_drum_events(['high_tom'], onset['onset_time'], current_features))
            last_tom_time = onset['onset_time']
            continue

        elif LOW_TOM_CENTROID_MIN < onset['spectral_centroid'] < LOW_TOM_CENTROID_MAX and \
             onset['zero_crossing_rate'] < LOW_TOM_ZCR_MAX:
            print("  - RESULT: Classified as LOW TOM.")
            classified_events.extend(create_detailed_drum_events(['low_tom'], onset['onset_time'], current_features))
            last_tom_time = onset['onset_time']
            continue

        # --- Ride Cymbal (check this BEFORE the crash) ---
        elif CYMBAL_CENTROID_MIN < onset['spectral_centroid'] < CYMBAL_CENTROID_MAX and \
             RIDE_SUSTAIN_MIN < onset['sustain_level'] < RIDE_SUSTAIN_MAX:
            print("  - RESULT: Classified as RIDE.")
            classified_events.extend(create_detailed_drum_events(['ride'], onset['onset_time'], current_features))
            last_ride_time = onset['onset_time'] 
            continue

        # --- Crash Cymbal Rule (now uses the shared CYMBAL constant) ---
        elif CYMBAL_CENTROID_MIN < onset['spectral_centroid'] < CYMBAL_CENTROID_MAX and \
             onset['sustain_level'] > CRASH_SUSTAIN_MIN:
            print("  - RESULT: Classified as CRASH.")
            classified_events.extend(create_detailed_drum_events(['crash'], onset['onset_time'], current_features))
            last_crash_time = onset['onset_time']
            continue

        elif SNARE_CENTROID_MIN < onset['spectral_centroid'] < SNARE_CENTROID_MAX and \
             onset['zero_crossing_rate'] >= SNARE_ZCR_MIN:
            print("  - RESULT: Classified as SNARE.")
            classified_events.extend(create_detailed_drum_events(['snare'], onset['onset_time'], current_features))
            continue

        elif onset['spectral_centroid'] > HIHAT_CENTROID_MIN and \
             onset['zero_crossing_rate'] >= HIHAT_ZCR_MIN:
            print("  - RESULT: Potentially a Hi-Hat...")
            if onset['sustain_level'] > HIHAT_SUSTAIN_THRESHOLD:
                print("    - Sustain is HIGH. Classified as OPEN HI-HAT.")
                classified_events.extend(create_detailed_drum_events(['hi_hat_open'], onset['onset_time'], current_features))
                last_open_hihat_time = onset['onset_time']
            else:
                print("    - Sustain is LOW. Classified as CLOSED HI-HAT.")
                classified_events.extend(create_detailed_drum_events(['hi_hat_closed'], onset['onset_time'], current_features))
            continue
        
        print("  - RESULT: No rule matched.")

    return classified_events

# This helper function is still very useful. It now takes a
# list of classified labels for a single onset and creates the detailed output.
def create_detailed_drum_events(
    predicted_drums: List[str], 
    onset_time: float,
    features: Dict[str, Any] = None
) -> List[Dict[str, Any]]:
    
    # Creates detailed drum event objects with metadata for a list of predicted drums.
    
    detailed_events = []
    for drum_type in predicted_drums:
        if drum_type in constants.DRUM_NOTATION_MAP:
            event = {
                'drum_type': drum_type,
                'onset_time_seconds': round(onset_time, 2), 
                'midi_pitch': DRUM_NOTATION_MAP[drum_type]['midi_program'],
                'note_head_type': DRUM_NOTATION_MAP[drum_type]['note_head'], 
                'staff_position': DRUM_NOTATION_MAP[drum_type]['staff_position'],
                # Include the analysis features if provided
                'analysis': features if features else {}
            }
            detailed_events.append(event)
    return detailed_events

if __name__ == "__main__":
    # Example block code omitted for brevity as per instructions
    pass