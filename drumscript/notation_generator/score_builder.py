# DrumScript/notation_generator/score_builder.py

import json
import os
from typing import List, Dict, Any
from drumscript.notation_generator.pdf_exporter import generate_custom_pdf 

def build_and_export_drum_score(
    detected_events: List[Dict[str, Any]],
    tempo: int = 120,
    output_filepath: str = "outputs/score.pdf",
    quantization_subdivision: int = 16, 
    time_signature: str = "4/4" 
):
    """
    Builds a drum score by saving the event data to JSON and then 
    rendering it directly to PDF using the custom engine.
    
    This bypasses MusicXML entirely to ensure WYSWYG (What You See Is What You Get) results.
    """
    print(f"--- Building Score for: {output_filepath} ---")

    # 1. Prepare File Paths
    # output_filepath e.g. "outputs/mysong.pdf"
    base_path = os.path.splitext(output_filepath)[0] # "outputs/mysong"
    json_path = f"{base_path}.json"

    # 2. Save Transcription Data to JSON (Intermediate "Score" File)
    # This file serves as the "Source of Truth" for the PDF renderer.
    try:
        print(f"Saving intermediate data to: {json_path}")
        with open(json_path, 'w') as f:
            json.dump(detected_events, f, indent=4)
    except Exception as e:
        print(f" Warning: Could not save intermediate JSON: {e}")

    # 3. Generate Visual PDF (Directly from Data)
    try:
        generate_custom_pdf(
            detected_events=detected_events,
            output_filepath=output_filepath,
            tempo=tempo
        )
        # Success message is handled inside generate_custom_pdf
    except Exception as e:
        print(f"Native PDF Export Failed: {e}")
        import traceback
        traceback.print_exc()