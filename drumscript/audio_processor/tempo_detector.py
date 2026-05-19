# DrumScript/audio_processor/tempo_detector.py
# ------------------------------------------------------------------------------------------------------------
"""
This module contains functions for automatic tempo detection from audio data.
"""
# Import packages: ------------------------------------------------------------------------------------------------

import argparse

import librosa
import numpy as np

from drumscript.notation_generator.constants import SAMPLE_RATE


def estimate_tempo(audio_path, sr):
    """
    Estimates tempo from the tempogram, but restricted to a plausible range.
    (Corrected to avoid INF and extreme BPM errors, ie 10500 BPM).
    Returns a default 120.0 BPM if the audio is too short to analyze.

    :param audio_path: The input audio time series.
    :type audio_path: np.ndarray
    :param sr: Sampling rate of the audio.
    :type sr: int
    :return: The estimated tempo in Beats Per Minute (BPM).
    :rtype: float
    """
    if audio_path.size == 0:
        return 0.0

    # Check if there are enough hits in the audio
    # Calculating tempo on clips shorter than ~1-2 seconds is unreliable and often produces artifacts (like 235 BPM for a single kick).
    duration_seconds = audio_path.shape[0] / sr
    if duration_seconds < 1.0:  # duration_seconds less than 1 second, ie anything over 1 sec duration is valid
        print(f"Audio too short for tempo detection ({duration_seconds:.2f}s). Defaulting to 120 BPM.")
        return 120.0

    # oenv = librosa.onset.onset_strength(y=audio_path, sr=sr, hop_length=256)
    oenv = librosa.onset.onset_strength(y=audio_path)
    tempogram = librosa.feature.tempogram(onset_envelope=oenv)
    tempo_spectrum = np.sum(tempogram, axis=1)
    tempo_freqs = librosa.tempo_frequencies(tempogram.shape[0])

    # --- Fix for extreme BPM error ---
    # Create a mask to only consider tempos in a plausible musical range (e.g., 60-240 BPM)
    plausible_tempos_mask = (tempo_freqs >= 60) & (tempo_freqs <= 240)

    # Find the index of the peak within the plausible range
    plausible_spectrum = tempo_spectrum[plausible_tempos_mask]
    if plausible_spectrum.size == 0:
        return 120.0  # Return default if no energy in plausible range

    peak_idx_in_plausible_range = np.argmax(plausible_spectrum)

    # Convert that index back to a BPM value
    plausible_tempo_freqs = tempo_freqs[plausible_tempos_mask]
    estimated_bpm = plausible_tempo_freqs[peak_idx_in_plausible_range]

    return estimated_bpm


# =====================================================================================================
# MAIN BLOCK - for local testing of this function

if __name__ == "__main__":
    # uncomment during testing
    # from datetime import datetime
    # print("\n# ------------------------------------------------------------------------------------")
    # datetimestamp = datetime.now()
    # print(f'\ndate/time: {datetimestamp}')

    from drumscript.audio_processor.audio_loader import load_audio, normalise_audio
    from drumscript.notation_generator.constants import SAMPLE_RATE

    parser = argparse.ArgumentParser(description="Estimate the tempo of an audio file.")
    # parser.add_argument("audio_file_path", type=str, help="Path to the audio file to be processed.")
    parser.add_argument("audio_path", type=str, help="Path to the audio file to be processed.")
    args = parser.parse_args()
    # actual_drum_recording_path = args.audio_file_path  # audio_file_path, relative to ROOT, not the path of this script
    audio_path = args.audio_path  # audio_path, relative to ROOT, not the path of this script
    sr = SAMPLE_RATE

    try:
        # Load and normalise the audio
        # print(f"Attempting to load: {actual_drum_recording_path}")
        print(f"Attempting to load: {audio_path}")
        # audio, sr = load_audio(actual_drum_recording_path, sr=44100)
        # audio, sr = load_audio(actual_drum_recording_path, sr=sr)
        audio, sr = load_audio(audio_path, sr=sr)
        normalised_audio = normalise_audio(audio)

        # Estimate the tempo
        bpm = estimate_tempo(normalised_audio, sr)
        print(f"Estimated Tempo: {int(round(bpm))} BPM")

    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    # print("\n#==================================================================================================")

# ------------------------------------------------------------------------------------------------------
