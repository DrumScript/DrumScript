# DrumScript/audio_processor/audio_loader.py

"""
This module handles loading and basic normalisation of audio files.
It also contains the main execution block to demonstrate the workflow.
"""

from __future__ import annotations

import argparse  # for command-line argument parsing

import librosa
import numpy as np

from drumscript.audio_processor.tempo_detector import estimate_tempo
from drumscript.notation_generator.constants import SAMPLE_RATE

# --- Define functions --------------------------------------------------------------------------------------------
# 1. Load audio file : -------------------------------------------------------------------------------


def load_audio(audio_path: str, sr: int | None = None) -> tuple[np.ndarray, int]:
    """
    Load an audio file and optionally resample it.

    :param audio_path: Path to the audio file (.wav, .mp3, .flac, .ogg, etc.).
    :type audio_path: str
    :param sr: Target sample rate in Hz.
        - ``None`` (default): load at the file's native sample rate (no resampling).
        - An integer (e.g. ``44100``): resample to that rate.
    :type sr: int or None
    :return: Tuple of (audio_data, sample_rate).
    :rtype: tuple[np.ndarray, int]
    :raises FileNotFoundError: If the file does not exist.

    **Examples:**

    Load at native sample rate (for exploration / notebooks)::

        import drumscript as ds
        audio, sr = ds.load_audio("my_drum_loop.wav")
        print(f"Native rate: {sr} Hz")

    Load and resample to 44100 Hz (for the transcription pipeline)::

        from drumscript.notation_generator.constants import SAMPLE_RATE
        audio, sr = ds.load_audio("my_drum_loop.wav", sr=SAMPLE_RATE)
    """
    # sample_rate = SAMPLE_RATE
    try:
        audio_data, sample_rate = librosa.load(
            audio_path, sr=sr
        )  # The librosa.load_audio() fct handles wide variety of audio formats, including .mp3, .wav, .flac, .ogg, etc.
        # return audio_data, sr
        return audio_data, sample_rate
    except FileNotFoundError:
        print(f"Error: Audio file not found at {audio_path}")
        raise
    except Exception as e:
        print(f"Error loading audio file {audio_path}: {e}")
        raise


# 2. Normalise audio file : -------------------------------------------------------------------------------


def normalise_audio(audio_data: np.ndarray) -> np.ndarray:
    """
    Normalises the audio data to a range between -1.0 and 1.0.

    :param audio_data: The input audio time series.
    :type audio_data: np.ndarray
    :return: The normalised audio time series.
    :rtype: np.ndarray

    """
    if audio_data.size == 0:
        return audio_data  # Return empty array if input is empty

    max_abs_val = np.max(np.abs(audio_data))
    if max_abs_val > 0:
        normalised_data = audio_data / max_abs_val
    else:
        normalised_data = audio_data  # Already zero or empty
    return normalised_data


# 3. Audio playback function: -------------------------------------------------------------------------------

# def _prompt_user_for_playback() -> bool:
#  """
#  Prompts the user whether to play the audio and returns their choice.
#
#
#
# Returns:
#    bool: True if the user wants to play, False otherwise.
# """
# response = input("Audio loaded. Would you like to play it? (yes/no): ").strip().lower()
# return response == 'yes' or response == 'y'

# def play_audio(audio_data: np.ndarray, sr: int):
#  """
#  Plays the provided audio data with an option to stop via user input.
#  """
#  def stop_playback_on_enter():
#      input("Audio is playing. Press Enter to stop...\n")
#      sd.stop()
#      print("Playback stopped by user.")
#  print("\nPlaying loaded audio...")
#  sd.play(audio_data, sr)
#

# listener_thread = threading.Thread(target=stop_playback_on_enter, daemon=True)
# listener_thread.start()

# sd.wait()
# print("Audio playback finished.")

# =========================================================================================================w
# MAIN BLOCK
if __name__ == "__main__":
    from drumscript.audio_processor.tempo_detector import estimate_tempo

    # --------------------------------------------------------------------------uncomment during testing
    # from datetime import datetime
    # print("\n# ------------------------------------------------------------------------------------")
    # datetimestamp = datetime.now()
    # print(f'\ndate/time: {datetimestamp}')
    # --------------------------------------------------------------------------------------------------

    print("Running audio_loader.py example with actual MP3/WAV...")  # FUTURE: Find way to encode this so it prints the file path provided in CLI

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Load and process an audio file for DrumScript.")
    parser.add_argument("audio_path", type=str, help="Path to the audio file to be processed.")

    # Parse the command-line arguments
    args = parser.parse_args()
    audio_path = args.audio_path

    try:
        print(f"Attempting to load: {audio_path}")
        audio, sr = load_audio(audio_path, sr=SAMPLE_RATE)

        normalised_audio = normalise_audio(audio)
        normalised_max = np.max(np.abs(normalised_audio))
        assert np.isclose(normalised_max, 1.0) or np.isclose(normalised_max, 0.0), "Normalisation failed!"

        bpm = estimate_tempo(normalised_audio, sr)
        # print(f"Estimated Tempo (Tempogram-First): {int(round(bpm))} BPM")
        print(f"Loaded audio: Shape={audio.shape}, Sample Rate={sr}, Tempo={bpm:.2f}, Duration={len(audio) / sr:.2f} seconds")

        # if _prompt_user_for_playback():
        #  play_audio(normalised_audio, sr)

    except Exception as e:
        print(f"\nAn unexpected error occurred during the example execution: {e}")

# Uncomment to use, for clearer error logs
# print("\n# ------------------------------------------------------------------------------------")
