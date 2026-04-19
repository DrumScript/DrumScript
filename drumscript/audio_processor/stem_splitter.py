# drumscript/audio_processor/stem_splitter.py
"""
This module uses the demucs library () to extract stemms from multi-layer audio files
Running: `python3 -m drumscript.audio_processor.stem_splitter path_to_audio_file`
It supports generating 'drumless' tracks, isolating specific instruments, and format conversion.
"""

import subprocess
import os
from pathlib import Path
import tempfile
import shutil
import sys
import time
from pydub import AudioSegment
# from datetime import datetime

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')

# Use 'htdemucs', the default (and high-quality) 4-stem model
# Stems output by htdemucs: 'drums', 'bass', 'other', 'vocals'
DEMUCS_MODEL = "htdemucs" 


## PLEASE NOTE: Original Demucs is no longer being maintained (owned by Meta/Facebook). Owners have forked and maintain occasionally: https://github.com/adefossez/demucs. THe usage of demucs is therefore subject to some uncertainty. We may decide to build our own stem_splitter model in DrumScript in order to ensure the long-term stability of the package, and to continue to make it as lightweight as possible.

# ===============================================================================================
def separate_audio(input_audio_path: str, output_format: str = "wav", drumless: bool = False, mute: list = None, all_stems: bool = False) -> dict:
    """
    Separates a full audio track using Demucs and processes the outputs based on user-input args (optional)
    
    Args:
    :param input_audio_path: Path to the source audio.
    :type input_audio_path: str
    :param output_format: 'wav' or 'mp3', defaults to 'wav'.
    :type output_format: str, optional
    :param drumless: If True, generates a track with everything EXCEPT drums, but also saves the drum only output
    :type drumless: bool, optional
    :param mute: List of stems to exclude (e.g., ['bass']).
    :type mute: list, optional
    :param all_stems: If True, saves all individual raw stems.
    :type all_stems: bool, optional
    :return: Dictionary of paths to generated files.
    :rtype: dict
    Returns:
        dict: Paths to the generated files (e.g., {'drums': path, 'mix': path}).
    """
    input_path = Path(input_audio_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_audio_path}")

    # 1. Define Output Directory
    # We save outputs to a 'processed_stems' folder in the project root/outputs for visibility
    base_output_dir = Path("./outputs/processed_stems") / input_path.stem
    base_output_dir.mkdir(parents=True, exist_ok=True)
    
    # Temp dir for raw demucs output
    temp_demucs_dir = base_output_dir / "temp_demucs"
    
    print(f"Starting Demucs separation for: {input_path.name}...")
    start_time = time.monotonic()

    # 2. Run Demucs
    # We always output FLAC or WAV from Demucs first, then convert/mix later.
    # Using flac for intermediate speed/quality.
    command = [
        "demucs",
        "-o", str(temp_demucs_dir),
        "-n", DEMUCS_MODEL,
        "--flac", 
        str(input_path)
    ]

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        shutil.rmtree(temp_demucs_dir, ignore_errors=True)
        raise RuntimeError(f"Demucs failed: {e.stderr}")
    except FileNotFoundError:
        raise FileNotFoundError("The 'demucs' command was not found. Please install it.")

    print(f"Demucs raw separation finished in {((time.monotonic() - start_time)/60):.2f} minutes.")

    # 3. Locate Raw Stems
    # Demucs structure: output_dir / model_name / song_name / {stem}.flac
    raw_stem_dir = temp_demucs_dir / DEMUCS_MODEL / input_path.stem
    
    available_stems = ['drums', 'bass', 'other', 'vocals']
    stem_paths = {}
    
    for stem in available_stems:
        # Demucs output is .flac because we used --flac
        path = raw_stem_dir / f"{stem}.flac"
        if path.exists():
            stem_paths[stem] = path
        else:
            print(f"Warning: Expected stem {stem} not found.")

    results = {}

    # 4. Handle "Drumless" Logic (Shortcut for Mute=['drums'])
    stems_to_exclude = set()
    if mute:
        stems_to_exclude.update(mute)
    if drumless:
        stems_to_exclude.add('drums')

    # 5. Determine what to mix
    # If the user asked to mute something (e.g. drums), we create a mix of everything else.
    if stems_to_exclude:
        mix_list = [s for s in available_stems if s not in stems_to_exclude]
        
        # Name the file based on what is missing, e.g., "song_no_drums" or "song_no_bass"
        exclusion_tag = "_no_" + "_".join(stems_to_exclude)
        output_filename = f"{input_path.stem}{exclusion_tag}.{output_format}"
        output_path = base_output_dir / output_filename
        
        print(f"Creating mix: {output_filename} (Stems: {mix_list})...")
        mix_stems(stem_paths, mix_list, output_path, fmt=output_format)
        results['mix'] = str(output_path)

        # The user requested: "saves the extracted element too"
        # So if we mute 'drums', we should also save the 'drums' stem separately.
        for excluded in stems_to_exclude:
            if excluded in stem_paths:
                stem_out_name = f"{input_path.stem}_only_{excluded}.{output_format}"
                stem_out_path = base_output_dir / stem_out_name
                # Convert/Copy the single stem
                AudioSegment.from_file(stem_paths[excluded]).export(
                    str(stem_out_path), format=output_format, 
                    parameters=["-q:a", "0"] if output_format == "mp3" else None
                )
                results[f'{excluded}_stem'] = str(stem_out_path)

    # 6. Handle "--all-stems"
    if all_stems:
        print("Exporting all individual stems...")
        for stem, path in stem_paths.items():
            # Avoid re-doing work if we already exported it in step 5
            expected_name = f"{input_path.stem}_only_{stem}.{output_format}"
            if (base_output_dir / expected_name).exists():
                continue
                
            out_path = base_output_dir / expected_name
            AudioSegment.from_file(path).export(
                str(out_path), format=output_format,
                parameters=["-q:a", "0"] if output_format == "mp3" else None
            )
            results[f'{stem}_stem'] = str(out_path)

    # 7. Default Case: No specific mute/drumless requested, but separate_audio was called.
    # Usually this is called for transcription (just need drums).
    # If no results yet, implies we just want the drums for processing or all stems were requested.
    if not results and not all_stems:
        # Default behavior: Just extract drums (for transcription)
        # We return the raw path (converted if necessary)
        drum_out_name = f"{input_path.stem}_drums.{output_format}"
        drum_out_path = base_output_dir / drum_out_name
        AudioSegment.from_file(stem_paths['drums']).export(
            str(drum_out_path), format=output_format
        )
        results['drums'] = str(drum_out_path)

    # Cleanup Temp Demucs Folder
    shutil.rmtree(temp_demucs_dir, ignore_errors=True)
    
    print(f"Separation complete. Outputs saved in: {base_output_dir}")
    return results



