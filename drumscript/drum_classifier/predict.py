# DrumScript/drum_classifier/predict.py
import numpy as np
from typing import List, Dict, Any
from drumscript.notation_generator import constants
from drumscript.notation_generator.constants import DRUM_NOTATION_MAP

def predict_drum_hits(onset_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    classified_events = []
    
    # Track last hits to prevent machine-gunning
    last_hits = {k: -1.0 for k in constants.REFRACTORY}

    for onset in onset_features:
        # 1. Parse & Cast Features
        sc = float(round(onset['spectral_centroid'], 2))
        zcr = float(round(onset['zero_crossing_rate'], 4))
        sus = float(round(onset['sustain_level'], 2))
        time = onset['onset_time']
        
        analysis = {'sc': sc, 'zcr': zcr, 'sus': sus}
        
        # --- CLASSIFICATION LOGIC (Zone-Based) ---
        
        # A. LOW ZONE (Kicks & Floor Toms)
        if sc < constants.LOW_ZONE_MAX:
            # Kicks are generally cleaner (lower ZCR) than Toms
            if zcr < constants.NOISE_THRESHOLD_LOW:
                if time - last_hits['kick'] > constants.REFRACTORY['kick']:
                    classified_events.extend(create_event('kick', time, analysis))
                    last_hits['kick'] = time
            else:
                # Noisy low end -> "Clicky" Kick for metal
                if time - last_hits['kick'] > constants.REFRACTORY['kick']:
                    classified_events.extend(create_event('kick_clicky', time, analysis))
                    last_hits['kick'] = time

        # B. MID ZONE (Snares & Rack Toms)
        elif constants.MID_ZONE_MIN <= sc < constants.MID_ZONE_MAX:
            # High Noise = Snare (wires)
            if zcr >= constants.NOISE_THRESHOLD_MID:
                if time - last_hits['snare'] > constants.REFRACTORY['snare']:
                    classified_events.extend(create_event('snare', time, analysis))
                    last_hits['snare'] = time
            # Low Noise = Tom (tone)
            else:
                if time - last_hits['tom'] > constants.REFRACTORY['tom']:
                    classified_events.extend(create_event('high_tom', time, analysis))
                    last_hits['tom'] = time

        # C. HIGH ZONE (Cymbals & Hi-Hats)
        elif sc >= constants.HIGH_ZONE_MIN:
            # 1. Short Sustain = Closed Hi-Hat (Tight sound)
            if sus <= constants.CLOSED_HAT_MAX_SUSTAIN:
                if time - last_hits['hi_hat'] > constants.REFRACTORY['hi_hat']:
                    classified_events.extend(create_event('hi_hat_closed', time, analysis))
                    last_hits['hi_hat'] = time
            
            # 2. Long Sustain = Crash / Ride / Open Hat
            else:
                # Very long? Crash.
                if sus > constants.CRASH_MIN_SUSTAIN:
                    if time - last_hits['crash'] > constants.REFRACTORY['crash']:
                        classified_events.extend(create_event('crash', time, analysis))
                        last_hits['crash'] = time
                # Medium length? Open Hi-Hat.
                else:
                    if time - last_hits['hi_hat'] > constants.REFRACTORY['hi_hat']:
                        classified_events.extend(create_event('hi_hat_open', time, analysis))
                        last_hits['hi_hat'] = time
        
        else:
            # Fallback (should rarely happen with overlapping zones)
            pass

    return classified_events

def create_event(drum_name: str, time: float, analysis: Dict) -> List[Dict[str, Any]]:
    """Helper to format the event object using constants."""
    if drum_name not in constants.DRUM_NOTATION_MAP:
        return []
        
    meta = constants.DRUM_NOTATION_MAP[drum_name]
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