# drumscript/main.py
import shutil
from pathlib import Path
import os
import sys
from drumscript.audio_processor.stem_splitter import extract_drum_stem
from drumscript.audio_processor import audio_loader, onset_detector, feature_extractor, tempo_detector
from drumscript.drum_classifier import predict
from drumscript.notation_generator import score_builder, pdf_exporter
# Logging imports removed

print("# ------------------------------------------------------------------------------------")

def main(input_audio_path: str, transcribe_full_song: bool = False):
    """
    Main orchestration script for the DrumScript transcription pipeline.

    Args:
        input_audio_path (str): Path to the audio file to process.
        transcribe_full_song (bool): 
            If True, treat input as a full song and run stem separation.
            If False (default), assume input is already a drum-only track.
    """
    
    print(f"--- Starting DrumScript transcription for: {input_audio_path} ---")

    temp_drum_file_path = None
    temp_output_dir = None

    try:
        # 2. Add the new pre-processing step
        if transcribe_full_song:
            try:
                # 1. SEPARATE DRUM STEM
                print("Full song mode: Separating drum stem...")
                temp_drum_file_path = extract_drum_stem(input_audio_path)
                
                temp_output_dir = Path(temp_drum_file_path).parent.parent.parent
                
                print(f"Drum stem extracted to: {temp_drum_file_path}")
                
                audio_to_process = temp_drum_file_path
                
            except (RuntimeError, FileNotFoundError) as e:
                print(f"Failed to separate drum stem: {e}")
                return # Exit if separation fails
        else:
            print("Drum-only mode: Processing file directly.")
            audio_to_process = input_audio_path

        # 2. LOAD AUDIO
        print(f"Loading audio from: {audio_to_process}")
        y, sr = audio_loader.load_audio(audio_to_process)

        # 3. DETECT TEMPO
        estimated_tempo = tempo_detector.estimate_tempo(y, sr)
        print(f"Estimated tempo: {estimated_tempo:.2f} BPM")

        # 4. DETECT ONSETS
        print("Detecting onsets...")
        detected_onsets = onset_detector.detect_onsets(y, sr)
        print(f"Found {len(detected_onsets)} onset events.")

        # 5. EXTRACT FEATURES
        print("Extracting features for each onset...")
        features = feature_extractor.extract_features_for_onsets(y, sr, detected_onsets)
        
        # 6. CLASSIFY HITS (Rule-Based Engine)
        print("Classifying drum hits...")
        classified_events = predict.predict_drum_hits(features)

        # We must now combine the classification results with their timestamps
        # before passing them to the score builder.
        
        print("Converting onset frames to timestamps...")
        # Convert frame indices (e.g., [500, 1000]) to seconds (e.g., [11.6, 23.2])
        onset_times_sec = onset_detector.detected_onsets(detected_onsets, sr=sr)

        # Ensure we have the same number of timestamps as classified hits
        if len(onset_times_sec) != len(classified_events):
            print(f"Error: Mismatch in onset times ({len(onset_times_sec)}) and classified hits ({len(classified_events)})")
            return 

        # Build the final 'classified_events' list in the format score_builder expects
        print("Combining timestamps and classified hits...")
        classified_events = []
        for i in range(len(onset_times_sec)):
            time_sec = onset_times_sec[i]
            drum_types = classified_events[i]
            
            # Only add events that actually have drum hits (not empty classifications)
            if drum_types: 
                classified_events.append({
                    'time': time_sec,
                    'drums': drum_types
                })
                
        print(f"Successfully combined {len(classified_events)} detected drum events with timestamps.")
        
        # 7. & 8. BUILD AND EXPORT SCORE
        print("Building and exporting music score...")

        # Define the final output path
        output_filename = f"{Path(input_audio_path).stem}_transcription"
        final_pdf_path = f"outputs/{output_filename}.pdf" 

        print(f"Exporting score to {final_pdf_path} (and .musicxml)...")

        # Pass all arguments to the combined score builder and exporter function.
        score_builder.build_and_export_drum_score(
            detected_events=classified_events, 
            tempo=estimated_tempo, 
            output_filepath=final_pdf_path  
        )

        print(f"--- Transcription complete for: {input_audio_path} ---")
        
    except Exception as e:
        # Replaced logger.error with print
        print(f"An unexpected error occurred in the pipeline: {e}")
        # If you want the full error traceback, uncomment the next two lines
        # import traceback
        # traceback.print_exc()

if __name__ == '__main__':
    # This allows testing the feature from the command line.
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_audio_file> [--full]")
        sys.exit(1)
        
    input_path = sys.argv[1]
    
    # Check if the '--full' flag is present
    run_as_full_song = '--full' in sys.argv
    
    main(input_path, transcribe_full_song=run_as_full_song)

print("# ------------------------------------------------------------------------------------")