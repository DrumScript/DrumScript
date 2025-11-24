# DrumScript/drum_classifier/classify.py

import numpy as np
from typing import List, Dict, Any
from drumscript.notation_generator import constants
from drumscript.notation_generator.constants import DRUM_NOTATION_MAP

# --- ACOUSTIC ZONES (Based on Standard Drum EQ Ranges) ---
# Ref: IDMT-SMT-Drums / Gear4Music Frequency Charts

# 1. LOW ZONE (0 - 800 Hz)
# Captures the fundamental "Thump" of Kicks (60-100Hz) and Floor Toms.
# We extend to 800Hz to capture the "knock" or attack of modern/metal kicks.
LOW_ZONE_MAX = 800 

# 2. MID ZONE (800 - 5000 Hz)
# Captures the "Body" and "Crack" of Snares (fundamental ~200Hz, snap ~3-5kHz)
# and the attack of Rack Toms.
MID_ZONE_MIN = 800
MID_ZONE_MAX = 5000

# 3. HIGH ZONE (> 5000 Hz)
# Captures the "Brightness" (Cymbals), "Sizzle" (Hats), and "Air".
HIGH_ZONE_MIN = 5000

# --- THRESHOLDS FOR DIFFERENTIATION ---

# NOISE (Zero-Crossing Rate): Distinguishes "Tone" (Toms) from "Noise" (Snare/Cymbals)
NOISE_THRESHOLD_LOW = 0.02  # Kicks are very clean
NOISE_THRESHOLD_MID = 0.05  # Snares are noisy
NOISE_THRESHOLD_HIGH = 0.08 # Cymbals are very noisy

# SUSTAIN (Seconds): Distinguishes "Short" (Hats/Kicks) from "Long" (Crashes/Rides)
# Closed Hats are VERY short (< 0.2s). Open Hats/Cymbals are long.
CLOSED_HAT_MAX_SUSTAIN = 0.25 
CRASH_MIN_SUSTAIN = 0.5

# Refractory Periods (Min seconds between hits of same type)
REFRACTORY = {
    'kick': 0.1, 'snare': 0.1, 'hi_hat': 0.05, 'crash': 0.2, 'tom': 0.12
}

def classify_drum_hits(onset_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    classified_events = []
    
    # Track last hits to prevent machine-gunning
    last_hits = {k: -1.0 for k in REFRACTORY}

    for onset in onset_features:
        # 1. Parse & Cast Features (Fixes JSON float32 error)
        sc = float(round(onset['spectral_centroid'], 2))
        zcr = float(round(onset['zero_crossing_rate'], 4))
        sus = float(round(onset['sustain_level'], 2))
        time = onset['onset_time']
        
        analysis = {'sc': sc, 'zcr': zcr, 'sus': sus}
        
        # --- CLASSIFICATION LOGIC ---
        
        # A. LOW ZONE (Kicks & Floor Toms)
        if sc < LOW_ZONE_MAX:
            # Kicks are generally cleaner (lower ZCR) than Toms
            if zcr < NOISE_THRESHOLD_LOW:
                if time - last_hits['kick'] > REFRACTORY['kick']:
                    classified_events.extend(create_event('kick', time, analysis))
                    last_hits['kick'] = time
            else:
                # Noisy low end? Could be a loose Kick or Low Tom. 
                # Defaulting to Kick Clicky for metal contexts.
                if time - last_hits['kick'] > REFRACTORY['kick']:
                    classified_events.extend(create_event('kick_clicky', time, analysis))
                    last_hits['kick'] = time

        # B. MID ZONE (Snares & Rack Toms)
        elif MID_ZONE_MIN <= sc < MID_ZONE_MAX:
            # High Noise = Snare (wires)
            if zcr >= NOISE_THRESHOLD_MID:
                if time - last_hits['snare'] > REFRACTORY['snare']:
                    classified_events.extend(create_event('snare', time, analysis))
                    last_hits['snare'] = time
            # Low Noise = Tom (tone)
            else:
                if time - last_hits['tom'] > REFRACTORY['tom']:
                    classified_events.extend(create_event('high_tom', time, analysis))
                    last_hits['tom'] = time

        # C. HIGH ZONE (Cymbals & Hi-Hats)
        elif sc >= HIGH_ZONE_MIN:
            # 1. Short Sustain = Closed Hi-Hat (Tight sound)
            if sus <= CLOSED_HAT_MAX_SUSTAIN:
                if time - last_hits['hi_hat'] > REFRACTORY['hi_hat']:
                    classified_events.extend(create_event('hi_hat_closed', time, analysis))
                    last_hits['hi_hat'] = time
            
            # 2. Long Sustain = Crash / Ride / Open Hat
            else:
                # Very long? Crash.
                if sus > CRASH_MIN_SUSTAIN:
                    if time - last_hits['crash'] > REFRACTORY['crash']:
                        classified_events.extend(create_event('crash', time, analysis))
                        last_hits['crash'] = time
                # Medium length? Open Hi-Hat.
                else:
                    if time - last_hits['hi_hat'] > REFRACTORY['hi_hat']:
                        classified_events.extend(create_event('hi_hat_open', time, analysis))
                        last_hits['hi_hat'] = time
        
    return classified_events

def create_event(drum_name: str, time: float, analysis: Dict) -> List[Dict[str, Any]]:
    """Helper to format the event object."""
    if drum_name not in DRUM_NOTATION_MAP:
        return []
        
    meta = DRUM_NOTATION_MAP[drum_name]
    return [{
        'drum_type': drum_name,
        'onset_time_seconds': round(time, 2),
        'midi_pitch': meta['midi_program'],
        'note_head_type': meta['note_head'],
        'staff_position': meta['staff_position'],
        'analysis': analysis
    }]