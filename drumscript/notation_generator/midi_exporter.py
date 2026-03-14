# DrumScript/notation_generator/midi_exporter.py
"""
This module takes classified drum events and renders them into a standard MIDI file.

Uses event['time'] and event['drums'].
"""
import os
import argparse
import pretty_midi
from drumscript.notation_generator.constants import DRUM_NOTATION_MAP
# from datetime import datetime

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')


def export_to_midi(classified_events: list[dict], output_filepath: str, tempo: float = 120.0):
    """
    Takes a list of event dictionaries and writes a standard .mid file.
    
    :param classified_events: List of dicts containing 'time' and 'drums'.
    :param output_filepath: Where to save the file (e.g., 'output/drum_score.mid').
    :param tempo: The detected BPM of the track.
    """
    # 1. Initialize a new midi object with the detected tempo
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    
    # 2. Create a Drum Track (program=0, is_drum=True forces it to MIDI Channel 10)
    drum_track = pretty_midi.Instrument(program=0, is_drum=True, name="DrumScript Output")
    
    # 3. Loop through your beautifully classified timeline
    for event in classified_events:
        # ADAPTED KEYS: Using 'time' and 'drums' to match score_builder format
        time_sec = event["time"]
        instruments = event["drums"]
        
        # Multiple instruments can hit at the exact same millisecond!
        for inst in instruments:
            # Check if our physics engine spit out an instrument we have in our map
            if inst in DRUM_NOTATION_MAP:
                midi_pitch = DRUM_NOTATION_MAP[inst]['midi_program']
                
                # Create the MIDI Note.
                # (Drums don't hold sustain, so a 0.1s duration is standard for sheet music)
                note = pretty_midi.Note(
                    velocity=100,             # Default strong hit
                    pitch=midi_pitch,         # E.g., 36 for Kick, 38 for Snare
                    start=time_sec,           # The exact millisecond from onset_detector
                    end=time_sec + 0.1        
                )
                
                drum_track.notes.append(note)
            else:
                # If the classifier guessed 'unknown', we skip it for the clean score
                pass
                
    # 4. Add the finished track to the file and save it
    midi.instruments.append(drum_track)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    midi.write(output_filepath)
    
    print(f"SUCCESS: MIDI file generated at -> {output_filepath}")


# --------------------------------------


if __name__ == "__main__":
    from drumscript.audio_processor.audio_loader import load_audio, normalise_audio
    # from drumscript.audio_processor import tempo_detector
    from drumscript.audio_processor.tempo_detector import estimate_tempo
    from drumscript.notation_generator.constants import DRUM_NOTATION_MAP

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
        tempo = estimate_tempo(audio_data, SAMPLE_RATE)
        # tempo = estimate_tempo(audio_data, SAMPLE_RATE)/2 # temporary fix
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