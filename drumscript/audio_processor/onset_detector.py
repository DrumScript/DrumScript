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
from drumscript.notation_generator.constants import SAMPLE_RATE, SEGMENT_LENGTH_SECONDS, N_FFT, NOISE_THRESH_SNARE, DRUM_NOTATION_MAP, ONSET_SLICE_DURATION_MS, HOP_LENGTH
from drumscript.audio_processor import tempo_detector
from drumscript.audio_processor.tempo_detector import estimate_tempo
from datetime import datetime

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f'\ndate/time: {datetimestamp}')

def detect_onsets(audio_data: np.ndarray, sr: int) -> list[float]:
    """
    Detects the onset (start) times of drum hits in the audio.
    This version includes a post-processing step to filter out spurious
    onsets that occur too close together, which is common with cymbals.

    :param audio_data: The audio time series.
    :type audio_data: np.ndarray
    :param sr: The sampling rate.
    :type sr: int
    :return: A list of onset timestamps in seconds.
    :rtype: list[float]
    """
    if audio_data.size == 0:
        return []
    
    # --- 1. Extract percussive using HPSS ---
    ## HPSS: HARMONIC PERCUSSIVE SOURCE-SEPARATION  

    ## Harmonic-Percussive Source Separation (HPSS), we first split the audio into two separate tracks: one containing only the harmonic ringing and another containing only the percussive attack. Then, we onset detector runs on the PERCUSSIVE track only. 
    ### [TO DO]??? Maybe this is not so important when the user inputted-audio is specifically drum only? Or maybe it would be more useful doing this in stem_splitter.py, ie when the input audio contains more than the drums??
    ### The result of using the PERCUSSIVE element only is to create a new audio signal that only contains the percussive elements; then, any `harmonic` 'noise/ringing' (ie which COULD cause false positives) is filtered out. It should produce a cleaner audio output to which apply the function. 

    y_percussive = librosa.effects.percussive(y=audio_data)

    # We must convert seconds to "frames" because librosa 'wait' expects frames.
    # (Assuming HOP_LENGTH is imported from constants)
    # min_gap_seconds = 0.10  # 100ms
    # wait_frames = int(min_gap_seconds * (sr / HOP_LENGTH))

    # --- 2. Onset detection
    # Now, we run the same onset detection, but on the much cleaner
    # percussive signal. This allows us to get a precise detection
    # of the initial hit without interference from the sustain.

    # --- 2. Advanced Onset Strength Envelope (SuperFlux) ---
    # We use a lag-rectified spectral flux to avoid false positives from energy fluctuations
    onset_env = librosa.onset.onset_strength(
        y=y_percussive, 
        sr=sr, 
        hop_length=HOP_LENGTH,
        aggregate=np.median # Using median to suppress noise spikes
    )

    # --- 3. Peak Picking Parameters ---
    # Lockout period: 100ms (0.1s) is standard for drums to prevent double triggers
    # min_gap_seconds = 0.1 
    # wait_frames = int(min_gap_seconds * (sr / HOP_LENGTH))

    # --- UPDATED DETECTION METHOD: Direct Peak Picking ---
    # Instead of using the generic 'onset_detect' wrapper, we use 'peak_pick' directly.
    # This addresses the "vague" nature of the default function by giving us exact control
    # over the sliding window.
    
    # pre_max / post_max: These replace the "wait" logic. 
    # They say: "A peak is only a peak if it is the maximum value within X frames."
    # 30ms is roughly 1/32nd note at fast tempos. It prevents the double-trigger on a kick
    # (because the second wobble is smaller than the first peak), but allows fast rolls.
    window_secs = 0.03 # 30ms window
    window_frames = int(window_secs * (sr / HOP_LENGTH))
    print(f'\n(window_frames: {window_frames})')
    
    onset_frames = librosa.util.peak_pick(
        onset_env,
        pre_max=window_frames,      # Must be max value in previous ~30ms
        post_max=window_frames,     # Must be max value in subsequent ~30ms
        pre_avg=window_frames,      # Compare against average of previous ~30ms
        post_avg=window_frames,     # Compare against average of subsequent ~30ms
        delta=0.07,                 # Adaptive threshold (sensitivity)
        wait=1                      # Minimal wait (just 1 frame) to avoid mathematical overlap
    )

    # onset_frames = librosa.onset.onset_detect(
#       onset_envelope=onset_env,
    #    y=y_percussive,  # Use the percussive-only signal
    #    sr=SAMPLE_RATE,
        # sr = sr
        # units='time',
        # units='frames',
        # delta=0.07,
        # backtrack=True
        # wait=wait_frames
        # wait=1,
        # pre_avg=8,
        # post_avg=8,
        # backtrack=True
    # )

    # --- 4. Backtracking ---
    # Peak picking finds the *top* of the peak. We want the *start* of the drum hit.
    # Backtracking walks backwards from the peak to find where the energy started rising.
    
    # SAFETY CHECK: If no onsets are found, backtracking will crash.
    if len(onset_frames) > 0:
        onset_frames = librosa.onset.onset_backtrack(onset_frames, onset_env)

    onset_times = librosa.frames_to_time(onset_frames, sr=SAMPLE_RATE) # onset_time is in seconds, *1000 to get ms. This is fed into final output .json when transcription is run

    return onset_times.tolist() 

