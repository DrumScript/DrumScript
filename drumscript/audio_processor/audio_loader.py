# DrumScript/audio_processor/audio_loader.py
"""
This module handles loading and basic normalisation of audio files.
"""
# ------------------------------------------------------------------------------------------------------

"""
This module handles loading and basic normalisation of audio files.
It also contains the main execution block to demonstrate the workflow.
"""
# Import packages: ------------------------------------------------------------------------------------------------

import librosa
import numpy as np
import os
import sounddevice as sd
import threading
import argparse # for command-line argument parsing
from drumscript.notation_generator.constants import SAMPLE_RATE # Other args avl: SEGMENT_LENGTH_SECONDS, N_FFT, NOISE_THRESH_SNARE, DRUM_NOTATION_MAP, ONSET_SLICE_DURATION_MS, HOP_LENGTH
from drumscript.audio_processor import tempo_detector
from drumscript.audio_processor.tempo_detector import estimate_tempo

# from datetime import datetime

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')


# --- Define functions --------------------------------------------------------------------------------------------
# 1. Load audio file : -------------------------------------------------------------------------------

def load_audio(file_path: str, sr: int=SAMPLE_RATE) -> tuple[np.ndarray, int]:
    """
    Loads an audio file and optionally resamples it.

    :param file_path: The path to the audio file.
    :type file_path: str
    :param sr: The target sample rate.
    :type sr: int
    :return: A tuple containing (audio_data, sample_rate).
    :rtype: tuple[np.ndarray, int]
    :raises FileNotFoundError: If the file does not exist.
    """
    # sample_rate = SAMPLE_RATE
    try:
        audio_data, sample_rate = librosa.load(file_path, sr=sr) # The librosa.load_audio() fct handles wide variety of audio formats, including .mp3, .wav, .flac, .ogg, etc.
        return audio_data, sr
    except FileNotFoundError:
        print(f"Error: Audio file not found at {file_path}")
        raise
    except Exception as e:
        print(f"Error loading audio file {file_path}: {e}")
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
        return audio_data # Return empty array if input is empty

    max_abs_val = np.max(np.abs(audio_data))
    if max_abs_val > 0:
        normalised_data = audio_data / max_abs_val
    else:
        normalised_data = audio_data # Already zero or empty
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
    # print("\n#=============================================================================================")
    print("Running audio_loader.py example with actual MP3/WAV...")  # FUTURE: Find way to encode this so it prints the file path provided in CLI

    # Set up argument parser
    parser = argparse.ArgumentParser(description="Load and process an audio file for DrumScript.")
    parser.add_argument("audio_file_path", type=str,
                        help="Path to the audio file to be processed.")
    
    # Parse the command-line arguments
    args = parser.parse_args()
    actual_drum_recording_path = args.audio_file_path
    
    try:
        print(f"Attempting to load: {actual_drum_recording_path}")
        audio, sr = load_audio(actual_drum_recording_path, sr=SAMPLE_RATE)

        normalised_audio = normalise_audio(audio)
        normalised_max = np.max(np.abs(normalised_audio))
        assert np.isclose(normalised_max, 1.0) or np.isclose(normalised_max, 0.0), "Normalisation failed!"

        bpm = estimate_tempo(normalised_audio, sr)
        # print(f"Estimated Tempo (Tempogram-First): {int(round(bpm))} BPM")
        print(f"Loaded audio: Shape={audio.shape}, Sample Rate={sr}, Tempo={bpm:.2f}, Duration={len(audio)/sr:.2f} seconds")

        # if _prompt_user_for_playback():
          #  play_audio(normalised_audio, sr)

    except Exception as e:
        print(f"\nAn unexpected error occurred during the example execution: {e}")

# Uncomment to use, for clearer error logs
# print("\n# ------------------------------------------------------------------------------------")