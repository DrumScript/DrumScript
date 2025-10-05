# DrumScript/audio_processor/feature_extractor.py

"""
This module will extract relevant features from audio segments for drum classification.
[UPDATE--SUN05OCT2025]: It has been updated slightly for new classification system
"""

import os
from typing import List, Dict, Any
import numpy as np
import librosa
import soundfile
import math # Added for math.floor to calculate EXPECTED_N_FRAMES
import argparse # for command-line argument parsing


# --- Configuration (Mirroring model_trainer.py for consistency) ---
# These should ideally be imported from a central 'constants.py'
# but for now, we'll keep them consistent by defining them here.
SAMPLE_RATE = 44100
SEGMENT_LENGTH_SECONDS = 0.2 # SEGMENT_LENGTH_SECONDS is the duration of the audio snapshot the script analyses at one time. To give two extremes. If you increase it (e.g., to 1.0): You would capture several drum hits in one fingerprint, making it impossible for the model to know which sound happened when, if you decrease it (e.g., to 0.05): You might only capture the initial "click" of the drum hit and miss the sound's body, losing important information. 0.2 is (seconds) is usually good-enough for drum events, ie kick+snare
N_FFT = 1024 # N_FFT is the 'size of the window for the fourier transform" N_FFT = 1024 (Frequency Resolution)
# This is the size of the analysis window for the Fourier Transform, which breaks the sound down into its constituent frequencies. A larger N_FFT gives you a more detailed picture of which frequencies are present but a less precise idea of exactly when they happened. If you increase it (e.g., to 2048): You get a very precise frequency analysis, which could help distinguish two very similar-sounding cymbals. If you decrease it (e.g., to 512): You get better timing precision but a "blurrier" picture of the frequencies.
HOP_LENGTH = 512
# NEW: Define a fixed duration for the audio slice to analyze around each onset
ONSET_SLICE_DURATION_MS = 200 # 200 milliseconds

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
TOTAL_FEATURES_PER_FRAME = N_MFCC + 3 # TOTAL_FEATURES_PER_FRAME = 44
# THE SCRIP WILL ADD 3 FEATURES [1 (Centroid) + 1 (Rolloff) + 1 (RMS)] SO IN TOTAL WE HAVE 44 FEATURES


# --- Main Feature Extraction Functions ---

def extract_features(audio_segment: np.ndarray, sr: int) -> Dict[str, Any]:
    """
    Extracts a dictionary of features from a single audio segment.

    Features are returned as mean values over the segment's duration.
    """
    if audio_segment.size == 0:
        return None

    try:
        # 1. Spectral Centroid
        spectral_centroid = np.mean(librosa.feature.spectral_centroid(y=audio_segment, sr=sr))

        # 2. Spectral Rolloff
        spectral_rolloff = np.mean(librosa.feature.spectral_rolloff(y=audio_segment, sr=sr))

        # 3. RMS Energy
        rms = np.mean(librosa.feature.rms(y=audio_segment))
        
        # 4. Zero-Crossing Rate
        zcr = np.mean(librosa.feature.zero_crossing_rate(y=audio_segment))

        # 5. MFCCs
        mfccs = np.mean(librosa.feature.mfcc(y=audio_segment, sr=sr, n_mfcc=N_MFCC), axis=1)

        # Return a dictionary of features
        return {
            'spectral_centroid': spectral_centroid,
            'spectral_rolloff': spectral_rolloff,
            'rms': rms,
            'zero_crossing_rate': zcr,
            'mfccs': mfccs.tolist() # Convert numpy array to list for JSON serialization
        }

    except Exception as e:
        print(f"Warning: Error extracting features from a segment: {e}")
        return None

# NEW: Wrapper function to process all onsets from a single audio file.
# This is the function that `predict.py` will import and use.
def extract_features_for_onsets(y: np.ndarray, sr: int, onset_times: List[float]) -> List[Dict[str, Any]]:
    """
    Slices an audio array around each onset time and extracts features for each slice.
    """
    all_features = []
    slice_samples = int((ONSET_SLICE_DURATION_MS / 1000.0) * sr)

    for time_sec in onset_times:
        start_sample = librosa.time_to_samples(time_sec, sr=sr)
        end_sample = start_sample + slice_samples
        
        # Ensure the slice does not go out of bounds
        audio_slice = y[start_sample:end_sample]

        # Extract features for the slice
        features = extract_features(audio_slice, sr)
        
        if features:
            # Add the onset time to the dictionary of features
            features['onset_time'] = time_sec
            all_features.append(features)
            
    return all_features


if __name__ == '__main__':
    # This block is for testing the feature_extractor.py script directly.
    import os
    from audio_loader import load_audio
    
    print("--- Running feature_extractor.py test ---")
    
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
    test_audio_path = os.path.join(project_root, "test_audio", "test.wav")
    # print(f'project_root: {project_root}') # comment out if need to check imports
    # print(f'test_audio_path: {test_audio_path}') # comment out if need to check imports

    if not os.path.exists(test_audio_path):
        print(f"Error: Test audio file not found at {test_audio_path}")
    else:
        y, sr = load_audio(test_audio_path)
        
        # Dummy onsets for testing
        onset_times_test = [0.5, 1.0, 1.5] 
        print(f"Testing with dummy onsets at times: {onset_times_test}")

        # Test the new wrapper function
        features_list = extract_features_for_onsets(y, sr, onset_times_test)
        
        if features_list:
            print(f"\nSuccessfully extracted features for {len(features_list)} onsets.")
            print("\n--- Features for first detected onset ---")
            first_onset = features_list[0]
            for key, value in first_onset.items():
                if isinstance(value, list):
                    print(f"  {key}: list of {len(value)} values")
                else:
                    print(f"  {key}: {value:.2f}")
        else:
            print("\nFeature extraction failed or returned no features.")

    print("\n--- feature_extractor.py test finished ---")
    print("\n-----------------------------------------------------")
