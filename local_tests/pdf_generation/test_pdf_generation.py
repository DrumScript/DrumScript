import os
import sys
from datetime import datetime


print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f'\ndate/time: {datetimestamp}')


# --- PATH SETUP ---
# Get the directory where this script is located 
# (e.g., .../DrumScript/local_tests/pdf_generation)
current_dir = os.path.dirname(os.path.abspath(__file__))

# Go up TWO levels to find the project root (e.g., .../DrumScript)
# Level 1: .../DrumScript/local_tests
# Level 2: .../DrumScript
project_root = os.path.abspath(os.path.join(current_dir, "..", ".."))

# Add project root to sys.path so we can import 'drumscript'
sys.path.insert(0, project_root)

try:
    from drumscript.notation_generator.pdf_exporter import generate_custom_pdf
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Python path is currently: {sys.path}")
    sys.exit(1)

def run_pdf_test():
    print("--- Running PDF Generation Test with Extended Mock Data ---")

    # 1. Define Mock Data: Extended to test Toms, Ride, and Double Bass
    # 120 BPM -> 1 beat = 0.5 seconds
    mock_events = [
        # --- MEASURE 1: Basic Rock (Kick/Snare/Hats) ---
        # (We know this works, but keeping it as a baseline)
        {'time': 0.00, 'drums': ['kick', 'hi_hat_closed']},
        {'time': 0.25, 'drums': ['hi_hat_closed']},
        {'time': 0.50, 'drums': ['snare', 'hi_hat_closed']},
        {'time': 0.75, 'drums': ['hi_hat_closed']},
        {'time': 1.00, 'drums': ['kick', 'hi_hat_closed']},
        {'time': 1.25, 'drums': ['hi_hat_closed']},
        {'time': 1.50, 'drums': ['snare', 'hi_hat_open']},
        {'time': 1.75, 'drums': ['hi_hat_closed']}, 

        # --- MEASURE 2: Tom Fill (High -> Mid -> Low) ---
        # Testing vertical separation of toms. 
        # Ideally: High (Top Space), Mid (Line 4), Low (Space 2)
        {'time': 2.00, 'drums': ['high_tom']},
        {'time': 2.25, 'drums': ['high_tom']},
        {'time': 2.50, 'drums': ['mid_tom']},
        {'time': 2.75, 'drums': ['mid_tom']},
        {'time': 3.00, 'drums': ['low_tom']},  # <--- Checks "Floor Tom" position
        {'time': 3.25, 'drums': ['low_tom']},
        {'time': 3.50, 'drums': ['kick', 'crash']}, # Accent finish
        {'time': 3.75, 'drums': []}, # Rest

        # --- MEASURE 3: Double Bass & Ride Cymbal ---
        # Testing 'kick_clicky' (should look like Kick) and 'ride' (Top Line)
        {'time': 4.00, 'drums': ['kick_clicky', 'ride']},
        {'time': 4.125, 'drums': ['kick_clicky']}, # 16th note double kick
        {'time': 4.25, 'drums': ['ride']},
        {'time': 4.375, 'drums': ['kick_clicky']},
        {'time': 4.50, 'drums': ['snare', 'ride']},
        {'time': 4.75, 'drums': ['ride']},
        
        # --- MEASURE 4: Visual Comparison (Snare vs Low Tom) ---
        # Helpful to resolve your ambiguity issue: Do they look distinct?
        {'time': 6.00, 'drums': ['snare']},    # Should be`` Space 3 (Higher)
        {'time': 6.50, 'drums': ['low_tom']},  # Should be Space 2 (Lower)
        {'time': 7.00, 'drums': ['snare', 'low_tom']}, # Simultaneous hit check
    ]

    # 2. Define Output Path
    output_dir = os.path.join(project_root, "outputs")
    os.makedirs(output_dir, exist_ok=True)
    
    output_path = os.path.join(output_dir, "extended_drum_test.pdf")

    # 3. Run the PDF Generator
    try:
        generate_custom_pdf(
            detected_events=mock_events,
            output_filepath=output_path,
            tempo=120
        )
        print(f"\n SUCCESS! Extended Test PDF saved to: {output_path}")
        print("Open this file to check:")
        print("  1. Are Toms clearly separated vertically?")
        print("  2. Does the 'Low Tom' look like a Floor Tom (Space 2)?")
        print("  3. Does 'Kick Clicky' look identical to a normal Kick (Bottom Space)?")
        print("  4. Is the Ride cymbal on the Top Line (distinct from Hi-Hat above it)?")
        
    except Exception as e:
        print(f"\n FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    run_pdf_test()


print("\n# ------------------------------------------------------------------------------------")