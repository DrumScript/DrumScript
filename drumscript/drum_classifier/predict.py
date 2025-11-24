# DrumScript/drum_classifier/predict.py
import numpy as np
from typing import List, Dict, Any
from drumscript.notation_generator import constants
from drumscript.notation_generator.constants import DRUM_NOTATION_MAP

# --- SIMPLIFIED FREQUENCY ZONES (Based on Standard Acoustic Ranges) ---

# 1. LOW ZONE (0 - 600 Hz): Kicks and Floor Toms
# Kicks fundamental is ~60Hz, but attack pushes centroid up. 
# 600Hz is a safe upper limit for most kicks.
LOW_ZONE_MAX = 600 

# 2. MID ZONE (600 - 5000 Hz): Snares and Rack Toms
# Snare fundamental is ~200Hz, but wires/snap push centroid to 2-4kHz.
MID_ZONE_MIN = 600
MID_ZONE_MAX = 5000

# 3. HIGH ZONE (> 5000 Hz): Cymbals and Hi-Hats
# Covers "Brightness" (4-8kHz) and "Air" (>10kHz).
HIGH_ZONE_MIN = 5000

# --- Secondary Features for Differentiation ---
# Zero-Crossing Rate (ZCR): "Noisiness". High ZCR = Snare/Cymbal. Low ZCR = Kick/Tom.
NOISE_THRESHOLD = 0.05 

# Sustain: "Length". Short = Hi-Hat/Kick. Long = Crash/Ride.
SUSTAIN_THRESHOLD = 0.5 


def predict_drum_hits(onset_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    classified_events = []
    
    # Track last hits for refractory logic (prevents machine-gun triggering)
    last_hit_times = {
        'kick': -1.0, 'snare': -1.0, 'hi_hat': -1.0, 'crash': -1.0, 'tom': -1.0
    }
    
    # Refractory periods (seconds)
    REFRACTORY = {
        'kick': 0.1, 'snare': 0.1, 'hi_hat': 0.05, 'crash': 0.2, 'tom': 0.15
    }

    for onset in onset_features:
        # 1. Parse Features (Cast to standard float for JSON safety)
        sc = float(round(onset['spectral_centroid'], 2))
        zcr = float(round(onset['zero_crossing_rate'], 4))
        sus = float(round(onset['sustain_level'], 2))
        time = onset['onset_time']
        
        # 2. Capture Analysis Data
        analysis = {'spectral_centroid': sc, 'zcr': zcr, 'sustain': sus}
        
        # --- CLASSIFICATION LOGIC ---
        
        # A. LOW ZONE (Kicks & Low Toms)
        if sc < LOW_ZONE_MAX:
            # If it's very clean (Low ZCR), it's a Kick
            if zcr < NOISE_THRESHOLD:
                if time - last_hit_times['kick'] > REFRACTORY['kick']:
                    classified_events.extend(create_event('kick', time, analysis))
                    last_hit_times['kick'] = time
            else:
                # A bit noisy in the low end? Might be a loose Kick or Floor Tom.
                # For V1 simplification, we default to Kick.
                if time - last_hit_times['kick'] > REFRACTORY['kick']:
                    classified_events.extend(create_event('kick', time, analysis))
                    last_hit_times['kick'] = time

        # B. MID ZONE (Snares & Rack Toms)
        elif MID_ZONE_MIN <= sc < MID_ZONE_MAX:
            # High Noise (ZCR) = Snare (snares buzzing)
            if zcr >= NOISE_THRESHOLD:
                if time - last_hit_times['snare'] > REFRACTORY['snare']:
                    classified_events.extend(create_event('snare', time, analysis))
                    last_hit_times['snare'] = time
            # Low Noise = Rack Tom (resonant tube sound)
            else:
                if time - last_hit_times['tom'] > REFRACTORY['tom']:
                    classified_events.extend(create_event('high_tom', time, analysis))
                    last_hit_times['tom'] = time

        # C. HIGH ZONE (Cymbals & Hi-Hats)
        elif sc >= HIGH_ZONE_MIN:
            # Distinguish by Sustain (Length)
            if sus > SUSTAIN_THRESHOLD:
                # Long Sustain = Crash or Ride
                # (Simple logic: Every long bright sound is a Crash for now)
                if time - last_hit_times['crash'] > REFRACTORY['crash']:
                    classified_events.extend(create_event('crash', time, analysis))
                    last_hit_times['crash'] = time
            else:
                # Short Sustain = Hi-Hat
                if time - last_hit_times['hi_hat'] > REFRACTORY['hi_hat']:
                    classified_events.extend(create_event('hi_hat_closed', time, analysis))
                    last_hit_times['hi_hat'] = time
        
        else:
            print(f"--- Unclassified: SC={sc}, ZCR={zcr} ---")

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

if __name__ == "__main__":
    pass