# ===============================================================================================
def extract_drum_stem(input_audio_path: str) -> str:
    """
    Legacy wrapper for the transcription pipeline.
    Separates a full audio track using the Demucs command-line tool
    and returns the file path to the isolated drum stem.
    
    :param input_audio_path: The file path to the user's full song.
    :type input_audio_path: str
    :return: The file path to the extracted 'drums.wav' stem.
    :rtype: str
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
    # print("\n# ------------------------------------------------------------------------------------")
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

# ===============================================================================================
def mix_stems(stems_dict, stems_to_mix, output_path, fmt="wav"):
    """
    Helper function to mix multiple audio files into one.
    
    :param stems_dict: Dictionary mapping stem names to file paths.
    :type stems_dict: dict
    :param stems_to_mix: List of stem names to combine.
    :type stems_to_mix: list
    :param output_path: Destination path.
    :type output_path: Path
    :param fmt: Output format ('wav' or 'mp3').
    :type fmt: str

    
    """
    if not stems_to_mix:
        return None

    # Load the first stem
    combined = AudioSegment.from_file(stems_dict[stems_to_mix[0]])

    # Overlay the rest
    for stem_name in stems_to_mix[1:]:
        if stem_name in stems_dict:
            track = AudioSegment.from_file(stems_dict[stem_name])
            combined = combined.overlay(track)
    
    # Export
    # For MP3, pydub uses ffmpeg backend. Quality '0' is best variable bit rate.
    combined.export(str(output_path), format=fmt, parameters=["-q:a", "0"] if fmt == "mp3" else None)
    return output_path

# ===============================================================================================
## Extended legacy orchestration script, ie before adding in the extraction/mute drums etc functionality, 
## Expanded with more advanced functionality for stem extraction

# --- Test harness ---
if __name__ == "__main__":
    """
    Allows the script to be run directly for testing.
    Default arguments if not specified otherwise are: .wav for output format, extract all stems and output all separately and NO concatenation of stems
    
    Usage:
        python drumscript/audio_processor/stem_splitter.py "path/to/song.mp3" (OR .wav, as required)
    """
    if len(sys.argv) < 2:
        # print("Usage: python stem_splitter.py <path_to_audio_file>")
        print("Usage: python stem_splitter.py <file> [--drumless] [--mp3] [--all]")
        sys.exit(1)
        
    input_file = sys.argv[1]
    
    if not Path(input_file).exists():
        print(f"Error: File not found at {input_file}")
        sys.exit(1)

    dl = "--drumless" in sys.argv
    mp3 = "--mp3" in sys.argv
    all_s = "--all" in sys.argv
    
    fmt = "mp3" if mp3 else "wav"
    separate_audio(input_file, output_format=fmt, drumless=dl, all_stems=all_s)

    ## The following block was for testing when the original demucs-extraction stem_splitter.py was built
    #temp_drum_file_path = None
    #temp_dir_to_clean = None
    # try:
        # Run the function
      #  temp_drum_file_path = extract_drum_stem(input_file)
        
        # On success, find the root temp directory
       # if temp_drum_file_path:
            # Path is .../temp_dir_xyz/htdemucs/song_name/drums.wav
            # We must delete the root temp directory, 3 levels up.
        #    temp_dir_to_clean = Path(temp_drum_file_path).parent.parent.parent
        #    print(f"\n--- TEST SUCCESSFUL ---")
        #    print(f"Drum file created at: {temp_drum_file_path}")
        #    print(f"Root temp directory: {temp_dir_to_clean}")

    # except Exception as e:
      #  print(f"\n--- TEST FAILED ---")
      #  print(f"An error occurred: {e}")
        
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

# ===============================================================================================