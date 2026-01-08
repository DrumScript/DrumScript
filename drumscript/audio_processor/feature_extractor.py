# DrumScript/audio_processor/feature_extractor.py

"""
This module will extract relevant features from audio segments for drum classification.
"""

import os
from typing import List, Dict, Any
import numpy as np
import librosa
import soundfile
import math # Added for math.floor to calculate EXPECTED_N_FRAMES
import argparse # for command-line argument parsing
from datetime import datetime
from drumscript.notation_generator.constants import SAMPLE_RATE, SEGMENT_LENGTH_SECONDS, N_FFT, NOISE_THRESH_SNARE, DRUM_NOTATION_MAP, ONSET_SLICE_DURATION_MS, HOP_LENGTH
# from datetime import datetime

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')


# Calculate the expected number of frames (timesteps) per segment
# This calculation needs to be robust to ensure consistency with librosa's output.
# librosa.stft typically returns 1 + (len(y) - n_fft) // hop_length frames.
# So, we first determine the expected audio length that corresponds to SEGMENT_LENGTH_SECONDS
EXPECTED_AUDIO_LEN_SAMPLES = int(SEGMENT_LENGTH_SECONDS * SAMPLE_RATE)
EXPECTED_N_FRAMES = 1 + (EXPECTED_AUDIO_LEN_SAMPLES - N_FFT) // HOP_LENGTH
if EXPECTED_N_FRAMES < 1:
    EXPECTED_N_FRAMES = 1 # Ensure at least one frame, even for very short segments

# previous Define TOTAL_FEATURES_PER_FRAME globally so it's accessible in __main__ block
# previous Number of MFCCs + Spectral Centroid + Spectral Rolloff + ZCR + RMS = 20 + 1 + 1 + 1 + 1 = 24
# previous TOTAL_FEATURES_PER_FRAME = 20 + 1 + 1 + 1 + 1

# current TOTAL_FEATURES_PER_FRAME = 40 (MFCCs) + 1 (Zero-Crossing Rate) = 41
N_MFCC = 41
# UPDATED: We are adding band energy features (Low, Mid, High), so +3 more features
TOTAL_FEATURES_PER_FRAME = N_MFCC + 3 + 3 # TOTAL_FEATURES_PER_FRAME = 47
# THE SCRIP WILL ADD FEATURES [1 (Centroid) + 1 (Rolloff) + 1 (RMS) + 3 (Band Energies)]


# --- Main Feature Extraction Functions ---

def extract_features(audio_segment: np.ndarray, sr: int) -> Dict[str, Any]:
    """
    Extracts a dictionary of features from a single audio segment.
    Features are returned as mean values over the segment's duration.
    """
    if audio_segment.size == 0:
        return None

    try:
        # --- Standard Features ---
        # spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio_segment, sr=sr))
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio_segment, sr=SAMPLE_RATE))
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio_segment, sr=SAMPLE_RATE))
        # spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio_segment, sr=sr))
        rms = np.mean(librosa.feature.rms(y=audio_segment))
        zcr = np.mean(librosa.feature.zero_crossing_rate(y=audio_segment))
        # mfccs = np.mean(librosa.feature.mfcc(y=audio_segment, sr=sr, n_mfcc=N_MFCC), axis=1)
        mfccs = np.mean(librosa.feature.mfcc(y=audio_segment, sr=SAMPLE_RATE, n_mfcc=N_MFCC), axis=1)

        # --- Sustain Feature Calculation ---
        # Split the segment into two halves to measure energy decay.
        half_point = len(audio_segment) // 2
        first_half_rms = np.mean(librosa.feature.rms(y=audio_segment[:half_point]))
        second_half_rms = np.mean(librosa.feature.rms(y=audio_segment[half_point:]))
        
        # Calculate the ratio. Add a small epsilon to avoid division by zero.
        sustain_level = second_half_rms / (first_half_rms + 1e-6)

        # --- Band Energy Calculation (Based on Cheatsheet Logic) ---
        # Calculate Spectrogram magnitude
        S = np.abs(librosa.stft(audio_segment, n_fft=N_FFT, hop_length=HOP_LENGTH))
        
        # Get frequency bins
        # fft_freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
        fft_freqs = librosa.fft_frequencies(sr=SAMPLE_RATE, n_fft=N_FFT)
        
        # Define masks for bands based on constants.py (Low < 300Hz, Mid 300-5000Hz, High > 5000Hz)
        # Note: 300Hz chosen to separate Kick/Floor Tom from Snare/Rack Tom body
        low_band_mask = (fft_freqs <= 300)
        mid_band_mask = (fft_freqs > 300) & (fft_freqs <= 5000)
        high_band_mask = (fft_freqs > 5000)

        # Sum energy in these bands (averaging over time)
        energy_low = np.mean(np.sum(S[low_band_mask, :], axis=0))
        energy_mid = np.mean(np.sum(S[mid_band_mask, :], axis=0))
        energy_high = np.mean(np.sum(S[high_band_mask, :], axis=0))

        return {
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'rms': rms,
            'zero_crossing_rate': zcr,
            'mfccs': mfccs.tolist(),
            'sustain_level': sustain_level,
            'energy_low': energy_low,   # Kick/Floor Tom indicator
            'energy_mid': energy_mid,   # Snare/Rack Tom indicator
            'energy_high': energy_high  # Hi-Hat/Cymbal indicator
        }

    except Exception as e:
        print(f"Warning: Error extracting features from a segment: {e}")
        return None

def extract_features_for_onsets(y: np.ndarray, sr: int, onset_times: List[float]) -> List[Dict[str, Any]]:
    """
    Slices an audio array around each onset time and extracts features for each slice.
    """
    all_features = []
    sr = SAMPLE_RATE
    # Calculate *half* the slice duration in samples
    half_slice_samples = int((ONSET_SLICE_DURATION_MS / 1000.0) * sr) // 2

    for time_sec in onset_times:
        # center_sample = librosa.time_to_samples(time_sec, sr=sr)
        center_sample = librosa.time_to_samples(time_sec, sr=SAMPLE_RATE)
        
        # Define start and end points, centered around the onset
        start_sample = center_sample - half_slice_samples
        end_sample = center_sample + half_slice_samples
        
        # Boundary checks
        start_sample = max(0, start_sample)
        end_sample = min(len(y), end_sample)
        
        audio_slice = y[start_sample:end_sample]

        # Extract features for the slice
        features = extract_features(audio_slice, sr)
        
        if features:
            # Add the onset time to the dictionary of features
            features['onset_time'] = time_sec
            all_features.append(features)
            
    return all_features

# Uncomment to use, for clearer error logs
# print("\n# ------------------------------------------------------------------------------------")