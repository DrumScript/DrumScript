# DrumScript/drum_classifier/classify.py
# NOTE: This script was renamed from previous predictive model used so some references to 'predict' might still appear
import numpy as np
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
    Classifies drum hits using Multi-Band Energy detection to support polyphony.
    """
    classified_events = []
    
    for onset_time in onsets:
        # 1. Extract Window (100ms)
        start_sample = int(onset_time * sr)
        end_sample = int((onset_time + 0.10) * sr)
        
        if end_sample > len(audio_data): end_sample = len(audio_data)
        if start_sample >= end_sample: continue
            
        y_window = audio_data[start_sample:end_sample]
        
        # 2. Calculate Band Energies
        e_low = get_band_energy(y_window, sr, constants.BAND_LOW)
        e_mid = get_band_energy(y_window, sr, constants.BAND_MID)
        e_high = get_band_energy(y_window, sr, constants.BAND_HIGH)
        
        total_energy = e_low + e_mid + e_high + 1e-8
        p_low = e_low / total_energy
        p_mid = e_mid / total_energy
        p_high = e_high / total_energy
        
        # 3. Calculate Secondary Features
        zcr = np.mean(librosa.feature.zero_crossing_rate(y=y_window))
        
        # Sustain (Decay Ratio)
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

        # --- POLYPHONIC LOGIC ---

        # Check LOW (Kick)
        if p_low > constants.THRESH_LOW_ENERGY:
            if zcr < 0.1: # Kicks are clean
                detected_types.append('kick')

        # Check HIGH (Cymbals/Hats) - Independent Check!
        if p_high > constants.THRESH_HIGH_ENERGY:
            if decay_ratio < constants.CLOSED_HAT_MAX_DECAY:
                detected_types.append('hi_hat_closed')
            elif decay_ratio > constants.CRASH_MIN_DECAY:
                detected_types.append('crash')
            else:
                detected_types.append('hi_hat_open')

        # Check MID (Snare/Toms)
        # Only if not overwhelmed by High energy
        if p_mid > constants.THRESH_MID_ENERGY:
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