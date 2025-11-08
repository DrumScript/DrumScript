# DrumScript/audio_processor/onset_detector.py
"""
This module will detect the onset (start) times of drum hits in the audio.
"""
import librosa
import numpy as np
import os
import soundfile
import argparse # for command-line argument parsing



def detect_onsets(audio_data: np.ndarray, sr: int) -> list[float]:
    """
    Detects the onset (start) times of drum hits in the audio.
    This version includes a post-processing step to filter out spurious
    onsets that occur too close together, which is common with cymbals.
    """
    if audio_data.size == 0:
        return []
    
    # --- 1. Separate the Percussive Component ---
    # USES HPSS: HARMONIC PERCUSSIVE SOURCE-SEPARATION  

    # NOTE (REMOVE LATER):
    #Harmonic-Percussive Source Separation (HPSS), we can first split the audio into two separate tracks: one #containing only the harmonic ringing and another containing only the percussive attack. Then, we can run #our sensitive onset detector on the percussive track only.


    # This is the key step. We create a new audio signal that only
    # contains the percussive elements. The harmonic ringing that was
    # causing false positives is filtered out.
    y_percussive = librosa.effects.percussive(y=audio_data)

    # --- 2. Run Onset Detection on the Percussive Signal ---
    # Now, we run the same onset detection, but on the much cleaner
    # percussive signal. This allows us to get a precise detection
    # of the initial hit without interference from the sustain.
    onset_frames = librosa.onset.onset_detect(
        y=y_percussive,  # Use the percussive-only signal
        sr=sr,
        units='frames',
        delta=0.01,       # The sensitive delta is now effective and safe to use
        wait=1,
        pre_avg=8,
        post_avg=8,
        backtrack=True
    )

    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    return onset_times.tolist()

"""   COMMENTING OUT (OLD) REFRACTORY PERIOD LOGIC FOR NOW (BUT KEEPING (FOR NOW))
# --- 1. Initial Onset Detection (with sensitive delta) ---
    onset_frames = librosa.onset.onset_detect(
        y=audio_data,
        sr=sr,
        units='frames',
        delta=0.1,   # Keep the sensitive delta to catch the initial hit
        wait=1,
        pre_avg=8,
        post_avg=8,
        backtrack=True
    )
    onset_times = librosa.frames_to_time(onset_frames, sr=sr)

    if onset_times.size == 0:
        return []

    # --- 2. Post-Processing: Filter out double-detections ---
    # Define a refractory period: a minimum time between valid onsets.
    # 150ms is a good starting point for preventing double-triggers on a single hit.
    refractory_period_seconds = 0.15

    # The first detected onset is always considered valid.
    final_onsets = [onset_times[0]]

    # Iterate through the rest of the onsets
    for i in range(1, len(onset_times)):
        # Calculate the time difference between the current onset and the last *accepted* onset
        time_since_last_onset = onset_times[i] - final_onsets[-1]

        # If the time difference is greater than our refractory period, it's a new, valid hit.
        if time_since_last_onset >= refractory_period_seconds:
            final_onsets.append(onset_times[i])
        # Otherwise, it's likely part of the previous hit's sustain, so we ignore it.

    return final_onsets
"""

#-------NEW FCT AUTOMATIC TEMPO DETECTION---- TO BE REVIEWED/.TESTED

def calculate_tempo_from_onsets(onset_times: np.ndarray, sr: int) -> float:
    """
    Estimates the tempo (BPM) from a list of onset timestamps.

    Args:
        onset_times (np.ndarray): An array of timestamps for detected onsets.
        sr (int): The sample rate of the audio.

    Returns:
        float: The estimated tempo in beats per minute (BPM).
    """
    if len(onset_times) < 2:
        return 120.0 # Return a default tempo if not enough onsets are found

    # Estimate tempo from the onset timestamps
    tempo = librosa.beat.tempo(onset_envelope=None, sr=sr, onset_events=onset_times)
    
    # librosa.beat.tempo returns an array, we'll take the first (most likely) value
    return tempo[0]

#----------------------------------------------------------------------


if __name__ == "__main__":
    from drumscript.audio_processor.audio_loader import load_audio, normalise_audio
    print("\n#=======================================================================================")
    #print("Running onset_detector.py example with test.wav/test.mp3...")
    print("Running onset_detector.py example with provided filepath...") # FUTURE: Find way to encode this so it prints the file path provided in CLI
    try:

        # Import necessary modules from your package
        # Note: You might need 'from DrumScript.audio_processor.audio_loader import ...'
        # if running this script directly and 'audio_processor' is not in the Python path.
        # However, for 'python -m' style execution, 'from audio_processor.audio_loader import ...' is usually correct.

        sr = 44100 # Target sample rate for processing
        #sr = 44100*1.5 # Target sample rate for processing
        print(f'sample_rate=sr={sr}') # Print current sample rate applied

        # --- Path to your actual drum recording/audio (test.wav/test.mp3) ---
        # This dynamic path calculation should correctly point to DRUMSCRIPT/test_audio/test.wav
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        print(f'current_script_dir: {current_script_dir}')
        # Go up one level from audio_processor/onset_detector.py to the outer DRUMSCRIPT/ folder
        project_root = os.path.abspath(os.path.join(current_script_dir, '..', '..'))
        print(f'project_root: {project_root}')

        # Construct the path to test.mp3/test.wav within the 'test_audio' directory
        #test_audio_path = os.path.join(project_root, "test_audio", "SCHAMMASCH-Split-My-Tongue.mp3") # Change .mp3 to .wav if using WAV, or other audio format
        test_audio_path = os.path.join(project_root, "test_audio", "test.wav") # Change .wav to .mp3 if using MP3, or other audio format
        print(f'test_audio_path: {test_audio_path}')
        print(f"Attempting to load: {test_audio_path}")

        # Load and normalise the test.mp3/test.wav audio
        audio_data, sample_rate = load_audio(test_audio_path, sr=sr)
        normalised_audio = normalise_audio(audio_data)
        print(f"Loaded audio: Shape={normalised_audio.shape}, Sample Rate={sample_rate}, Duration={len(normalised_audio)/sample_rate:.2f} seconds")

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
        else:
            print("No onsets detected in test.mp3/test.wav.")

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
    print("\n-----------------------------------------------------")