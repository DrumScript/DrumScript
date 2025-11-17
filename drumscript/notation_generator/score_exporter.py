# DrumScript/notation_generator/score_exporter.py
import music21
import os
import logging
from pathlib import Path

# Get the logger for consistent logging
logger = logging.getLogger('DrumScript')

def export_score(score: music21.stream.Score, output_filepath_base: str):
    """
    Exports a music21 score to MusicXML format.
    
    Args:
        score (music21.stream.Score): The music21 score object to be exported.
        output_filepath_base (str): The full path *without* an extension.
                                    e.g., "outputs/my_song_transcription"
    """
    
    # --- 1. Define File Paths ---
    output_path = Path(output_filepath_base)
    output_dir = output_path.parent
    file_stem = output_path.stem
    
    # Define the .xml path
    xml_path = output_dir / f"{file_stem}.musicxml"
    
    # Create the output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    xml_path_str = str(xml_path)

    # --- 2. Export the MusicXML file ---
    try:
        logger.info(f"Saving MusicXML transcription to: {xml_path_str}...")
        score.write('musicxml', fp=xml_path_str)
        logger.info(f"Successfully saved {xml_path_str}")
        
    except Exception as e:
        logger.error(f"ERROR: Failed to save MusicXML file: {e}", exc_info=True)
        raise