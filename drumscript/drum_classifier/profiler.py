
# drumscript/drum_classifier/profiler.py
# 
import numpy as np
import librosa

def analyse_track_profile(audio_data: np.ndarray, sr: int, onsets: list[float]) -> bool:
    """
    Analyses the raw audio and onsets to determine if the track is a isolated/repetitive 
    single beat sample, or a complex polyphonic song.
    
    Uses Global Spectral Variance (GSV) and Onset Density.
    Returns True if it's a single beat track, False if it's a standard song.
    """
    if len(onsets) <= 1:
        return True
        
    duration = len(audio_data) / sr
    
    # Check 1: Onset Density (Hits per second)
    # A single isolated hit or a sparse loop usually has a low density.
    onset_density = len(onsets) / duration if duration > 0 else 0
    if duration < 20.0 and onset_density < 1.5:
        return True

    # Check 2: Global Spectral Variance (GSV)
    # We take the RMS (volume) of each onset slice. If the variance between the peaks 
    # is extremely low (meaning every hit is exactly as loud as the last), it's highly 
    # likely to be a sequenced, repetitive single beat loop, not a human playing a song.
    peaks = []
    for onset in onsets:
        start_sample = int(onset * sr)
        end_sample = start_sample + int(0.1 * sr) # 100ms slice
        
        if end_sample > len(audio_data):
            end_sample = len(audio_data)
            
        slice_data = audio_data[start_sample:end_sample]
        if len(slice_data) > 0:
            peaks.append(np.max(np.abs(slice_data)))
            
    if len(peaks) > 1:
        variance = np.var(peaks)
        # If the variance between hits is practically zero, it's a mechanical single beat
        if variance < 0.005: 
            return True

    # Default to normal polyphonic song classification
    return False

# Reasoning: Separating this logic into `profiler.py` keeps the classification engine clean and allows us to easily test and tweak the GSV thresholds independently.