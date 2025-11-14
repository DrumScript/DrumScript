import shutil
from pathlib import Path
import os
import sys
from drumscript.audio_processor.stem_splitter import extract_drum_stem
from drumscript.audio_processor import audio_loader, onset_detector, feature_extractor, tempo_detector
from drumscript.drum_classifier import predict
from drumscript.notation_generator import score_builder, pdf_exporter
from drumscript.utils.logging import setup_logging

print("\n#=============================================================================================")

def main(input_audio_path: str, transcribe_full_song: bool = False):
    """
    Main orchestration script for the DrumScript transcription pipeline.

    Args:
        input_audio_path (str): Path to the audio file to process.
        transcribe_full_song (bool): 
            If True, treat input as a full song and run stem separation.
            If False (default), assume input is already a drum-only track.
    """
    
    logger = setup_logging()
    logger.info(f"--- Starting DrumScript transcription for: {input_audio_path} ---")

    temp_drum_file_path = None
    temp_output_dir = None

    try:
        # 2. Add the new pre-processing step
        if transcribe_full_song:
            try:
                # 1. SEPARATE DRUM STEM
                logger.info("Full song mode: Separating drum stem...")
                # This will create the stems in a temp folder
                temp_drum_file_path = extract_drum_stem(input_audio_path)
                
                # The path to the drum file is .../temp_dir_xyz/htdemucs/song_name/drums.flac
                # We must delete the root temp directory, 3 levels up.
                # temp_dir_to_clean = Path(temp_drum_file_path).parent.parent.parent
                temp_output_dir = Path(temp_drum_file_path).parent.parent.parent
                
                logger.info(f"Drum stem extracted to: {temp_drum_file_path}")
                
                # Use the new stem path for the rest of the pipeline
                audio_to_process = temp_drum_file_path
                
            except (RuntimeError, FileNotFoundError) as e:
                logger.error(f"Failed to separate drum stem: {e}")
                return # Exit if separation fails
        else:
            logger.info("Drum-only mode: Processing file directly.")
            audio_to_process = input_audio_path

        # 2. LOAD AUDIO
        logger.info(f"Loading audio from: {audio_to_process}")
        y, sr = audio_loader.load_audio(audio_to_process)

        # 3. DETECT TEMPO
        estimated_tempo = tempo_detector.estimate_tempo(y, sr)
        logger.info(f"Estimated tempo: {estimated_tempo:.2f} BPM")

        # 4. DETECT ONSETS
        logger.info("Detecting onsets...")
        # onset_frames = onset_detector.find_onsets(y, sr)
        onset_frames = onset_detector.detect_onsets(y, sr)
        logger.info(f"Found {len(onset_frames)} onset events.")

        # 5. EXTRACT FEATURES
        logger.info("Extracting features for each onset...")
        features = feature_extractor.extract_features_for_onsets(y, sr, onset_frames)
        
        # 6. CLASSIFY HITS (Rule-Based Engine)
        logger.info("Classifying drum hits...")
        classified_events = predict.predict_drum_hits(features)
        
        # 7. BUILD SCORE
        logger.info("Building music score...")
        #score = score_builder.build_score(classified_events, estimated_tempo)
        score = score_builder.build_and_export_drum_score(classified_events, estimated_tempo)

        # 8. EXPORT SCORE
        output_filename = f"{Path(input_audio_path).stem}_transcription"
        logger.info(f"Exporting score to {output_filename}...")
        pdf_exporter.export_score_to_pdf(score, f"outputs/{output_filename}.pdf")
        
        logger.info(f"--- Transcription complete for: {input_audio_path} ---")

    except Exception as e:
        logger.error(f"An unexpected error occurred in the pipeline: {e}", exc_info=True)

    finally:
            # 3. Add the cleanup block for the temp files
            if temp_output_dir and Path(temp_output_dir).exists():
                try:
                    # shutil.rmtree(temp_output_dir)
                    logger.info(f"Successfully cleaned up temporary directory: {temp_output_dir}")
                except OSError as e:
                    logger.error(f"Failed to clean up temporary directory {temp_output_dir}: {e}")

if __name__ == '__main__':
    # This allows testing the feature from the command line.
    
    if len(sys.argv) < 2:
        print("Usage: python main.py <path_to_audio_file> [--full]")
        sys.exit(1)
        
    input_path = sys.argv[1]
    
    # Check if the '--full' flag is present
    run_as_full_song = '--full' in sys.argv
    
    main(input_path, transcribe_full_song=run_as_full_song)

print("\n#=============================================================================================")