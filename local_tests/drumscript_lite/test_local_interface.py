# local_tests/drumscript_lite/test_local_interface.py
import os
import sys

import numpy as np

# from datetime import datetime

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')


# 1. Force Python to look in the project root for 'drumscript'
# Go up levels from 'local_tests/drumscript_lite' to reach the root
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, "../../"))
sys.path.insert(0, project_root)

print("--- Testing DrumScript Package Interface ---")
print(f"Searching for package in: {project_root}")

try:
    import drumscript as ds

    # IMPORT CONSTANT HERE
    # We access the sub-module explicitly
    from drumscript.notation_generator.constants import SAMPLE_RATE as sr

    print("SUCCESS: 'import drumscript' worked.")
    print(f"SUCCESS: Imported 'SAMPLE_RATE' as {sr} Hz")

except ImportError as e:
    print(f"FAIL: Could not import drumscript or constants. Error: {e}")
    sys.exit(1)

# 2. Check if functions are exposed correctly
functions_to_check = ["stem_split", "tempo_detector", "install_ffmpeg"]
all_present = True

for func_name in functions_to_check:
    if hasattr(ds, func_name):
        print(f"FOUND: ds.{func_name}")
    else:
        print(f"MISSING: ds.{func_name}")
        all_present = False

if not all_present:
    print("Stopping test due to missing functions.")
    sys.exit(1)

# 3. Functional Test: Tempo Detector (using constants)
print("\n--- Running Functional Test: Tempo Detector ---")
try:
    # Use the imported 'sr' (SAMPLE_RATE) to generate 2 seconds of silence
    dummy_audio = np.zeros(sr * 2)

    # Run the function
    result = ds.tempo_detector(dummy_audio, full=True)

    print("Tempo Detector ran successfully!")
    print(f"   Output: {result}")
except Exception as e:
    print(f"Tempo Detector crashed: {e}")

# 4. Interface Test: Stem Split
print("\n--- Checking Stem Splitter ---")
try:
    # Checking internal import
    from drumscript.audio_processor.stem_splitter import extract_drum_stem

    print("Internal import 'extract_drum_stem' is accessible.")
except ImportError as e:
    print(f"Could not access internal stem splitter: {e}")

print("\n-------------------------------------------")
print("READY TO BUILD: usage of 'ds.stem_split' and 'ds.tempo_detector' is valid.")

# print("\n# ------------------------------------------------------------------------------------")
