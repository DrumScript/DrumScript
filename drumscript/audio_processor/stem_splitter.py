import subprocess
import os
from pathlib import Path
import tempfile
import shutil

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
    
    # 1. Create a temporary directory to store the separation output
    temp_output_dir = tempfile.mkdtemp()

    # 2. Build the Demucs command
    # This command tells Demucs to:
    # -o: Use our temporary output directory
    # -n: Use the specified model (htdemucs)
    # The final argument is the input file path.
    command = [
        "demucs",
        "-o", str(temp_output_dir),
        "-n", DEMUCS_MODEL,
        str(input_audio_path)
    ]

    # 3. Run the Demucs separation process
    print(f"Starting Demucs separation for: {input_audio_path}...")
    try:
        # We use subprocess.run for a clean, blocking call.
        # check=True will raise an error if Demucs fails.
        # capture_output=True keeps stdout/stderr tidy.
        subprocess.run(command, check=True, capture_output=True, text=True)
        
    except subprocess.CalledProcessError as e:
        # This error means demucs ran but failed.
        print(f"Demucs separation failed with error: {e.stderr}")
        shutil.rmtree(temp_output_dir) # Clean up
        raise RuntimeError(f"Demucs failed to process the audio. Error: {e.stderr}")
        
    except FileNotFoundError:
        # This error means the 'demucs' command wasn't found at all.
        shutil.rmtree(temp_output_dir) # Clean up
        raise FileNotFoundError(
            "The 'demucs' command was not found. "
            "Is it installed correctly in your environment's PATH?"
        )

    # 4. Find and return the path to the drum file
    # Demucs creates a specific folder structure:
    # <temp_output_dir> / <model_name> / <input_filename_stem> / drums.wav
    
    input_filename_stem = Path(input_audio_path).stem
    expected_drum_path = Path(temp_output_dir) / DEMUCS_MODEL / input_filename_stem / "drums.wav"

    if not expected_drum_path.exists():
        shutil.rmtree(temp_output_dir) # Clean up
        raise FileNotFoundError(
            f"Demucs ran, but the drum output file was not found at {expected_drum_path}"
        )

    print(f"Drum stem extracted successfully to: {expected_drum_path}")
    
    # Return the full path to the drum file.
    # The calling script (main.py) will be responsible for deleting
    # the parent 'temp_output_dir' when it's done.
    return str(expected_drum_path)