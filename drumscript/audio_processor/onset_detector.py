# DrumScript/audio_processor/onset_detector.py
"""
This module will detect the onset (start) times of drum hits in the audio.
"""
import os
import sys
import librosa
import numpy as np
import soundfile
import argparse
from drumscript.notation_generator.constants import SAMPLE_RATE, HOP_LENGTH
# from drumscript.audio_processor import tempo_detector
from drumscript.audio_processor.tempo_detector import estimate_tempo
from datetime import datetime

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f'\ndate/time: {datetimestamp}')
def detect_onsets(audio_data: np.ndarray, sr: int) -> list[float]:
    
    #Detects the onset (start) times of percussive events in an audio signal.

    #This function uses librosa's built-in onset detection algorithms, which
    # typically rely on spectral flux or other energy-based methods to identify
    # sudden changes in the audio signal characteristic of percussive hits.

    #Args:
     #   audio_data (np.ndarray): The input audio time series.
     #   sr (int): The sample rate of the audio data.

    #Returns:
     #   list[float]: A list of detected onset times in seconds.

    if audio_data.size == 0:
        return []

    y_percussive = librosa.effects.percussive(y=audio_data)

    # --- ENFORCE PHYSICAL DRUMMING LIMITS ---
    # Because HOP_LENGTH is 128, the frames are very tiny (~2.9ms).
    # We must explicitly tell Librosa to wait at least 50ms before triggering 
    # a second hit, otherwise it will trigger on cymbal vibrations.
    lockout_time_secs = 0.05 
    wait_frames = int(lockout_time_secs * (SAMPLE_RATE / HOP_LENGTH))

    print(f"(HOP_LENGTH: {HOP_LENGTH})")
    print(f"(Wait Frames Applied: {wait_frames})")

    # Pass the 'wait' and 'delta' constraints directly into the simple wrapper
    onset_frames = librosa.onset.onset_detect(
        y=y_percussive, 
        sr=SAMPLE_RATE,
        hop_length=HOP_LENGTH,
        units='frames',
        wait=wait_frames,  # Stops rapid double-triggering on cymbals
        delta=0.05         # Ignores general background noise floor
    )
    
    print(f'(len_onset_frames:{len(onset_frames)})')

    # Convert onset frames to time in seconds
    onset_times = librosa.frames_to_time(
        onset_frames, 
        sr=SAMPLE_RATE,
        hop_length=HOP_LENGTH
    )
    
    print(f'(len_onset_times:{len(onset_times)})')

    return onset_times.tolist()



#------- AUTOMATIC TEMPO DETECTION------------------------------------
# REPLACED THE FUNCTION THAT WAS HARDCODED TO DETECT TEMPO FROM ONSETS WITH IMPORTED FCT FROM THE TEMPO_DETECTOR SCRIPT

"""
def calculate_tempo_from_onsets(onset_times: np.ndarray, sr: int) -> float:
    #
    #Estimates the tempo (BPM) from a list of onset timestamps.

   # :param onset_times: Array of onset timestamps in seconds.
    #:type onset_times: np.ndarray
    #:param sr: The sampling rate.
    #:type sr: int
    #:return: The estimated tempo in BPM.
    #:rtype: float
    #
    if len(onset_times) < 2:
        return 120.0 # Return a default tempo if not enough onsets are found

    # FIX: librosa.beat.tempo does NOT accept 'onset_events' without audio/envelope.
    # We calculate tempo using Inter-Onset Intervals (IOI).
    
    # 1. Calculate the time difference between consecutive hits
    ioi = np.diff(onset_times)
    
    # 2. Filter out extremely short or long gaps (e.g., fast rolls or long pauses)
    # 0.2s = 300 BPM, 1.5s = 40 BPM
    valid_ioi = ioi[(ioi > 0.2) & (ioi < 1.5)]
    
    if len(valid_ioi) > 0:
        # 3. Take the median interval (median is better than average as it ignores outliers)
        avg_interval = np.median(valid_ioi)
        tempo = 60.0 / avg_interval
    else:
        tempo = 120.0 # Default if pattern is weird or too sparse

    return float(tempo)

"""


#----------------------------------------------------------------------


