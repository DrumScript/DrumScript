# drumscript/main.py
import shutil
from pathlib import Path
import os
import sys
import json
import argparse
from drumscript.audio_processor.stem_splitter import extract_drum_stem
from drumscript.audio_processor import audio_loader, onset_detector, feature_extractor, tempo_detector
from drumscript.drum_classifier import classify
from drumscript.notation_generator import score_builder
from datetime import datetime

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')

def main(input_audio_path: str, transcribe_full_song: bool = False, time_signature: str = "4/4"):
    """
    Main orchestration script.
    Now accepts a time_signature argument (e.g., "4/4", "3/4", "6/8").
    """
    
    print(f"--- Starting DrumScript transcription for: {input_audio_path} ---")
    print(f"Settings: Time Signature = {time_signature}")

    temp_drum_file_path = None

    try:
        # 1. PRE-PROCESSING
        if transcribe_full_song:
            try:
                print("Full song mode: Separating drum stem...")
                temp_drum_file_path = extract_drum_stem(input_audio_path)
                print(f"Drum stem extracted to: {temp_drum_file_path}")
                audio_to_process = temp_drum_file_path
            except (RuntimeError, FileNotFoundError) as e:
                print(f"Failed to separate drum stem: {e}")
                return 
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
        onset_times = onset_detector.detect_onsets(y, sr)
        print(f"Found {len(onset_times)} onset events.")

        # 5. EXTRACT FEATURES
        print("Extracting features for each onset...")
        features = feature_extractor.extract_features_for_onsets(y, sr, onset_times)
        
        # 6. CLASSIFY HITS
        print("Classifying drum hits...")
        raw_classified_events = classify.predict_drum_hits(features)

        # Save Analysis
        output_dir = "outputs"
        os.makedirs(output_dir, exist_ok=True)
        json_output_path = os.path.join(output_dir, "prediction_output.json")
        try:
            with open(json_output_path, 'w') as f:
                json.dump(raw_classified_events, f, indent=4)
        except Exception as e:
            print(f"Warning: Could not save prediction_output.json: {e}")

        # 7. FORMAT EVENTS
        print("Formatting events for score builder...")
        final_classified_events = []
        
        for event in raw_classified_events:
            final_classified_events.append({
                'time': event['onset_time_seconds'],
                'drums': [event['drum_type']] 
            })
        
        # 8. BUILD AND EXPORT SCORE (With Time Signature)
        print("Building and exporting music score...")

        output_filename = f"{Path(input_audio_path).stem}_transcription"
        final_pdf_path = f"outputs/{output_filename}.pdf" 

        print(f"Exporting score to {final_pdf_path}...")

        score_builder.build_and_export_drum_score(
            detected_events=final_classified_events, 
            tempo=estimated_tempo, 
            output_filepath=final_pdf_path,
            time_signature=time_signature  # Pass the string "4/4", "3/4" etc.
        )

        print(f"--- Transcription complete for: {input_audio_path} ---")
        
    except Exception as e:
        print(f"An unexpected error occurred in the pipeline: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="DrumScript: Audio to Sheet Music")
    parser.add_argument("input_audio_path", type=str, help="Path to the audio file")
    parser.add_argument("--full", action="store_true", help="Process full song (separate stems)")
    parser.add_argument("--ts", type=str, default="4/4", help="Time Signature (e.g. '4/4', '3/4', '6/8')")     # Added new --ts argument for Time Signature
    
    args = parser.parse_args()
    
    main(args.input_audio_path, 
         transcribe_full_song=args.full,
         time_signature=args.ts)

# print("# ------------------------------------------------------------------------------------")