# local_tests/pdf_generation/json_to_pdf_test.py

import os
import sys
import json
from datetime import datetime

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f'\ndate/time: {datetimestamp}')

# --- PATH SETUP ---
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))
sys.path.insert(0, project_root)

try:
    from drumscript.notation_generator.pdf_exporter import generate_custom_pdf
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Python path: {sys.path}")
    sys.exit(1)

def run_json_test():
    print("--- Running JSON to PDF Fidelity Test (Mock Data) ---")

    # 1. Mock JSON Data
    # UPDATED: Keys now match what pdf_exporter expects ('time', 'drums')
    mock_data = [
        # Measure 1: Basic Groove
        {"time": 0.0, "drums": ["kick"], "analysis": {}},
        {"time": 0.25, "drums": ["hi_hat_closed"], "analysis": {}},
        {"time": 0.5, "drums": ["snare"], "analysis": {}},
        {"time": 0.75, "drums": ["hi_hat_closed"], "analysis": {}},

        # Measure 2: Toms and Clicky Kick Check
        {"time": 1.0, "drums": ["kick_clicky"], "analysis": {}},
        {"time": 1.25, "drums": ["low_tom"], "analysis": {}},
        {"time": 1.5, "drums": ["mid_tom"], "analysis": {}},
        {"time": 1.75, "drums": ["high_tom"], "analysis": {}},

        # Measure 3: Cymbals and Open Hat
        {"time": 2.0, "drums": ["crash"], "analysis": {}},
        {"time": 2.25, "drums": ["ride"], "analysis": {}},
        {"time": 2.5, "drums": ["snare"], "analysis": {}},
        {"time": 2.75, "drums": ["hi_hat_open"], "analysis": {}},
    ]

    # 2. Define Output Paths
    output_dir = os.path.join(project_root, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "json_fidelity_test_output.pdf")

    # 3. Run the PDF Generator
    try:
        generate_custom_pdf(
            detected_events=mock_data,
            output_filepath=output_path,
            tempo=120
        )
        print(f"SUCCESS! Fidelity Test PDF generated: {output_path}")
        print("Please check the PDF to confirm all notes are in their correct vertical positions.")
    except Exception as e:
        print(f"FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_json_test()

print("\n# ------------------------------------------------------------------------------------")