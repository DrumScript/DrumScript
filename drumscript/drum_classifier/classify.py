# DrumScript/drum_classifier/classify.py
# Requires path to audio file in cli command, ie:
# `python3 -m drumscript.drum_classifier.classify path_to_audio_file
# ------------------------------------------------------------------------------------------------------------
"""
This script determines the classification rules by which the parameters in py are applied to audio_file_path.
"""

from typing import Any, Dict, List
import numpy as np
import scipy.signal
import librosa
from drumscript.notation_generator.constants import SAMPLE_RATE, ONSET_SLICE_DURATION_MS, N_FFT, HOP_LENGTH, DRUM_NOTATION_MAP,KICK_FREQ_MIN, KICK_FREQ_MAX, KICK_LFER_MIN, SNARE_FREQ_MIN, SNARE_FREQ_MAX, SNARE_HFER_MIN, TOM_FREQ_LOW_MAX, TOM_FREQ_MID_MAX, TOM_MIN_DECAY, HAT_CLOSED_MAX_DECAY, HAT_OPEN_MAX_DECAY, IDIOPHONE_MIN_HFER_5K, CYMBAL_CENTROID_THRESHOLD
from drumscript.notation_generator import constants

from datetime import datetime

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f'\ndate/time: {datetimestamp}')


def get_physics_profile(y, sr): # remains unchanged but amended function docstring slightly
    """
    Extracts the 'DNA' of the drum hit: Pitch, Decay, Brightness, and Energy Ratios.
    Uses High-Res Scipy Welch and RMS.
    """
    # 1. Frequency Analysis (High Resolution)
    freqs, psd = scipy.signal.welch(y, sr, nperseg=4096)
    peak_idx = np.argmax(psd)
    peak_freq = freqs[peak_idx]
    
    # 2. Spectral Centroid (Brightness - Critical for Cymbals)
    centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
    
    # 3. Energy Distribution Ratios
    total_energy = np.sum(psd) + 1e-9
    
    # Bass Energy (<150Hz) - Kick detection
    low_energy = np.sum(psd[freqs < 150])
    lfer = low_energy / total_energy
    
    # Wire Energy (>2000Hz) - Snare vs High Tom detection
    mid_high_energy = np.sum(psd[freqs > 2000])
    #hfer_2k = mid_high_energy / total_energy
    hfer = mid_high_energy / total_energy
    
    # Shimmer Energy (>5000Hz) - Skin vs Metal detection
    high_energy = np.sum(psd[freqs > 5000])
    hfer_5k = high_energy / total_energy
    
    # 4. Resonance (Decay Time)
    rms = librosa.feature.rms(y=y)[0]
    peak_rms_idx = np.argmax(rms)
    threshold = np.max(rms) * 0.1 # -20dB point
    
    decay_frames = 0
    for i in range(peak_rms_idx, len(rms)):
        if rms[i] < threshold:
            break
        decay_frames += 1
    decay_time = librosa.frames_to_time(decay_frames, sr=sr)
    
    return {
        "peak_freq": peak_freq,
        "centroid": centroid,
        "lfer": lfer,
        #"hfer_2k": hfer_2k,
        "hfer": hfer,      # Renamed key to 'hfer' to match _classifier logging
        "hfer_5k": hfer_5k,
        "decay": decay_time
    }



def classify_membranophone(p):
    """
    Stage 2A: Sorts Skins (Kick, Snare, Toms).
    """
    # 1. IDENTIFY SNARE (The "Noisy" Skin)
    # Must have wire noise (>2k energy). Frequency alone is unreliable.
    is_snare_freq = SNARE_FREQ_MIN <= p['peak_freq'] <= SNARE_FREQ_MAX
    is_snare_wire = p['hfer_2k'] >= SNARE_HFER_MIN
    
    if is_snare_freq and is_snare_wire:
        return "snare"
    
    # Fallback for deep/fat snares
    if (p['peak_freq'] < SNARE_FREQ_MIN) and is_snare_wire:
        return "snare"

    # 2. IDENTIFY KICK vs LOW TOM
    # Conflict Zone: < 92Hz. Use Decay to separate.
    if p['peak_freq'] <= TOM_FREQ_LOW_MAX:
        if p['decay'] > TOM_MIN_DECAY:
            return "low_tom" # Long boom
        else:
            return "kick"    # Short thud

    # 3. IDENTIFY REMAINING TOMS
    # If we are here, it's a skin, not a snare, not a kick.
    if p['peak_freq'] <= TOM_FREQ_MID_MAX:
        return "mid_tom"
    
    # Default: High Tom (Pure tone > 135Hz)
    return "high_tom"

def classify_idiophone(p):
    """
    Stage 2B: Sorts Metals (Hats, Cymbals).
    """
    decay = p['decay']
    
    # 1. Check Closed Hi-Hat (Shortest)
    if decay <= HAT_CLOSED_MAX_DECAY:
        return "hi_hat_closed"
    
    # 2. Check Open Hi-Hat (Medium)
    elif decay <= HAT_OPEN_MAX_DECAY:
        return "hi_hat_open"
    
    # 3. Check Cymbals (Longest)
    # Differentiate Ride vs Crash using Spectral Centroid (Brightness)
    else:
        if p['centroid'] > CYMBAL_CENTROID_THRESHOLD:
            return "crash" # Bright, explosive
        else:
            return "ride"  # Darker, gong-like body

