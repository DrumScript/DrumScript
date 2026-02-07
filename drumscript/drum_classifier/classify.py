# DrumScript/drum_classifier/classify.py
# Requires path to audio file in cli command, ie:
# `python3 -m drumscript.drum_classifier.classify path_to_audio_file
# ------------------------------------------------------------------------------------------------------------
"""
This script determines the classification rules by which the parameters in constants.py are applied to audio_file_path.
"""

from typing import Any, Dict, List

import librosa
import numpy as np


from drumscript.notation_generator import constants
from drumscript.notation_generator import constants as c
from drumscript.notation_generator.constants import DRUM_NOTATION_MAP, N_FFT, SAMPLE_RATE

# from datetime import datetime

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')
# print("\n# ------------------------------------------------------------------------------------")

import numpy as np
import scipy.signal
from drumscript.notation_generator import constants as c

def get_spectral_features(y, sr):
    """
    Extracts physics fingerprints: Peak Freq, Low Energy (Bass), High Energy (Treble).
    """
    freqs, psd = scipy.signal.welch(y, sr, nperseg=2048)
    
    # Peak Frequency
    peak_idx = np.argmax(psd)
    peak_freq = freqs[peak_idx]
    
    # Energy Ratios
    total_energy = np.sum(psd) + 1e-9
    
    # Bass (Kick indicator)
    low_energy = np.sum(psd[freqs < 150])
    lfer = low_energy / total_energy
    
    # Treble (Snare Wire indicator)
    high_energy = np.sum(psd[freqs > 2000])
    hfer = high_energy / total_energy
    
    return peak_freq, lfer, hfer

def is_kick(peak_freq, lfer, hfer):
    # Rule 1: Must be in bass range
    is_bass = c.KICK_FREQ_MIN <= peak_freq <= c.KICK_FREQ_MAX
    # Rule 2: Must be thump-dominant
    is_thump = lfer >= c.KICK_LFER_MIN
    # Rule 3 (Tie-Breaker): Must NOT have too much treble (excludes fat snares)
    not_too_crisp = hfer < c.SNARE_HFER_MIN
    
    return is_bass and is_thump and not_too_crisp

def is_snare(peak_freq, hfer):
    # Case A: Standard Snare (High pitched body)
    is_standard = c.SNARE_FREQ_MIN <= peak_freq <= c.SNARE_FREQ_MAX
    
    # Case B: Fat/Deep Snare (Low pitch, but lots of wire noise)
    # This catches snare_0004 (64Hz)
    is_fat_snare = (peak_freq < c.SNARE_FREQ_MIN) and (hfer >= c.SNARE_HFER_MIN)
    
    return is_standard or is_fat_snare

def classify_event(audio_segment, sr):
    peak_freq, lfer, hfer = get_spectral_features(audio_segment, sr)
    
    # Priority: Check Snare first (as it overlaps kick freq sometimes)
    if is_snare(peak_freq, hfer):
        return "Snare"
    elif is_kick(peak_freq, lfer, hfer):
        return "Kick"
    
    return "Unknown"

# print("\n# ------------------------------------------------------------------------------------")
# LEGACY CODE (PRESERVING FOR EASE)

