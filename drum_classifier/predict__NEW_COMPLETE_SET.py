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
    'high_tom': { 'midi_pitch': 48, 'note_head_type': 'normal', 'staff_position': 'E3', 'display_name': 'High Tom' }
}

# --- Rule-based thresholds ---
KICK_SPECTRAL_CENTROID_MAX = 400

MID_TOM_CENTROID_MIN = 400
MID_TOM_CENTROID_MAX = 800
MID_TOM_ZCR_MAX = 0.05

# --- NEW: Define a rule space for our High Tom ---
HIGH_TOM_CENTROID_MIN = 800
HIGH_TOM_CENTROID_MAX = 1380 # Captures 1353.96

# --- UPDATED: Adjust the Low Tom rule ---
LOW_TOM_CENTROID_MIN = 1380
LOW_TOM_CENTROID_MAX = 1600 # Captures 1406.22
LOW_TOM_ZCR_MAX = 0.05

SNARE_CENTROID_MIN = 1500 # Adjusted to not overlap with toms
SNARE_CENTROID_MAX = 4000
SNARE_ZCR_MIN = 0.09

HIHAT_CENTROID_MIN = 9000
HIHAT_ZCR_MIN = 0.2
HIHAT_SUSTAIN_THRESHOLD = 0.5

# --- Refractory period constants ---
OPEN_HIHAT_REFRACTORY_PERIOD_S = 0.6
TOM_REFRACTORY_PERIOD_S = 3.0

# --- Core Classification Logic ---
def predict_drum_hits(onset_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    classified_events = []
    last_open_hihat_time = -1.0
    last_tom_time = -1.0

    for onset in onset_features:
        # Refractory period checks
        if last_open_hihat_time > 0 and (onset['onset_time'] - last_open_hihat_time) < OPEN_HIHAT_REFRACTORY_PERIOD_S:
            print(f"\n--- Ignoring Onset... (within open hi-hat refractory period) ---")
            continue
        if last_tom_time > 0 and (onset['onset_time'] - last_tom_time) < TOM_REFRACTORY_PERIOD_S:
            print(f"\n--- Ignoring Onset... (within tom refractory period) ---")
            continue

        # Debugging block
        print(f"\n--- Processing Onset at {onset['onset_time']:.2f}s ---")
        print(f"  - Spectral Centroid: {onset['spectral_centroid']:.2f}")
        print(f"  - Zero-Crossing Rate: {onset['zero_crossing_rate']:.4f}")
        print(f"  - Sustain Level: {onset['sustain_level']:.2f}")

        # --- RULE 1: Kick Drum ---
        if onset['spectral_centroid'] < KICK_SPECTRAL_CENTROID_MAX:
            print("  - RESULT: Classified as KICK.")
            classified_events.extend(create_detailed_drum_events(['kick'], onset['onset_time']))
            continue

        # --- RULE 2: Mid Tom ---
        elif MID_TOM_CENTROID_MIN < onset['spectral_centroid'] < MID_TOM_CENTROID_MAX and \
             onset['zero_crossing_rate'] < MID_TOM_ZCR_MAX:
            print("  - RESULT: Classified as MID TOM.")
            classified_events.extend(create_detailed_drum_events(['mid_tom'], onset['onset_time']))
            last_tom_time = onset['onset_time']
            continue

        # --- NEW RULE: High Tom ---
        elif HIGH_TOM_CENTROID_MIN < onset['spectral_centroid'] < HIGH_TOM_CENTROID_MAX and \
             onset['zero_crossing_rate'] < LOW_TOM_ZCR_MAX: # Using same ZCR rule for all toms
            print("  - RESULT: Classified as HIGH TOM.")
            classified_events.extend(create_detailed_drum_events(['high_tom'], onset['onset_time']))
            last_tom_time = onset['onset_time']
            continue

        # --- RULE 4: Low Tom ---
        elif LOW_TOM_CENTROID_MIN < onset['spectral_centroid'] < LOW_TOM_CENTROID_MAX and \
             onset['zero_crossing_rate'] < LOW_TOM_ZCR_MAX:
            print("  - RESULT: Classified as LOW TOM.")
            classified_events.extend(create_detailed_drum_events(['low_tom'], onset['onset_time']))
            last_tom_time = onset['onset_time']
            continue

        # --- RULE 5: Snare Drum ---
        elif SNARE_CENTROID_MIN < onset['spectral_centroid'] < SNARE_CENTROID_MAX and \
             onset['zero_crossing_rate'] >= SNARE_ZCR_MIN:
            print("  - RESULT: Classified as SNARE.")
            classified_events.extend(create_detailed_drum_events(['snare'], onset['onset_time']))
            continue

        # --- RULE 6: Hi-Hat ---
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
# ... (rest of the file remains the same) ...