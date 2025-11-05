# main.py
import argparse
import os
import sys

# --- 1. IMPORT MODULES ---
# This try/except block ensures that if the package isn't
# installed correctly, the user gets a helpful error.
try:
    # Import functions from audio_processor module
    from drumscript.audio_processor.audio_loader import load_audio
    from drumscript.audio_processor.onset_detector import detect_onsets
    from drumscript.audio_processor.feature_extractor import extract_features_for_onsets

    # Import the predict function from rule-based engine
    from drumscript.drum_classifier.predict import predict_drum_hits

    # Import notation functions
    # (Assuming 'build_score' creates the score and exporters save it)
    from drumscript.notation_generator.score_builder import build_and_export_drum_score
    from drumscript.notation_generator.pdf_exporter import export_to_xml # Keep this for the separate XML export

except ImportError as e:
    print(f"Error importing DrumScript modules: {e}")
    print("Please ensure DrumScript is installed correctly.")
    print("If running from source, try 'pip install -e .' from the project root.")
    sys.exit(1)


def run_transcription_pipeline(input_path: str, output_base_path: str):
    """
    Orchestrates the complete DrumScript transcription pipeline.
    This is the new logic, based on rule-based engine.
    """
    try:
        # --- 1. AUDIO PROCESSOR ---
        print(f"Loading and processing audio file: {input_path}")
        y, sr = load_audio(input_path, sr=44100) # Use 44.1kHz as used in our tests

        print("Detecting onsets...")
        onset_times = detect_onsets(y, sr)
        print(f"Detected {len(onset_times)} onsets.")

        print("Extracting features for each onset...")
        all_onset_features = extract_features_for_onsets(y, sr, onset_times)
        print("Feature extraction complete.")

        # --- 2. DRUM CLASSIFIER (THE ENGINE) ---
        print("Classifying onsets using rule-based system...")
        classified_drum_events = predict_drum_hits(all_onset_features)
        print(f"Classification complete. Found {len(classified_drum_events)} drum events.")

        if not classified_drum_events:
            print("No drum events were classified. Exiting.")
            return

        # --- 3. NOTATION GENERATOR ---
        print("Building musical score and exporting...")

        # Define output file paths
        output_pdf_path = output_base_path + ".pdf"
        output_xml_path = output_base_path + ".xml"

        # Call the correct function from score_builder
        # This function currently builds the score AND exports the PDF
        score_object = build_and_export_drum_score(
            detected_events=classified_drum_events,
            tempo=120, # Placeholder: We'll need to get this from tempo_detector
            output_filepath=output_pdf_path,
            quantization_subdivision=16 
        )
        print(f"PDF saved to: {output_pdf_path}")

        # Now, export the XML from the returned score object
        print(f"Exporting MusicXML to: {output_xml_path}")
        export_to_xml(score_object, output_xml_path)

        print("\n--- Transcription Complete! ---")
        print(f"PDF saved to: {output_pdf_path}")
        print(f"XML saved to: {output_xml_path}")

    except Exception as e:
        print(f"\n--- An Error Occurred ---", file=sys.stderr)
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)

def main():
    """
    Main entry point for the 'drumscript' command-line tool.
    """
    parser = argparse.ArgumentParser(
        description="Transcribe drum audio into sheet music.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument(
        "input_file",
        type=str,
        help="Path to the input audio file (e.g., my_drums.wav)"
    )
    parser.add_argument(
        "-o", "--output",
        type=str,
        default=None,
        help="The base name for output files (e.g., 'my_score').\n"
             "This will create 'my_score.pdf' and 'my_score.xml'.\n"
             "(Default: Same name as the input file)"
    )

    args = parser.parse_args()

    # --- Determine output path ---
    output_base = args.output
    if output_base is None:
        # If no output name is given, use the input file's name
        output_base = os.path.splitext(os.path.basename(args.input_file))[0]

    # --- Run the pipeline ---
    run_transcription_pipeline(args.input_file, output_base)


if __name__ == "__main__":
    main()