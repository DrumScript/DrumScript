# DrumScript/drum_classifier/classify.py
# Requires path to audio file in cli command, ie:
# `python3 -m drumscript.drum_classifier.classify path_to_audio_file
# ------------------------------------------------------------------------------------------------------------
"""
This script determines the classification rules by which the parameters in py are applied to audio_file_path.
It fuses high-resolution acoustic DNA extraction with simultaneous HFER/LFER physics rules.
"""

from typing import Any, Dict, List
import numpy as np
import scipy.signal
import librosa
from datetime import datetime
from drumscript.notation_generator import constants
from drumscript.notation_generator.constants import (
    SAMPLE_RATE, ONSET_SLICE_DURATION_MS, N_FFT, HOP_LENGTH, DRUM_NOTATION_MAP,
    KICK_FREQ_MIN, KICK_FREQ_MAX, KICK_LFER_MIN, 
    SNARE_FREQ_MIN, SNARE_FREQ_MAX, SNARE_HFER_MIN, 
    TOM_FREQ_LOW_MAX, TOM_FREQ_MID_MAX, TOM_MIN_DECAY, 
    HAT_CLOSED_MAX_DECAY, HAT_OPEN_MAX_DECAY, 
    IDIOPHONE_MIN_HFER_5K, CYMBAL_CENTROID_THRESHOLD
)

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

# --- EXTRACT_FEATURES ---
# This restores the linear magnitude scale from _classifier.py so the thresholds 
# (like KICK_LFER_MIN and SNARE_HFER_MIN) work flawlessly again.
def extract_features(audio_slice: np.ndarray, sr: int) -> dict:
    """
    Analyses the audio slice and extracts the physical DSP features.
    Wraps numpy outputs in float() to ensure JSON serialization.
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
    features['peak_freq'] = float(frequencies[peak_idx]) # Added float() casting
    
    # 3. Calculate Spectral Centroid (The "Center of Mass" or Brightness)
    centroid = librosa.feature.spectral_centroid(S=stft, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)
    features['centroid'] = float(np.mean(centroid)) # Added float() casting
    
    # 4. Resonance (Decay Time) - IMPORTED SO TOMS AND HATS CAN BE CLASSIFIED
    rms = librosa.feature.rms(y=audio_slice)[0]
    peak_rms_idx = np.argmax(rms)
    threshold = np.max(rms) * 0.1 # -20dB point
    
    decay_frames = 0
    for i in range(peak_rms_idx, len(rms)):
        if rms[i] < threshold:
            break
        decay_frames += 1
    features['decay'] = float(librosa.frames_to_time(decay_frames, sr=sr)) # Added float() casting

    # 5. Calculate Energy Ratios (LFER & HFER)
    total_energy = np.sum(spectrum)
    if total_energy == 0: # Prevent division by zero on silent slices
        features['lfer'] = 0.0
        features['hfer'] = 0.0
        features['hfer_5k'] = 0.0
        return features

    # Low Frequency Energy Ratio (Energy below 150Hz)
    low_idx = np.where(frequencies <= 150.0)[0]
    features['lfer'] = float(np.sum(spectrum[low_idx]) / total_energy) # Added float() casting
    
    # Snare Wire Energy Ratio (Energy > 2000Hz)
    high_idx = np.where(frequencies > 2000.0)[0]
    features['hfer'] = float(np.sum(spectrum[high_idx]) / total_energy) # Added float() casting
    
    # Cymbal/Hat Energy Ratio (Energy > 5000Hz)
    metal_idx = np.where(frequencies > 5000.0)[0]
    features['hfer_5k'] = float(np.sum(spectrum[metal_idx]) / total_energy) # Added float() casting
    
    return features


# --- COMMENTED OUT GET_PHYSICS_PROFILE ---
# REASON: The Welch method calculates Power (amplitude squared), which breaks 
# the LFER/HFER percentage thresholds. STFT magnitude (extract_features) restores accuracy.
# def get_physics_profile(y, sr):
#     """
#     Extracts the 'DNA' of the drum hit: 
#     Pitch, Decay, Brightness, and Energy Ratios.
#     """
#     # 1. Frequency Analysis (High Resolution)
#     freqs, psd = scipy.signal.welch(y, sr, nperseg=4096)
#     peak_idx = np.argmax(psd)
#     peak_freq = freqs[peak_idx]
#     
#     # 2. Spectral Centroid (Brightness - Critical for Cymbals)
#     centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
#     
#     # 3. Energy Distribution Ratios
#     total_energy = np.sum(psd) + 1e-9
#     
#     # Bass Energy (<150Hz) - Kick detection
#     low_energy = np.sum(psd[freqs < 150])
#     lfer = low_energy / total_energy
#     
#     # Wire Energy (>2000Hz) - Snare vs High Tom detection
#     mid_high_energy = np.sum(psd[freqs > 2000])
#     hfer_2k = mid_high_energy / total_energy
#     
#     # Shimmer Energy (>5000Hz) - Skin vs Metal detection
#     high_energy = np.sum(psd[freqs > 5000])
#     hfer_5k = high_energy / total_energy
#     
#     # 4. Resonance (Decay Time)
#     rms = librosa.feature.rms(y=y)[0]
#     peak_rms_idx = np.argmax(rms)
#     threshold = np.max(rms) * 0.1 # -20dB point
#     
#     decay_frames = 0
#     for i in range(peak_rms_idx, len(rms)):
#         if rms[i] < threshold:
#             break
#         decay_frames += 1
#     decay_time = librosa.frames_to_time(decay_frames, sr=sr)
#     
#     return {
#         "peak_freq": peak_freq,
#         "centroid": centroid,
#         "lfer": lfer,
#         "hfer_2k": hfer_2k,
#         "hfer": hfer_2k,      # Mapped to 'hfer' to ensure compatibility with classify_onset
#         "hfer_5k": hfer_5k,
#         "decay": decay_time
#     }


