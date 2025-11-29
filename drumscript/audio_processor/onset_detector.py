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
# import scipy # removed. CONSIDER DELETING. For kick drum detection, testing

# print("\n# ---------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time of run: {datetimestamp}') # for logging 

def detect_onsets(audio_data: np.ndarray, sr: int) -> list[float]:
    """
    Detects onsets using standard percussive detection.
    Specific low-frequency kick detection has been removed to rely on the 
    standard wide-band detection.
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

    # Return the standard onsets directly
    return standard_onsets.tolist()