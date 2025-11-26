# DrumScript/drum_classifier/classify.py
# NOTE: This script was renamed from previous predictive model used so some references to 'predict' might still appear
import numpy as np
import librosa
from typing import List, Dict, Any
from drumscript.notation_generator import constants
from drumscript.notation_generator.constants import DRUM_NOTATION_MAP


def get_band_energy(y, sr, band):
    """Calculates energy within a specific frequency band."""
    spec = np.abs(librosa.stft(y, n_fft=512))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=512)
    bin_start = np.argmax(freqs >= band[0])
    bin_end = np.argmax(freqs >= band[1])
    if bin_end == 0: bin_end = len(freqs)
    return np.sum(spec[bin_start:bin_end, :])

def classify_drum_hits(audio_data, sr, onsets) -> List[Dict[str, Any]]:
    """
    Classifies drum hits using Multi-Band Energy detection.
    Optimized for Polyphony (Kick + Hat) and false-positive reduction.
    """
    classified_events = []
    
    for onset_time in onsets:
        # 1. Extract Window (100ms)
        start_sample = int(onset_time * sr)
        end_sample = int((onset_time + 0.10) * sr)
        
        if end_sample > len(audio_data): end_sample = len(audio_data)
        if start_sample >= end_sample: continue
            
        y_window = audio_data[start_sample:end_sample]
        if len(y_window) == 0: continue 

        # 2. Calculate Band Energies
        e_low = get_band_energy(y_window, sr, constants.BAND_LOW)
        e_mid = get_band_energy(y_window, sr, constants.BAND_MID)
        e_high = get_band_energy(y_window, sr, constants.BAND_HIGH)
        
        total_energy = e_low + e_mid + e_high + 1e-8
        
        # Ratios (0.0 - 1.0)
        p_low = e_low / total_energy
        p_mid = e_mid / total_energy
        p_high = e_high / total_energy
        
        # 3. Secondary Features
        zcr = np.mean(librosa.feature.zero_crossing_rate(y=y_window))
        rms = librosa.feature.rms(y=y_window)[0]
        split = len(rms) // 2
        if np.mean(rms[:split]) < 1e-4:
            decay_ratio = 0.0
        else:
            decay_ratio = np.mean(rms[split:]) / np.mean(rms[:split])

        analysis = {
            'p_low': float(round(p_low, 2)), 
            'p_mid': float(round(p_mid, 2)),
            'p_high': float(round(p_high, 2)),
            'decay': float(round(decay_ratio, 2)),
            'zcr': float(round(zcr, 3))
        }
        
        detected_types = []

        # --- INTELLIGENT CLASSIFICATION LOGIC ---

        # 1. CHECK KICK (Base)
        is_kick = False
        if p_low > constants.THRESH_LOW_ENERGY:
            # Kick confirmed if low energy is dominant
            if zcr < 0.1: 
                detected_types.append('kick')
                is_kick = True

        # 2. CHECK HIGH (Hats/Cymbals)
        # If we found a Kick, the High energy will be relatively smaller (drowned out).
        # So we use a LOWER threshold for high-end if a Kick is present.
        
        high_threshold = constants.THRESH_HIGH_ENERGY # Default (0.3)
        if is_kick:
            high_threshold = 0.15 # Lower threshold to catch Hi-Hat *with* Kick

        if p_high > high_threshold:
            if decay_ratio < constants.CLOSED_HAT_MAX_DECAY:
                detected_types.append('hi_hat_closed')
            elif decay_ratio > constants.CRASH_MIN_DECAY:
                detected_types.append('crash')
            else:
                detected_types.append('hi_hat_open')

        # 3. CHECK MID (Snare/Toms) - The "Too Many Notes" Fix
        # Only detect Mid drums if they are the DOMINANT energy or extremely strong.
        # This prevents Kicks (which have some mid attack) from triggering a Tom/Snare.
        
        if p_mid > constants.THRESH_MID_ENERGY:
            # STRICT RULE: Mid must be the strongest band, OR > 50% energy
            if p_mid > p_low and p_mid > p_high:
                if zcr > constants.NOISE_THRESH_SNARE:
                    detected_types.append('snare')
                else:
                    # Tonal mid = Tom
                    if p_low > 0.2:
                        detected_types.append('low_tom')
                    else:
                        detected_types.append('high_tom')

        # Create Events
        for dtype in detected_types:
            if dtype in constants.DRUM_NOTATION_MAP:
                meta = constants.DRUM_NOTATION_MAP[dtype]
                classified_events.append({
                    'drum_type': dtype,
                    'onset_time_seconds': round(onset_time, 2),
                    'midi_pitch': meta['midi_program'],
                    'note_head_type': meta['note_head'],
                    'staff_position': meta['staff_position'],
                    'analysis': analysis
                })
            
    return classified_events