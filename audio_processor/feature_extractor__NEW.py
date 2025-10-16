# DrumScript/audio_processor/feature_extractor.py

"""
This module will extract relevant features from audio segments for drum classification.
"""

import os
from typing import List, Dict, Any
import numpy as np
import librosa
import soundfile
import math
import argparse

# --- Configuration ---
SAMPLE_RATE = 44100
ONSET_SLICE_DURATION_MS = 200 # 200 milliseconds
N_MFCC = 41

# --- Main Feature Extraction Functions ---

def extract_features(audio_segment: np.ndarray, sr: int) -> Dict[str, Any]:
    """
    Extracts a dictionary of features from a single audio segment.
    """
    if audio_segment.size == 0:
        return None

    try:
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio_segment, sr=sr))
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio_segment, sr=sr))
        rms = np.mean(librosa.feature.rms(y=audio_segment))
        zcr = np.mean(librosa.feature.zero_crossing_rate(y=audio_segment))
        mfccs = np.mean(librosa.feature.mfcc(y=audio_segment, sr=sr, n_mfcc=N_MFCC), axis=1)

        half_point = len(audio_segment) // 2
        first_half_rms = np.mean(librosa.feature.rms(y=audio_segment[:half_point]))
        second_half_rms = np.mean(librosa.feature.rms(y=audio_segment[half_point:]))
        
        sustain_level = second_half_rms / (first_half_rms + 1e-6)

        return {
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'rms': rms,
            'zero_crossing_rate': zcr,
            'mfccs': mfccs.tolist(),
            'sustain_level': sustain_level
        }

    except Exception as e:
        print(f"Warning: Error extracting features from a segment: {e}")
        return None

def extract_features_for_onsets(y: np.ndarray, sr: int, onset_times: List[float]) -> List[Dict[str, Any]]:
    """
    Slices an audio array around each onset time and extracts features for each slice.
    """
    all_features = []
    half_slice_samples = int((ONSET_SLICE_DURATION_MS / 1000.0) * sr) // 2

    for time_sec in onset_times:
        center_sample = librosa.time_to_samples(time_sec, sr=sr)
        
        start_sample = center_sample - half_slice_samples
        end_sample = center_sample + half_slice_samples
        
        start_sample = max(0, start_sample)
        end_sample = min(len(y), end_sample)
        
        audio_slice = y[start_sample:end_sample]

        features = extract_features(audio_slice, sr)
        
        if features:
            features['onset_time'] = time_sec
            all_features.append(features)
            
    return all_features

# NOTE: The if __name__ == '__main__' block has been removed to avoid confusion.
# The best way to test this module is by running the full drum_classifier.predict pipeline,
# which uses this script to process real onsets.