"""def analyze_event(y, sr):
    #
    #Calculates specific acoustic features:
    #- f0: Fundamental Frequency (Peak Magnitude)
    #- sc: Spectral Centroid (Brightness)
    #- width: Spectral Bandwidth
    #- depth: Decay Ratio (Sustain)

    #:param y: Audio segment.
    #:type y: np.ndarray
    #:param sr: Sampling rate.
    #:type sr: int
    #:return: Dictionary of features [f0: (Fundamental Frequency (Peak Magnitude)), sc: Spectral Centroid (Brightness), width: Spectral Bandwidth], depth: Decay Ratio (Sustain)]
    #:rtype: dict
    
    # 1. FFT for Frequency Analysis
    # High resolution (n_fft=2048) to see low frequencies clearly
    # n_fft = 2048
    # spec = np.abs(librosa.stft(y, n_fft=n_fft))
    # freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    n_fft = N_FFT
    spec = np.abs(librosa.stft(y, n_fft=N_FFT))
    freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)

    # Sum magnitudes to find the strongest frequency (Fundamental)
    sum_spec = np.sum(spec, axis=1)
    peak_idx = np.argmax(sum_spec)
    f0 = freqs[peak_idx]

    # 2. Spectral Features
    # sc = float(np.mean(librosa.feature.spectral_centroid(S=spec, sr=sr)))
    # width = float(np.mean(librosa.feature.spectral_bandwidth(S=spec, sr=sr)))

    sc = float(np.mean(librosa.feature.spectral_centroid(S=spec, sr=SAMPLE_RATE)))
    width = float(np.mean(librosa.feature.spectral_bandwidth(S=spec, sr=SAMPLE_RATE)))
    # 3. Depth / Decay (Sustain)
    rms = librosa.feature.rms(y=y)[0]
    split = len(rms) // 2
    if np.mean(rms[:split]) < 1e-5:
        decay = 0.0
    else:
        decay = np.mean(rms[split:]) / np.mean(rms[:split])

    return {
        "f0": float(f0),
        "sc": float(round(sc, 2)),
        "width": float(round(width, 2)),
        "depth": float(round(decay, 2)),
    }

"""
"""
def classify_events (audio_data, sr, onsets) -> List[Dict[str, Any]]:
    # Classifies hits strictly based on Fundamental Frequency ($f_0$) ranges.
    :param audio_data: Full audio array.
    :type audio_data: np.ndarray
    :param sr: Sampling rate.
    :type sr: int
    :param onsets: List of onset times.
    :type onsets: list
    :return: List of classified event dictionaries.
    :rtype: List[Dict[str, Any]]

    classified_events = []

    for onset_time in onsets:
        # Extract 150ms window for analysis
        start_sample = int(onset_time * sr)
        end_sample = int((onset_time + 0.15) * sr)

        if end_sample > len(audio_data):
            end_sample = len(audio_data)
        if start_sample >= end_sample:
            continue

        y_window = audio_data[start_sample:end_sample]
        if len(y_window) == 0:
            continue

        # Analyze
        features = analyze_event(y_window, sr)
        f0 = features["f0"]

        drum_type = None

        # --- STRICT FREQUENCY RANGE CLASSIFICATION ---
        # Order matters for overlaps!

        # 1. Low End
        if constants.KICK_RANGE[0] <= f0 <= constants.KICK_RANGE[1]:
            drum_type = "kick"
        elif constants.LOW_TOM_RANGE[0] <= f0 <= constants.LOW_TOM_RANGE[1]:
            drum_type = "low_tom"

        # 2. Mids (Check Tom first to catch narrow band, then Snare)
        elif constants.MID_TOM_RANGE[0] <= f0 <= constants.MID_TOM_RANGE[1]:
            drum_type = "mid_tom"
        elif constants.SNARE_RANGE[0] <= f0 <= constants.SNARE_RANGE[1]:
            drum_type = "snare"

        # 3. Highs
        elif constants.OPEN_HAT_RANGE[0] <= f0 <= constants.OPEN_HAT_RANGE[1]:
            drum_type = "hi_hat_open"
        elif constants.CLOSED_HAT_RANGE[0] <= f0 <= constants.CLOSED_HAT_RANGE[1]:
            drum_type = "hi_hat_closed"
        elif constants.RIDE_RANGE[0] <= f0 <= constants.RIDE_RANGE[1]:
            drum_type = "ride"
        elif constants.CRASH_RANGE[0] <= f0 <= constants.CRASH_RANGE[1]:
            drum_type = "crash"

        # If detected, append
        if drum_type:
            meta = DRUM_NOTATION_MAP[drum_type]
            classified_events.append(
                {
                    "drum_type": drum_type,
                    "onset_time_seconds": round(onset_time, 2),
                    "midi_pitch": meta["midi_program"],
                    "note_head_type": meta["note_head"],
                    "staff_position": meta["staff_position"],
                    "analysis": features,
                }
            )

    return classified_events"""