if __name__ == "__main__":
    from drumscript.audio_processor.audio_loader import load_audio, normalise_audio
    # from drumscript.audio_processor import tempo_detector x 
    from drumscript.audio_processor.tempo_detector import estimate_tempo
    print("\n#=======================================================================================")
    print("Running onset_detector.py example with provided filepath...") # FUTURE: Find way to encode this so it prints the file path provided in CLI
    try:

        # Import necessary modules from your package
        # Note: You might need 'from DrumScript.audio_processor.audio_loader import ...'
        # if running this script directly and 'audio_processor' is not in the Python path.
        # However, for 'python -m' style execution, 'from audio_processor.audio_loader import ...' is usually correct.

        # Required for CLI argparsing
        parser = argparse.ArgumentParser(description="Detect onsets in drum audio.")
        parser.add_argument("input_audio", help="Path to the input audio file")
        args = parser.parse_args()

        # sr = 44100 # Target sample rate for processing
        #sr = 44100*1.5 # Target sample rate for processing
        sr = SAMPLE_RATE
        print(f'sample_rate=sr={sr}') # Print current sample rate applied

        # --- Get path to audio (cli or import from sister module)
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f'current_script_dir: {current_script_dir}')
        # Go up one level from audio_processor/onset_detector.py to the outer DRUMSCRIPT/ folder
        project_root = os.path.abspath(os.path.join(current_script_dir, '..', '..'))
        print(f'project_root: {project_root}')
        audio_path = os.path.abspath(args.input_audio)

        print(f'audio_path: {audio_path}')
        print(f"Attempting to load: {audio_path}")
        
        # Load and normalise audio
        # audio_data, sample_rate = load_audio(audio_path, sr=sr)
        audio_data, sample_rate = load_audio(audio_path, sr=SAMPLE_RATE)
        normalised_audio = normalise_audio(audio_data)

        # Detect onsets
        print(f"Detecting onsets in : {audio_path}")
        onsets = detect_onsets(normalised_audio, SAMPLE_RATE)
        print(f"Detected {len(onsets)} onsets.")

        if onsets:
            # Print the first few detected onsets for verification
            #print("\nFirst 10 detected onsets (seconds):")
            #for i, onset_time in enumerate(onsets[:10]):
            #if len(onsets) > 10:
             #   print(f"  ...and {len(onsets) - 10} more onsets.")
            
            # Print * (ALL) detected onsets for now
            print(f"\n All {len(onsets)} detected onsets (seconds):")
            for i, onset_time in enumerate(onsets):
             print(f"  Onset {i+1}: {onset_time:.4f}s")
            #for i, onset_time in enumerate(onsets):
            #print(f"  Onset {i+1}: {onsets:.4f}s")
        else:
            print(f"No onsets detected in audio_path: {audio_path}")
       #global_tempo = estimate_tempo(audio_data, SAMPLE_RATE, HOP_LENGTH)
        #tempo = estimate_tempo(audio_data, SAMPLE_RATE, HOP_LENGTH)
        tempo = estimate_tempo(audio_data, SAMPLE_RATE)/2 # temporary fix
        #tempo = estimate_tempo(audio_data, SAMPLE_RATE)/4 # temporary fix
        #print(f"Loaded audio: Shape={normalised_audio.shape}, Sample Rate={sample_rate}, Duration={len(normalised_audio)/sample_rate:.2f} seconds, Tempo={calculate_tempo_from_onsets(onsets, sr=SAMPLE_RATE):2f}")
        print(f"Loaded audio: Shape={normalised_audio.shape}, Sample Rate={sample_rate} (Hz), Hop Length={HOP_LENGTH} (Hz), Duration={len(normalised_audio)/sample_rate:.2f} seconds, Tempo={tempo:.2f} BPM")
    except FileNotFoundError:
        print(f"\nERROR: The audio file '{audio_path}' was not found.")
        print(f"\nPlease ensure you have provided the correct path to your audio file: {audio_path}")
    except ImportError as e:
        print(f"\nERROR: Required modules/libraries might be missing or imports are incorrect: {e}")
        print("Ensure 'soundfile', 'librosa', 'numpy', and your DrumScript modules are correctly installed and structured.")
        print("For MP3, 'ffmpeg' must also be installed on your system and accessible in PATH.")
    except Exception as e:
        print(f"\nAn unexpected error occurred during the example execution: {e}")
        import traceback
        traceback.print_exc() # Print full traceback for debugging

    print("\nonset_detector.py example finished.")
# Uncomment to use, for clearer error logs
# print("\n# ------------------------------------------------------------------------------------")
    # LEGACY CODE:
        # --- 2. Onset detection
    # Now, we run the same onset detection, but on the much cleaner
    # percussive signal. This allows us to get a precise detection
    # of the initial hit without interference from the sustain.
    
    #  Changed units from 'frames' to 'time' to get seconds directly.
    # This removes the need for the subsequent librosa.frames_to_time conversion.
    # onset_times = librosa.onset.onset_detect(
      #   y=y_percussive,  # Use the percussive-only signal
      #  sr=SAMPLE_RATE,
      #  units='time',       # Request output directly in seconds (float)
        #delta=0.0095,       # The sensitive delta is now effective and safe to use
        #wait=1,
      #  pre_avg=8,
      #  post_avg=8,
      #  backtrack=True
    #)