import subprocess
import os
from pathlib import Path
import tempfile
import shutil
import sys
import time

from datetime import datetime

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f'\ndate/time: {datetimestamp}')

## PLEASE NOTE: This is currently a test script. Original Demucs is no longer being maintained (owned by Meta/Facebook). Owners have forked and maintain occasionally: https://github.com/adefossez/demucs. THe usage of demucs is therefore subject to some uncertainty. We may decide to build our own stem_splitter model in DrumScript in order to ensure the long-term stability of the package, and to continue to make it as lightweight as possible.

# Use 'htdemucs', the default (and high-quality) 4-stem model
DEMUCS_MODEL = "htdemucs" 

def extract_drum_stem(input_audio_path: str) -> str:
    """
    Separates a full audio track using the Demucs command-line tool
    and returns the file path to the isolated drum stem.
    
    Args:
        input_audio_path: The file path to the user's full song.

    Returns:
        The file path to the extracted 'drums.wav' stem.
        
    Raises:
        FileNotFoundError: If demucs isn't installed or the drum file isn't created.
        RuntimeError: If the Demucs process fails.
    """
    
    # 1. Create a temporary directory to store the separation output. 
    ## Use this for storing in /var/ folder on local machine, 'ie /var/folders/m0/_mjkpjps6lq_13m2l6sfckw40000gn/T/tmpp8b3ez_e/htdemucs/'
    ## MIGHT RESTORE THIS POST-TESTING

    # temp_output_dir = tempfile.mkdtemp()

    ### OR...

    # 1. Define a local output directory, ie put the outputs where you want them
    ## MIGHT COMMENT OUT AGAIN, POST-TESTING
    output_dir = Path("./outputs/stems_test")
    
    # Create the directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Use this path as the output directory
    temp_output_dir = str(output_dir)

    # 2. Build the Demucs command
    command = [
        "demucs",
        "-o", str(temp_output_dir),
        "-n", DEMUCS_MODEL,
        "--flac",
        str(input_audio_path)
    ]

    # 3. Run the Demucs separation process
    # print("\n# =============================================================================================")
    # print("\n# PLEASE NOTE: This is currently a test script. Original Demucs is no longer being maintained (owned by Meta/Facebook). Owners have forked and maintain occasionally: https://github.com/adefossez/demucs. The usage of demucs is therefore subject to some uncertainty. We may decide to build our own stem_splitter model in DrumScript in order to ensure the long-term stability of the package, and to continue to make it as lightweight as possible.")
    print(f"Starting Demucs separation for: {input_audio_path}...")

    ## ---- Timer block, might remove later --------------------------------------------------------------
    start_time = time.monotonic() # Start timer, MIGHT REMOVE LATER ONCE FINISHED DEBUGGING

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
                
        end_time = time.monotonic()  # <-- 3. Stop the timer
        duration = end_time - start_time
        print(f"Demucs separation finished in {(duration/60):.2f} minutes.")
    ## ----------------------------------------------------------------------------------------------------
    # --- NEW: Step 3.5 - Convert FLAC files to MP3 ---
        print("Converting stems to MP3...")
        
        # Find the folder where demucs saved the files
        input_filename_stem = Path(input_audio_path).stem
        stems_folder = Path(temp_output_dir) / DEMUCS_MODEL / input_filename_stem
        
        # Find all the .flac files in that folder
        flac_files = list(stems_folder.glob("*.flac"))
        if not flac_files:
            print("Warning: No .flac files found to convert.")

        for flac_file in flac_files:
            mp3_file = flac_file.with_suffix(".mp3")
            
            # This command converts FLAC to high-quality VBR MP3
            convert_command = [
                "ffmpeg",
                "-i", str(flac_file),  # Input file
                "-q:a", "0",          # Set quality to highest VBR (0)
                str(mp3_file),        # Output file
                "-y"
            ]
            
            # Run the conversion
            subprocess.run(convert_command, check=True, capture_output=True, text=True)
            
        print(f"Successfully converted {len(flac_files)} stems to MP3.")
        # --- END OF NEW SECTION ---

        
    except subprocess.CalledProcessError as e:
        print(f"Demucs separation failed with error: {e.stderr}")
        shutil.rmtree(temp_output_dir) # Clean upc
        raise RuntimeError(f"Demucs failed to process the audio. Error: {e.stderr}")
        
    except FileNotFoundError:
        shutil.rmtree(temp_output_dir) # Clean up
        raise FileNotFoundError(
            "The 'demucs' command was not found. "
            "Is it installed correctly in your environment's PATH?"
        )
    

    # 4. Find and return the path to the drum file
    input_filename_stem = Path(input_audio_path).stem

    expected_drum_path = Path(temp_output_dir) / DEMUCS_MODEL / input_filename_stem / "drums.flac"
    # expected_drum_path = Path(temp_output_dir) / DEMUCS_MODEL / input_filename_stem / "drums.wav" # commented out in order to avoid using torchcodec

    if not expected_drum_path.exists():
        shutil.rmtree(temp_output_dir) # Clean up
        raise FileNotFoundError(
            f"Demucs ran, but the drum output file was not found at {expected_drum_path}"
        )

    print(f"Drum stem extracted successfully to: {expected_drum_path}")
    
    # Return the full path to the drum file.
    return str(expected_drum_path)

# --- Test harness ---
if __name__ == "__main__":
    """
    Allows the script to be run directly for testing.
    
    Usage:
        python drumscript/audio_processor/stem_splitter.py "path/to/song.mp3"
    """
    if len(sys.argv) < 2:
        print("Usage: python stem_splitter.py <path_to_audio_file>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    
    if not Path(input_file).exists():
        print(f"Error: File not found at {input_file}")
        sys.exit(1)

    temp_drum_file_path = None
    temp_dir_to_clean = None

    try:
        # Run the function
        temp_drum_file_path = extract_drum_stem(input_file)
        
        # On success, find the root temp directory
        if temp_drum_file_path:
            # Path is .../temp_dir_xyz/htdemucs/song_name/drums.wav
            # We must delete the root temp directory, 3 levels up.
            temp_dir_to_clean = Path(temp_drum_file_path).parent.parent.parent
            print(f"\n--- TEST SUCCESSFUL ---")
            print(f"Drum file created at: {temp_drum_file_path}")
            print(f"Root temp directory: {temp_dir_to_clean}")

    except Exception as e:
        print(f"\n--- TEST FAILED ---")
        print(f"An error occurred: {e}")
        
    # commenting out the cleaning step (for now)
    #finally:
         # Clean up the temporary directory AFTER the test
        #if temp_dir_to_clean and Path(temp_dir_to_clean).exists():
            #try:
             #   shutil.rmtree(temp_dir_to_clean)
             #   print(f"Successfully cleaned up temporary directory.")
            #except OSError as e:
             #   print(f"Error cleaning up directory {temp_dir_to_clean}: {e}")
        #else:
         #   print("No temporary directory to clean up.")

# Uncomment to use, for clearer error logs
print("\n# ------------------------------------------------------------------------------------")