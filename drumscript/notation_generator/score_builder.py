# DrumScript/notation_generator/score_builder.py

"""
Module to build the final score from classified events.
"""

import json
import os
from typing import Any

from drumscript.notation_generator.midi_exporter import export_to_midi

# from drumscript.notation_generator.pdf_exporter import generate_custom_pdf
from drumscript.notation_generator.pdf_exporter import export_pdf


def build_score(
    detected_events: list[dict[str, Any]],
    # tempo: int = 120,
    # tempo: int, # <-- forces the caller to provide tempo
    tempo: float,
    output_path: str = "outputs/score.pdf",
    quantization_subdivision: int = 16,
    time_signature: str = "4/4",
):
    """
    Builds a drum score by saving event data to JSON and rendering to PDF.
    # Builds a drum score by saving the event data to JSON and then
    # rendering it directly to PDF using the custom engine.
    # This bypasses MusicXML entirely to ensure WYSIWYG (What You See Is What You Get) results.
    # Builds a drum score PDF, respecting the provided Time Signature, or assuming default 4/4 if not provided

    :param detected_events: List of classified drum events.
    :type detected_events: List[Dict[str, Any]]
    :param tempo: Tempo in BPM.
    :type tempo: int
    :param output_path: Path to save the PDF.
    :type output_path: str, optional
    :param quantization_subdivision: Grid for quantization (e.g., 16 for 16th notes).
    :type quantization_subdivision: int, optional
    :param time_signature: Time signature string (e.g., "4/4").
    :type time_signature: str, optional
    """

    print(f"--- Building Score for: {output_path} [Time Sig: {time_signature}] ---")

    # --- MUSICAL INTERPRETATION LOGIC ---
    # Drum algorithms often detect the "double time" tempo (e.g. 130 BPM instead of 65 BPM).
    # To make the sheet music readable in standard 4/4 time (giving it a "half-time feel"
    # where the snare lands heavily on beat 3), we halve the raw detected tempo for notation.
    #    tempo = tempo / 2.0
    tempo = tempo

    # --- QUANTIZATION LOGIC
    # Snap all raw timestamps to a perfect musical grid so notes align vertically
    if tempo > 0:
        seconds_per_beat = 60.0 / float(tempo)
        # If subdivision is 16 (16th notes), that is 4 grid slices per beat
        grid_step_seconds = seconds_per_beat * (4.0 / quantization_subdivision)

        for event in detected_events:
            # raw_time = event['time']
            raw_time = event["time_sec"]
            # Round the raw human time to the nearest perfect grid step
            quantized_time = round(raw_time / grid_step_seconds) * grid_step_seconds
            # Overwrite the raw time with the "snapped" perfect time
            # event['time'] = quantized_time
            event["time_sec"] = quantized_time

    # ----------------------------------------------------
    # 1. Prepare File Paths
    # output_path e.g. "outputs/mysong.pdf"
    base_path = os.path.splitext(output_path)[0]  # "outputs/mysong"
    json_path = f"{base_path}.json"

    # NEW: Derive specific file paths from the base string
    pdf_filepath = f"{base_path}.pdf"
    midi_filepath = f"{base_path}.mid"

    # 2. Save Transcription Data to JSON
    # This file serves as the "Source of Truth" for the PDF renderer.
    try:
        print(f"Saving to: {json_path}")
        with open(json_path, "w") as f:
            json.dump(detected_events, f, indent=4)
    except Exception as e:
        print(f" Warning: Could not save JSON transcription: {e}")

    # 3. Generate Visual PDF (Directly from Data)
    try:
        # generate_custom_pdf(
        export_pdf(
            detected_events=detected_events,
            # OLD: output_path=output_path,
            output_path=pdf_filepath,  # Updated to explicitly map to .pdf
            tempo=tempo,
            time_signature=time_signature,
        )

    # Success message is handled inside generate_custom_pdf/export_pdf in pdf_exporter.py
    except Exception as e:
        print(f"PDF Export Failed: {e}")
        import traceback

        traceback.print_exc()

    # 4. Generate MIDI File
    try:
        export_to_midi(
            classified_events=detected_events,
            output_path=midi_filepath,  # Updated to explicitly map to .mid
            tempo=tempo,
        )
    except Exception as e:
        print(f"MIDI Export Failed: {e}")
        import traceback

        traceback.print_exc()


# --------------------------------------------------------------------------uncomment during testing
# from datetime import datetime
# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')
# --------------------------------------------------------------------------------------------------