def classify_event(audio_segment, sr):
    """
    Stage 1: Class Separation (Skin vs Metal)
    """
    physics = get_physics_profile(audio_segment, sr)
    
    # Is it Metal? (High energy > 5kHz)
    if physics['hfer_5k'] >= IDIOPHONE_MIN_HFER_5K:
        return classify_idiophone(physics)
    else:
        return classify_membranophone(physics)

# --- NEW SIMULTANEOUS PHYSICS ENGINE (Merged from _classifier.py + Your Decay Rules) ---
def classify_onset(p: dict) -> list[str]:
    """
    Applies deterministic physics rules to classify the hit.
    Evaluates Skins and Metals independently so they can trigger simultaneously!
    """
    detected_instruments = []
    
    # --- CLASS 1: MEMBRANOPHONES (SKINS) ---
    
    # RULE 1: KICK vs LOW TOM (Using LFER and Decay)
    if p['lfer'] >= KICK_LFER_MIN and (KICK_FREQ_MIN <= p['peak_freq'] <= KICK_FREQ_MAX):
        # We use your awesome RMS decay rule to separate the short thud from the long boom!
        if p['decay'] > TOM_MIN_DECAY:
            detected_instruments.append('low_tom')
        else:
            detected_instruments.append('kick')
            
    # RULE 2: SNARE DRUM
    is_snare_freq = (SNARE_FREQ_MIN <= p['peak_freq'] <= SNARE_FREQ_MAX)
    has_snare_wire = (SNARE_HFER_MIN <= p['hfer'] < 0.85) # Capped at 0.85 to avoid pure hi-hats
    
    if has_snare_wire and (is_snare_freq or p['peak_freq'] < SNARE_FREQ_MIN):
        detected_instruments.append('snare')
        
    # RULE 3: MID / HIGH TOMS (Pure tones with low wire noise)
    if p['hfer'] < SNARE_HFER_MIN: # It doesn't have snare wires
        if TOM_FREQ_LOW_MAX < p['peak_freq'] <= TOM_FREQ_MID_MAX:
            detected_instruments.append('mid_tom')
        elif p['peak_freq'] > TOM_FREQ_MID_MAX and p['peak_freq'] <= 400: # Upper safety bound
            detected_instruments.append('high_tom')


    # --- CLASS 2: IDIOPHONES (METALS) ---
    
    # RULE 4: METALS (Hats / Cymbals)
    if p['hfer_5k'] >= IDIOPHONE_MIN_HFER_5K:
        # We use your decay rules to determine the exact metal!
        decay = p['decay']
        if decay <= HAT_CLOSED_MAX_DECAY:
            detected_instruments.append('hi_hat_closed')
        elif decay <= HAT_OPEN_MAX_DECAY:
            detected_instruments.append('hi_hat_open')
        else:
            # Note: You may need to tune CYMBAL_CENTROID_THRESHOLD down to ~2500 
            # if Kick bleed pulls the centroid down.
            if p['centroid'] > CYMBAL_CENTROID_THRESHOLD:
                detected_instruments.append('crash') 
            else:
                detected_instruments.append('ride') 
            
    # Fallback
    if not detected_instruments:
        detected_instruments.append('unknown')
        
    return detected_instruments

def classify_events(audio_data, sr, onsets) -> List[Dict[str, Any]]:
    """
    Wrapper to route detected onsets through the new Physics-First Classification Engine.
    """
    classified_events = []

    for onset_time in onsets:
        # Extract 200ms window (as defined in our Feb 9 constants: ONSET_SLICE_DURATION_MS)
        start_sample = int(onset_time * sr)
        end_sample = int((onset_time + 0.2) * sr)
        #duration_secs = ONSET_SLICE_DURATION_MS / 1000.0 
        #end_sample = start_sample + int(duration_secs * sr)


        if end_sample > len(audio_data):
            end_sample = len(audio_data)
        if start_sample >= end_sample:
            continue

        y_window = audio_data[start_sample:end_sample]
        if len(y_window) == 0:
            continue

        # --- ROUTE TO NEW PHYSICS ENGINE ---
        # We now use the classify_event function we built together!
        drum_type = classify_event(y_window, sr)

        if drum_type:
            meta = constants.DRUM_NOTATION_MAP.get(drum_type, constants.DRUM_NOTATION_MAP['snare']) ## WHY IS THIS ONLY THE SNARE? 
            
            # To avoid breaking your score_builder which expects an 'analysis' dict:
            physics_profile = get_physics_profile(y_window, sr)
                   # 2. Run the simultaneous rules
            instruments = classify_onset(physics_profile)
            
            classified_events.append(
                {
                    "drum_type": drum_type,
                    "onset_time_seconds": round(onset_time, 2),
                    "midi_pitch": meta["midi_program"],
                    "note_head_type": meta["note_head"],
                    "staff_position": meta["staff_position"],
                    #"analysis": physics_profile, # Feed the new physics data to the JSON output
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