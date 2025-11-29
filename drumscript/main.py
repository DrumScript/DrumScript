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
# from datetime import datetime

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')


def main(input_audio_path: str, transcribe_full_song: bool = False, time_signature: str = "4/4"):
    print(f"\n--- Starting DrumScript ---")
    print(f"Target: {input_audio_path}")

    try:
        # 1. Pre-processing
        audio_path = input_audio_path
        if transcribe_full_song:
            try:
                print("...Separating drum stem...")
                audio_path = extract_drum_stem(input_audio_path)
            except Exception as e:
                print(f"Stem separation failed: {e}")
                return

        # 2. Analysis Pipeline
        print("...Loading & Analyzing Audio...")
        y, sr = audio_loader.load_audio(audio_path)
        y = audio_loader.normalise_audio(y) 
        
        tempo = tempo_detector.estimate_tempo(y, sr)
        onsets = onset_detector.detect_onsets(y, sr)
        
        print(f"   -> Detected Tempo: {tempo:.1f} BPM")
        print(f"   -> Detected Onsets: {len(onsets)}")

        # 3. Classification
        print("...Classifying Events (Multi-Band)...")
        # Pass raw audio for polyphonic analysis
        classified_events = classify.classify_drum_hits(y, sr, onsets)
        print(f"   -> Classified {len(classified_events)} events")

        # 4. Score Formatting
        final_events = []
        for event in classified_events:
            final_events.append({
                'time': event['onset_time_seconds'],
                'drums': [event['drum_type']],
                'analysis': event['analysis']
            })

        # 5. Output Generation
        output_filename = f"{Path(input_audio_path).stem}_transcription"
        final_pdf_path = f"outputs/{output_filename}.pdf" 
        
        print(f"...Building Score: {final_pdf_path}...")
        
        # This saves the single master JSON and PDF
        score_builder.build_and_export_drum_score(
            detected_events=final_events, 
            tempo=tempo, 
            output_filepath=final_pdf_path,
            time_signature=time_signature
        )

        print("--- Done! ---\n")
        
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("input_audio_path", type=str)
    parser.add_argument("--full", action="store_true")
    parser.add_argument("--ts", type=str, default="4/4")
    args = parser.parse_args()
    
    main(args.input_audio_path, args.full, args.ts)
    
# print("# ------------------------------------------------------------------------------------")