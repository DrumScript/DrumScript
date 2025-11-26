# DrumScript/drum_classifier/classify.py
import numpy as np
import librosa
from typing import List, Dict, Any
from drumscript.notation_generator import constants
from drumscript.notation_generator.constants import DRUM_NOTATION_MAP

def get_band_energy(y, sr, band):
    """Calculates energy within a specific frequency band."""
    spec = np.abs(librosa.stft(y, n_fft=256))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=256)
    bin_start = np.argmax(freqs >= band[0])
    bin_end = np.argmax(freqs >= band[1])
    if bin_end == 0: bin_end = len(freqs)
    return np.sum(spec[bin_start:bin_end, :])

def classify_drum_hits(audio_data, sr, onsets) -> List[Dict[str, Any]]:
    classified_events = []
    
    for onset_time in onsets:
        # 1. Extract Window
        start_sample = int(onset_time * sr)
        end_sample = int((onset_time + 0.10) * sr)
        if end_sample > len(audio_data): end_sample = len(audio_data)
        if start_sample >= end_sample: continue
        y_window = audio_data[start_sample:end_sample]
        if len(y_window) == 0: continue 

        # 2. Calculate Specific Band Energies
        # We sum energy across the whole spectrum to normalize
        total_energy = np.sum(np.abs(librosa.stft(y_window, n_fft=256))) + 1e-8
        
        # Helper to check ratio
        def check_band(band, threshold):
            e = get_band_energy(y_window, sr, band)
            return (e / total_energy) > threshold

        # 3. Secondary Features
        zcr = np.mean(librosa.feature.zero_crossing_rate(y=y_window))
        rms = librosa.feature.rms(y=y_window)[0]
        split = len(rms) // 2
        if np.mean(rms[:split]) < 1e-4: decay_ratio = 0.0
        else: decay_ratio = np.mean(rms[split:]) / np.mean(rms[:split])

        analysis = {'zcr': float(round(zcr, 3)), 'decay': float(round(decay_ratio, 2))}
        detected_types = []

        # --- CLASSIFICATION LOGIC (Range-Based) ---

        # 1. KICK vs LOW TOM
        if check_band(constants.KICK_RANGE, constants.THRESH_KICK):
            # Differentiate by ZCR or just prioritize Kick
            if zcr < 0.1: 
                detected_types.append('kick')
        elif check_band(constants.LOW_TOM_RANGE, constants.THRESH_KICK):
             detected_types.append('low_tom')

        # 2. SNARE vs MID TOM
        if check_band(constants.SNARE_RANGE, constants.THRESH_SNARE):
            if zcr > constants.NOISE_THRESH_SNARE:
                detected_types.append('snare')
            else:
                detected_types.append('mid_tom') # Tonal in snare range = Tom

        # 3. HATS vs CYMBALS
        # Checking fundamental ranges for body/tone
        
        # Closed Hat Body
        if check_band(constants.CLOSED_HAT_RANGE, constants.THRESH_HAT):
             detected_types.append('hi_hat_closed')

        # Open Hat / Ride Body
        if check_band(constants.OPEN_HAT_RANGE, constants.THRESH_HAT):
             if decay_ratio > 0.4: # Long sustain? Maybe Ride
                 detected_types.append('hi_hat_open') # Or Ride, hard to say without high freq check
             else:
                 detected_types.append('hi_hat_open')

        # Crash / Ride (High Freq + Long Sustain)
        if check_band(constants.CRASH_RANGE, constants.THRESH_CYMBAL):
            if decay_ratio > constants.CRASH_MIN_DECAY:
                detected_types.append('crash')
        
        # --- Legacy "High Band" Check for Air/Sizzle ---
        # (Optional: Add back if needed to catch high-end only sounds)

        # Create Events
        for dtype in set(detected_types): # set() prevents duplicates
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