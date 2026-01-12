# drumscript/main.py
"""
This job of this script is to orchestrate the End-to-End running of DrumScript modules
"""
import shutil
import os
import sys
import json
import argparse
from pathlib import Path

from drumscript.audio_processor import audio_loader, onset_detector, feature_extractor, tempo_detector
from drumscript.audio_processor.stem_splitter import extract_drum_stem
from drumscript.audio_processor.stem_splitter import separate_audio
from drumscript.drum_classifier import classify
from drumscript.drum_classifier.classify import classify_events
from drumscript.notation_generator import score_builder
from drumscript.notation_generator.score_builder import build_score
from drumscript.notation_generator import constants
from drumscript.notation_generator.constants import SAMPLE_RATE
# from datetime import datetime

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')

def main(input_audio_path: str, 
         transcribe_full_song: bool = False, 
         time_signature: str = "4/4",
         drumless: bool = False,
         mute: list = None,
         all_stems: bool = False,
         output_format: str = "wav"):
        # .wav format as default, unless --mp3 input specified as an arg in user command
    
    """
    Main orchestration function for DrumScript.

    :param input_audio_path: Path to the input audio file.
    :type input_audio_path: str
    :param transcribe_full_song: If True, separates drums and generates score.
    :type transcribe_full_song: bool, optional
    :param time_signature: Time signature for notation, defaults to "4/4".
    :type time_signature: str, optional
    :param drumless: If True, generates a drumless backing track.
    :type drumless: bool, optional
    :param mute: List of stems to mute.
    :type mute: list, optional
    :param all_stems: If True, exports all individual stems.
    :type all_stems: bool, optional
    :param output_format: Output format ('wav' or 'mp3'), defaults to "wav".
    :type output_format: str, optional
    """
    print(f"\n--- Starting DrumScript ---")
    print(f"Target: {input_audio_path}")

    try:
        # 1. Pre-processing
        #  Stem Separation / Pre-processing
        # Check if user wants stem separation (either for transcription or just extracting stems)
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
        sr = SAMPLE_RATE
        y, sr = audio_loader.load_audio(audio_path, sr=SAMPLE_RATE)
        y = audio_loader.normalise_audio(y) 
        
        # Preserve core functionality: Automatic Tempo Detection
        tempo = tempo_detector.estimate_tempo(y, sr)
        onsets = onset_detector.detect_onsets(y, sr)
        
        print(f"   -> Detected Tempo: {tempo:.1f} BPM")
        print(f"   -> Detected Onsets: {len(onsets)}")

        # 3. Classification
        print("...Classifying (Fundamental Frequency Engine)...")
        # classified_events = classify.classify_drum_hits(y, sr, onsets)
        classified_events = classify.classify_events(y, sr, onsets)
        print(f"   -> Classified {len(classified_events)} events")

        # 4. Score Formatting
        final_events = []
        for event in classified_events:
            final_events.append({
                'time': event['onset_time_seconds'],
                'drums': [event['drum_type']],
                'analysis': event['analysis'], # Contains f0, sc, width, depth
                'midi_pitch': event['midi_pitch'],
                'note_head_type': event['note_head_type'],
                'staff_position': event['staff_position']
            })

        # 5. Output Generation
        output_filename = f"{Path(input_audio_path).stem}_transcription"
        final_pdf_path = f"outputs/{output_filename}.pdf" 
        
        print(f"...Building Score & JSON: {final_pdf_path}...")
        
        # score_builder.build_and_export_drum_score(
        score_builder.build_score(
            detected_events=final_events, 
            tempo=tempo, 
            output_filepath=final_pdf_path,
            time_signature=time_signature
        )

        print("--- Done! ---\n")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

    # If any stem splitting flag is active
        if transcribe_full_song or drumless or mute or all_stems:
            print("...Processing Stems...")
            
            # If transcription is requested (--full), we assume the user wants the stems separated 
            # to feed the 'drums' stem into the transcriber. 
            # If only --drumless is passed, we might not want to transcribe, but the script flow 
            # currently implies transcription follows. 
            
            results = separate_audio(
                input_audio_path=input_audio_path,
                output_format=output_format,
                drumless=drumless,
                mute=mute,
                all_stems=all_stems
            )
            
            # If we are transcribing, we need the isolated drum track
            if transcribe_full_song:
                if 'drums' in results:
                    audio_path = results['drums']
                elif 'drums_stem' in results:
                    audio_path = results['drums_stem']
                else:
                    print("Warning: Drums stem was not found in separation results. Using original.")

            # If the user ONLY wanted stems (e.g. --drumless) and NOT transcription,
            # we should probably stop here? 
            # For now, I will allow it to proceed to transcription unless the user didn't ask for it.
            # However, the current main() structure is built around "Do Transcription".
            # Let's check if the user actually wants to stop.
            if not transcribe_full_song:
                print("Stem processing complete. Exiting (Transcription not requested).")
                return

        # 2. Analysis Pipeline
        print(f"...Loading & Analyzing Audio ({Path(audio_path).name})...")
        y, sr = audio_loader.load_audio(audio_path)
        y = audio_loader.normalise_audio(y) 
        
        tempo = tempo_detector.estimate_tempo(y, sr)
        onsets = onset_detector.detect_onsets(y, sr)
        
        print(f"   -> Detected Tempo: {tempo:.1f} BPM")
        print(f"   -> Detected Onsets: {len(onsets)}")

        # 3. Classification
        print("...Classifying (Fundamental Frequency Engine)...")
        # classified_events = classify.classify_drum_hits(y, sr, onsets)
        classified_events = classify.classify_events(y, sr, onsets)
        print(f"   -> Classified {len(classified_events)} events")

        # 4. Score Formatting
        final_events = []
        for event in classified_events:
            final_events.append({
                'time': event['onset_time_seconds'],
                'drums': [event['drum_type']],
                'analysis': event['analysis'], 
                'midi_pitch': event['midi_pitch'],
                'note_head_type': event['note_head_type'],
                'staff_position': event['staff_position']
            })

        # 5. Output Generation
        output_filename = f"{Path(input_audio_path).stem}_transcription"
        final_pdf_path = f"outputs/{output_filename}.pdf" 
        
        print(f"...Building Score & JSON: {final_pdf_path}...")
        
        # score_builder.build_and_export_drum_score(
        score_builder.build_and_export_drum_score(
            detected_events=final_events, 
            tempo=tempo, 
            output_filepath=final_pdf_path,
            time_signature=time_signature
        )

        print("--- Done! ---\n")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="DrumScript: Audio to Sheet Music & Stem Splitter")
    
    parser.add_argument("input_audio_path", type=str, help="Path to the audio file")
    
    # Transcription argument
    parser.add_argument("--full", action="store_true", help="Transcribe the full song (isolates drums first)")
    
    # Stem Splitter arguments
    parser.add_argument("--drumless", action="store_true", help="Extract a drumless backing track")
    parser.add_argument("--mute", type=str, action='append', help="Mute specific stems (e.g. --mute bass). Can be used multiple times.")
    parser.add_argument("--all-stems", action="store_true", help="Export all individual stems")
    parser.add_argument("--format", type=str, default="wav", choices=["wav", "mp3"], help="Output format for stems (default: wav)")
    
    # Notation arguments
    parser.add_argument("--ts", type=str, default="4/4", help="Time signature (default: 4/4)")
    
    args = parser.parse_args()
    
    main(input_audio_path=args.input_audio_path, 
         transcribe_full_song=args.full, 
         time_signature=args.ts,
         drumless=args.drumless,
         mute=args.mute,
         all_stems=args.all_stems,
         output_format=args.format)

# LEGACY: if __name__ == '__main__':
  #  parser = argparse.ArgumentParser()
  #  parser.add_argument("input_audio_path", type=str)
  #  parser.add_argument("--full", action="store_true")
  #  parser.add_argument("--ts", type=str, default="4/4")
  #  args = parser.parse_args()
    
  #  main(args.input_audio_path, args.full, args.ts)
    
# print("# ------------------------------------------------------------------------------------")