#------- AUTOMATIC TEMPO DETECTION------------------------------------
# REPLACED THE FUNCTION THAT WAS HARDCODED TO DETECT TEMPO FROM ONSETS WITH IMPORTED FCT FROM THE TEMPO_DETECTOR SCRIPT

def calculate_tempo_from_onsets(onset_times: np.ndarray, sr: int) -> float:
    """
    Estimates the tempo (BPM) from a list of onset timestamps.

    :param onset_times: Array of onset timestamps in seconds.
    :type onset_times: np.ndarray
    :param sr: The sampling rate.
    :type sr: int
    :return: The estimated tempo in BPM.
    :rtype: float
    """
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

#----------------------------------------------------------------------


if __name__ == "__main__":
    from drumscript.audio_processor.audio_loader import load_audio, normalise_audio
    print("\n#=======================================================================================")
    #print("Running onset_detector.py example with test.wav/test.mp3...")
    print("Running onset_detector.py example with provided filepath...") # FUTURE: Find way to encode this so it prints the file path provided in CLI
    try:

        # Import necessary modules from your package
        # Note: You might need 'from DrumScript.audio_processor.audio_loader import ...'
        # if running this script directly and 'audio_processor' is not in the Python path.
        # However, for 'python -m' style execution, 'from audio_processor.audio_loader import ...' is usually correct.

        # --- CLI ARGUMENT PARSING FIX ---
        parser = argparse.ArgumentParser(description="Detect onsets in drum audio.")
        parser.add_argument("input_audio", help="Path to the input audio file")
        args = parser.parse_args()

        # sr = 44100 # Target sample rate for processing
        #sr = 44100*1.5 # Target sample rate for processing
        sr = SAMPLE_RATE
        print(f'sample_rate=sr={sr}') # Print current sample rate applied

        # --- Path to your actual drum recording/audio (test.wav/test.mp3) ---
        # This dynamic path calculation should correctly point to DRUMSCRIPT/test_audio/test.wav
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f'current_script_dir: {current_script_dir}')
        # Go up one level from audio_processor/onset_detector.py to the outer DRUMSCRIPT/ folder
        project_root = os.path.abspath(os.path.join(current_script_dir, '..', '..'))
        print(f'project_root: {project_root}')

        # Construct the path to test.mp3/test.wav within the 'test_audio' directory
        #test_audio_path = os.path.join(project_root, "test_audio", "SCHAMMASCH-Split-My-Tongue.mp3") # Change .mp3 to .wav if using WAV, or other audio format
        # test_audio_path = os.path.join(project_root, "test_audio", "test.wav") # Change .wav to .mp3 if using MP3, or other audio format

        # USE CLI ARGUMENT PATH INSTEAD OF HARDCODED
        test_audio_path = os.path.abspath(args.input_audio)

        print(f'test_audio_path: {test_audio_path}')
        print(f"Attempting to load: {test_audio_path}")
        
        # Load and normalise the test.mp3/test.wav audio
        # audio_data, sample_rate = load_audio(test_audio_path, sr=sr)
        audio_data, sample_rate = load_audio(test_audio_path, sr=SAMPLE_RATE)
        normalised_audio = normalise_audio(audio_data)

        # Detect onsets from test.mp3/test.wav
        #print("\nDetecting onsets from test.mp3/test.wav...")
        onsets = detect_onsets(normalised_audio, sample_rate)
        print(f"Detected {len(onsets)} onsets.")

        if onsets:
            # Print the first few detected onsets for verification
            #print("\nFirst 10 detected onsets (seconds):")
            #for i, onset_time in enumerate(onsets[:10]):
            #if len(onsets) > 10:
             #   print(f"  ...and {len(onsets) - 10} more onsets.")
            
            # Print * (ALL) detected onsets for now
            print(f"\n All {len(onsets)} detected onsets (seconds):")
            #for i, onset_time in enumerate(onsets):
             #   print(f"  Onset {i+1}: {onset_time:.2f}s")
            for i, onset_time in enumerate(onsets):
                print(f"  Onset {i+1}: {onset_time:.4f}s")
        else:
            print("No onsets detected in test.mp3/test.wav.")
        print(f"Loaded audio: Shape={normalised_audio.shape}, Sample Rate={sample_rate}, Duration={len(normalised_audio)/sample_rate:.2f} seconds, Tempo={calculate_tempo_from_onsets(onsets, sr=SAMPLE_RATE):2f}")
    except FileNotFoundError:
        print(f"\nERROR: The audio file '{test_audio_path}' was not found.")
        print("Please ensure you have placed 'test.mp3/test.wav' inside your 'DrumScript/test_audio/' directory.")
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