# --- LEGACY CODE - COMMENTED OUT CLASSIFY_MEMBRANOPHONE (March 17 Interim) ---
# def classify_membranophone(p):
#     """
#     Stage 2A: Sorts Skins (Kick, Snare, Toms).
#     Updated to merge Feb 9 explicit logic with simultaneous hit routing.
#     """
#     detected_instruments = []
#     
#     # RULE 1: KICK DRUM (Using exact Feb 9 explicit logic)
#     is_kick_freq = KICK_FREQ_MIN <= p['peak_freq'] <= KICK_FREQ_MAX
#     is_thump = p['lfer'] >= KICK_LFER_MIN
#     not_too_crisp = p['hfer'] < SNARE_HFER_MIN # Excludes fat snares
#     
#     if is_kick_freq and is_thump and not_too_crisp:
#         detected_instruments.append('kick')
#             
#     # RULE 2: SNARE DRUM (Standard + Fat Snare catches)
#     is_snare_freq = (SNARE_FREQ_MIN <= p['peak_freq'] <= SNARE_FREQ_MAX)
#     has_snare_wire = (SNARE_HFER_MIN <= p['hfer'] < 0.85)
#     
#     if has_snare_wire and (is_snare_freq or p['peak_freq'] < SNARE_FREQ_MIN):
#         detected_instruments.append('snare')
#         
#     # RULE 3: TOMS (Integrating exact Feb 9 Purity & Resonance checks)
#     is_pure = p['hfer'] < SNARE_HFER_MIN  # Toms have almost no 'wire' noise
#     is_resonant = p['decay'] >= TOM_MIN_DECAY # Toms ring longer than kicks
#     
#     if is_pure and is_resonant:
#         if p['peak_freq'] <= TOM_FREQ_LOW_MAX:
#             # Prevent duplicate tagging if decay pushed it into Low Tom territory
#             if 'low_tom' not in detected_instruments:
#                 detected_instruments.append('low_tom')
#         elif p['peak_freq'] <= TOM_FREQ_MID_MAX:
#             detected_instruments.append('mid_tom')
#         elif p['peak_freq'] <= 400: # Upper safety bound
#             detected_instruments.append('high_tom')
# 
#     return detected_instruments

