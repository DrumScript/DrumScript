# DrumScript/audio_processor/onset_detector.py
"""
This module will detect the onset (start) times of drum hits in the audio.
"""
import librosa
import numpy as np
import os
import soundfile
import argparse # for command-line argument parsing
from datetime import datetime
import scipy

# print("\n# ---------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time of run: {datetimestamp}') # for logging 

def detect_onsets(audio_data: np.ndarray, sr: int) -> list[float]:
    """
    Detects onsets using a Multi-Band approach to capture both 
    heavy kicks (Low) and sharp cymbals (High) accurately, 
    even when they occur simultaneously.
    """
    if audio_data.size == 0:
        return []

    # --- 1. Standard Percussive Detection (Catches Snare, Hats, Crashes) ---
    # We use the 'percussive' component to remove tonal ringing
    y_percussive = librosa.effects.percussive(y=audio_data)
    
    standard_onsets = librosa.onset.onset_detect(
        y=y_percussive, 
        sr=sr, 
        units='time', 
        delta=0.06  # Sensitive enough for ghost notes
        # wait=1       # Don't double-trigger too fast
    )

    # --- 2. Low-Frequency Detection (Optimized for Kicks) ---
    # Filter audio to only hear < 200 Hz (The "Thump" zone)
    sos = scipy.signal.butter(4, 200, 'low', fs=sr, output='sos')
    y_low = scipy.signal.sosfilt(sos, audio_data)
    
    # Detect onsets specifically in this muddy low end
    # We use a higher delta here because kicks are powerful
    kick_onsets = librosa.onset.onset_detect(
        y=y_low, 
        sr=sr, 
        units='time', 
        delta=0.1  # Less sensitive, needs a real THUMP
        #wait=2       # Kicks don't roll as fast as snares
    )

    # --- 3. Merge & De-Duplicate ---
    # Combine both lists of timestamps
    all_onsets = np.concatenate((standard_onsets, kick_onsets))
    all_onsets.sort()
    
    # Remove duplicates that are too close together (e.g. < 30ms)
    # This prevents a single loud Kick from registering as two hits (Low + Standard)
    unique_onsets = []
    if len(all_onsets) > 0:
        unique_onsets.append(all_onsets[0])
        for onset in all_onsets[1:]:
            if onset - unique_onsets[-1] > 0.03: # 30ms window
                unique_onsets.append(onset)
            else:
                # If we have a duplicate, keep the average time for better accuracy? 
                # For now, just keeping the first one is cleaner.
                pass

    return unique_onsets
    # print("\n# ---------------------------------------------------------------------------------------")