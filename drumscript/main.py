# drumscript/main.py
import shutil
from pathlib import Path
import os
import sys
import json # Needed for saving the analysis file
from drumscript.audio_processor.stem_splitter import extract_drum_stem
from drumscript.audio_processor import audio_loader, onset_detector, feature_extractor, tempo_detector
from drumscript.drum_classifier import predict
from drumscript.notation_generator import score_builder, pdf_exporter
from datetime import datetime
# Logging imports removed

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f'\ndate/time: {datetimestamp}')

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
        # The onset_detector.detect_onsets function returns TIMESTAMPS (seconds), not frames.
        onset_times = onset_detector.detect_onsets(y, sr)
        print(f"Found {len(onset_times)} onset events.")

        # 5. EXTRACT FEATURES
        print("Extracting features for each onset...")
        # Pass the onset timestamps directly to feature extractor
        features = feature_extractor.extract_features_for_onsets(y, sr, onset_times)
        
        # 6. CLASSIFY HITS (Rule-Based Engine)
        print("Classifying drum hits...")
        # predict.py returns a list of event dictionaries that ALREADY contain the 'onset_time_seconds'
        raw_classified_events = predict.predict_drum_hits(features)

        # --- NEW: Save Classification Analysis for Accuracy Tuning ---
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        json_output_path = os.path.join(output_dir, "prediction_output.json")
        
        print(f"Saving classification analysis to {json_output_path}...")
        try:
            with open(json_output_path, 'w') as f:
                json.dump(raw_classified_events, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not save prediction_output.json: {e}")
        # -------------------------------------------------------------

        # 7. FORMAT EVENTS FOR SCORE BUILDER
        print("Formatting events for score builder...")
        # Convert the classifier output to the format score_builder expects: {'time': float, 'drums': [str]}
        final_classified_events = []
        
        for event in raw_classified_events:
            final_classified_events.append({
                'time': event['onset_time_seconds'],
                'drums': [event['drum_type']] # score_builder expects a list of drum types
            })
                
        print(f"Successfully prepared {len(final_classified_events)} detected drum events.")
        
        # 8. BUILD AND EXPORT SCORE
        print("Building and exporting music score...")

        # Define the final output path
        output_filename = f"{Path(input_audio_path).stem}_transcription"
        final_pdf_path = f"outputs/{output_filename}.pdf" 

        print(f"Exporting score to {final_pdf_path} (and .musicxml)...")

        # Pass all arguments to the combined score builder and exporter function.
        score_builder.build_and_export_drum_score(
            detected_events=final_classified_events, 
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