def classify_membranophone(p):
    """
    Stage 2A: Sorts Skins (Kick, Snare, Toms).
    Fuses logic from _classifier.py (Kick/Snare) with the Tom logic from v0.1.0.
    """
    detected_instruments = []
    
    # RULE 1: KICK DRUM (logic from _classifier.py)
    # Does not rely on decay, so overlapping cymbals won't turn Kicks into Low Toms!
    if p['lfer'] >= KICK_LFER_MIN and (KICK_FREQ_MIN <= p['peak_freq'] <= KICK_FREQ_MAX):
        detected_instruments.append('kick')
            
    # --- LEGACY CODE - COMMENTED OUT SNARE RULE (Fat Snare catch caused Kick+Hat hallucinations) ---
    # is_snare_freq = (SNARE_FREQ_MIN <= p['peak_freq'] <= SNARE_FREQ_MAX)
    # has_snare_wire = (SNARE_HFER_MIN <= p['hfer'] < 0.85)
    # 
    # if has_snare_wire and (is_snare_freq or p['peak_freq'] < SNARE_FREQ_MIN):
    #     detected_instruments.append('snare')

    # RULE 2: SNARE DRUM (strict logic from _classifier.py to prevent Kick+Hat hallucinations)
    is_snare_freq = (SNARE_FREQ_MIN <= p['peak_freq'] <= SNARE_FREQ_MAX)
    has_snare_wire = (SNARE_HFER_MIN <= p['hfer'] < 0.85)
    
    if has_snare_wire and is_snare_freq:
        detected_instruments.append('snare')
        
    # RULE 3: TOMS (From v0.1.0 - pure tone and longer decay)
    is_pure = p['hfer'] < SNARE_HFER_MIN  # Toms have almost no 'wire' noise
    is_resonant = p['decay'] >= TOM_MIN_DECAY # Toms ring longer than isolated kicks
    
    if is_pure and is_resonant:
        if p['peak_freq'] <= TOM_FREQ_LOW_MAX:
            if 'kick' not in detected_instruments: # Don't label a Kick as a Low Tom
                detected_instruments.append('low_tom')
        elif p['peak_freq'] <= TOM_FREQ_MID_MAX:
            detected_instruments.append('mid_tom')
        elif p['peak_freq'] <= 400: # Upper safety bound
            detected_instruments.append('high_tom')

    return detected_instruments


# --- LEGACY CODE - COMMENTED OUT CLASSIFY_IDIOPHONE (March 17 Interim) ---
# def classify_idiophone(p):
#     """
#     Stage 2B: Sorts Metals (Hats, Cymbals).
#     Updated to return a list of simultaneous hits.
#     """
#     detected_instruments = []
#     decay = p['decay']
#     
#     # RULE 4: METALS (Hats / Cymbals)
#     if p['hfer_5k'] >= IDIOPHONE_MIN_HFER_5K:
#         if decay <= HAT_CLOSED_MAX_DECAY:
#             detected_instruments.append('hi_hat_closed')
#         elif decay <= HAT_OPEN_MAX_DECAY:
#             detected_instruments.append('hi_hat_open')
#         else:
#             if p['centroid'] > 2500:
#                 detected_instruments.append('crash') 
#             else:
#                 detected_instruments.append('ride') 
#                 
#     return detected_instruments

def classify_idiophone(p):
    """
    Stage 2B: Sorts Metals (Hats, Cymbals).
    Uses Feb 9 Decay logic + _classifier.py Centroid thresholds.
    """
    detected_instruments = []
    decay = p['decay']
    
    # RULE 4: METALS (Hats / Cymbals)
    if p['hfer_5k'] >= IDIOPHONE_MIN_HFER_5K:
        if decay <= HAT_CLOSED_MAX_DECAY:
            detected_instruments.append('hi_hat_closed')
        elif decay <= HAT_OPEN_MAX_DECAY:
            detected_instruments.append('hi_hat_open')
        else:
            # Merged logic: use 2500 from _classifier to prevent kick overlaps looking like rides
            if p['centroid'] > 2500:
                detected_instruments.append('crash') 
            else:
                detected_instruments.append('ride') 
                
    return detected_instruments

# --- LEGACY CODE - COMMENTED OUT CLASSIFY_EVENT ---
# def classify_event(audio_segment, sr):
#     """
#     Stage 1: Class Separation (Skin vs Metal)
#     """
#     # physics = get_physics_profile(audio_segment, sr)
#     # 
#     # # Is it Metal? (High energy > 5kHz)
#     # if physics['hfer_5k'] >= IDIOPHONE_MIN_HFER_5K:
#     #     return classify_idiophone(physics)
#     # else:
#     #     return classify_membranophone(physics)

def classify_event(audio_segment, sr):
    """
    Stage 1: Evaluates both Skins and Metals simultaneously.
    Returns a list because multiple drums can hit simultaneously!
    """
    # LEGACY CODE - physics = get_physics_profile(audio_segment, sr)
    physics = extract_features(audio_segment, sr)
    instruments = []
    
    # Check skins
    instruments.extend(classify_membranophone(physics))
    
    # Check metals
    instruments.extend(classify_idiophone(physics))
    
    # Fallback
    if not instruments:
        instruments.append('unknown')
        
    return instruments

# --- LEGACY CODE - COMMENTED OUT CLASSIFY_EVENTS ---
# def classify_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:
#     """
#     Wrapper to route detected onsets through the new Physics-First Classification Engine.
#     Uses the unified dictionary keys: time_sec, instruments, debug_features.
#     """
#     classified_events = []
# 
#     for onset_time in onsets:
#         start_sample = int(onset_time * sr)
#         
#         # --- LEGACY CODE -  TRUNCATING LOGIC ---
#         # end_sample = int((onset_time + 0.2) * sr)
#         # #duration_secs = ONSET_SLICE_DURATION_MS / 1000.0 
#         # #end_sample = start_sample + int(duration_secs * sr)
#         # 
#         # if end_sample > len(audio_data):
#         #     end_sample = len(audio_data)
#         # if start_sample >= end_sample:
#         #     continue
#         #
#         # y_window = audio_data[start_sample:end_sample]
#         # if len(y_window) == 0:
#         #     continue
# 
#         # --- NEW PADDING LOGIC (Prevents SciPy/Librosa STFT Warnings at End of File) ---
#         duration_secs = ONSET_SLICE_DURATION_MS / 1000.0 
#         end_sample = start_sample + int(duration_secs * sr)
# 
#         if end_sample > len(audio_data):
#             slice_data = audio_data[start_sample:]
#             pad_length = end_sample - len(audio_data)
#             y_window = np.pad(slice_data, (0, pad_length), mode='constant')
#         else:
#             y_window = audio_data[start_sample:end_sample]
# 
#         if len(y_window) == 0:
#             continue
# 
#         # 1. Extract the physics DNA
#         physics_profile = get_physics_profile(y_window, sr)
# 
#         # 2. Run the simultaneous rules
#         instruments = classify_event(y_window, sr)
#         
#         # 3. Append with unified compatible keys
#         classified_events.append(
#             {
#                 "time_sec": float(onset_time), 
#                 "instruments": instruments, 
#                 "debug_features": physics_profile 
#             }
#         )
# 
#     return classified_events

def classify_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:
    """
    Wrapper to route detected onsets through the new Physics-First Classification Engine.
    Uses the unified dictionary keys: time_sec, instruments, debug_features.
    """
    classified_events = []

    for onset_time in onsets:
        start_sample = int(onset_time * sr)
        
        # --- NEW PADDING LOGIC (Prevents SciPy/Librosa STFT Warnings at End of File) ---
        duration_secs = ONSET_SLICE_DURATION_MS / 1000.0 
        end_sample = start_sample + int(duration_secs * sr)

        if end_sample > len(audio_data):
            slice_data = audio_data[start_sample:]
            pad_length = end_sample - len(audio_data)
            y_window = np.pad(slice_data, (0, pad_length), mode='constant')
        else:
            y_window = audio_data[start_sample:end_sample]

        if len(y_window) == 0:
            continue

        # 1. Extract the physics DNA
        # LEGACY CODE - physics_profile = get_physics_profile(y_window, sr)
        physics_profile = extract_features(y_window, sr)

        # 2. Run the simultaneous rules
        instruments = classify_event(y_window, sr)
        
        # 3. Append with unified compatible keys
        classified_events.append(
            {
                "time_sec": float(onset_time), 
                "instruments": instruments, 
                "debug_features": physics_profile 
            }
        )

    return classified_events


# print("\n# ------------------------------------------------------------------------------------")
# LEGACY CODE (PRESERVING FOR EASE)
# Leave these uncommented so not to break orchestration and docs
# def analyze_event(y, sr):
#     
#     # Calculates specific acoustic features:
#     # - f0: Fundamental Frequency (Peak Magnitude)
#     #- sc: Spectral Centroid (Brightness)
#     # - width: Spectral Bandwidth
#     # - depth: Decay Ratio (Sustain)
# 
#     #:param y: Audio segment.
#     #:type y: np.ndarray
#     #:param sr: Sampling rate.
#     #:type sr: int
#     #:return: Dictionary of features [f0: (Fundamental Frequency (Peak Magnitude)), sc: Spectral Centroid (Brightness), width: Spectral Bandwidth], depth: Decay Ratio (Sustain)]
#     #:rtype: dict
#     
#     # 1. FFT for Frequency Analysis
#     # High resolution (n_fft=2048) to see low frequencies clearly
#     # n_fft = 2048
#     # spec = np.abs(librosa.stft(y, n_fft=n_fft))
#     # freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
#     # n_fft = N_FFT
#     spec = np.abs(librosa.stft(y, n_fft=N_FFT))
#     freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
# 
#     # Sum magnitudes to find the strongest frequency (Fundamental)
#     sum_spec = np.sum(spec, axis=1)
#     peak_idx = np.argmax(sum_spec)
#     f0 = freqs[peak_idx]
# 
#     # 2. Spectral Features
#     # sc = float(np.mean(librosa.feature.spectral_centroid(S=spec, sr=sr)))
#     # width = float(np.mean(librosa.feature.spectral_bandwidth(S=spec, sr=sr)))
# 
#     sc = float(np.mean(librosa.feature.spectral_centroid(S=spec, sr=SAMPLE_RATE)))
#     width = float(np.mean(librosa.feature.spectral_bandwidth(S=spec, sr=SAMPLE_RATE)))
#     # 3. Depth / Decay (Sustain)
#     rms = librosa.feature.rms(y=y)[0]
#     split = len(rms) // 2
#     if np.mean(rms[:split]) < 1e-5:
#         decay = 0.0
#     else:
#         decay = np.mean(rms[split:]) / np.mean(rms[:split])
# 
#     return {
#         "f0": float(f0),
#         "sc": float(round(sc, 2)),
#         "width": float(round(width, 2)),
#         "depth": float(round(decay, 2)),
#     }
# 
# 
# # Leave these uncommented so not to break orchestration and docs
# def classify_events_legacy (audio_data, sr, onsets) -> List[Dict[str, Any]]:
#     # Classifies hits strictly based on Fundamental Frequency ($f_0$) ranges.
#     # :param audio_data: Full audio array.
#     # :type audio_data: np.ndarray
#     # :param sr: Sampling rate.
#     # :type sr: int
#     # :param onsets: List of onset times.
#     # :type onsets: list
#     # :return: List of classified event dictionaries.
#     # :rtype: List[Dict[str, Any]]
# 
#     classified_events = []
# 
#     for onset_time in onsets:
#         # Extract 150ms window for analysis
#         start_sample = int(onset_time * sr)
#         end_sample = int((onset_time + 0.15) * sr)
# 
#         if end_sample > len(audio_data):
#             end_sample = len(audio_data)
#         if start_sample >= end_sample:
#             continue
# 
#         y_window = audio_data[start_sample:end_sample]
#         if len(y_window) == 0:
#             continue
# 
#         # Analyze
#         features = analyze_event(y_window, sr)
#         f0 = features["f0"]
# 
#         drum_type = None
# 
#         # --- STRICT FREQUENCY RANGE CLASSIFICATION ---
#         # Order matters for overlaps!
# 
#         # 1. Low End
#         if KICK_RANGE[0] <= f0 <= KICK_RANGE[1]:
#             drum_type = "kick"
#         elif LOW_TOM_RANGE[0] <= f0 <= LOW_TOM_RANGE[1]:
#             drum_type = "low_tom"
# 
#         # 2. Mids (Check Tom first to catch narrow band, then Snare)
#         elif MID_TOM_RANGE[0] <= f0 <= MID_TOM_RANGE[1]:
#             drum_type = "mid_tom"
#         elif SNARE_RANGE[0] <= f0 <= SNARE_RANGE[1]:
#             drum_type = "snare"
# 
#         # 3. Highs
#         elif OPEN_HAT_RANGE[0] <= f0 <= OPEN_HAT_RANGE[1]:
#             drum_type = "hi_hat_open"
#         elif CLOSED_HAT_RANGE[0] <= f0 <= CLOSED_HAT_RANGE[1]:
#             drum_type = "hi_hat_closed"
#         elif RIDE_RANGE[0] <= f0 <= RIDE_RANGE[1]:
#             drum_type = "ride"
#         elif CRASH_RANGE[0] <= f0 <= CRASH_RANGE[1]:
#             drum_type = "crash"
# 
#         # If detected, append
#         if drum_type:
#             meta = DRUM_NOTATION_MAP[drum_type]
#             classified_events.append(
#                 {
#                     "drum_type": drum_type,
#                     "onset_time_seconds": round(onset_time, 2),
#                     "midi_pitch": meta["midi_program"],
#                     "note_head_type": meta["note_head"],
#                     "staff_position": meta["staff_position"],
#                     "analysis": features,
#                 }
#             )
# 
#     return classified_events