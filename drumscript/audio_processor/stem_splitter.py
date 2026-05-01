# drumscript/audio_processor/stem_splitter.py
"""
This module uses the demucs library () to extract stems from multi-layer audio files. 
It also contains functionality for re-mixing stems to create drumless backing tracks for user export.
Running: `python3 -m drumscript.audio_processor.stem_splitter path_to_audio_file, <output_path>`
It supports generating 'drumless' tracks, isolating specific instruments, and format conversion on demand.
"""

import shutil
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf
from pydub import AudioSegment

# from datetime import datetime

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')

# Use 'htdemucs', the default (and high-quality) 4-stem model
# Stems output by htdemucs: 'drums', 'bass', 'other', 'vocals'
DEMUCS_MODEL = "htdemucs"

## PLEASE NOTE: Original Demucs is no longer being maintained (owned by Meta/Facebook). Owners have forked and maintain occasionally:
# https://github.com/adefossez/demucs. THe usage of demucs is therefore subject to some uncertainty. We may decide to build our own stem_splitter model
#  in DrumScript in order to ensure the long-term stability of the package, and to continue to make it as lightweight as possible.


### --- LEGACY CODE -- BEFORE FFMPEG DECOUPLING FROM STEM_SPLITTER
# Audio backend used by Demucs to LOAD input files.
# We force 'soundfile' to avoid pulling in torchcodec, which has a nasty habit of
# breaking on PyTorch ABI mismatches (symbol `_torch_dtype_float4_e2m1fn_x2` not
# found) and on missing Homebrew FFmpeg dylibs (libavutil.{56..59}.dylib).
# 'soundfile' handles WAV/FLAC natively; MP3 decoding still needs ffmpeg on PATH,
# which pydub also requires, so no new dependency is introduced.
# Valid values at the time of writing: "soundfile", "ffmpeg", "torchcodec".
# DEMUCS_BACKEND = "soundfile"


# ===============================================================================================
# Format-aware audio I/O helpers.
#
# Design goal: WAV output must be completely ffmpeg-free, so users who only
# want WAV never need ffmpeg on their system. MP3 output still requires
# ffmpeg (via pydub), which is unavoidable.
#
# - WAV path: uses `soundfile` (pure Python + libsndfile wheel) for read/write.
# - MP3 path: uses `pydub` which shells out to ffmpeg's LAME encoder.
# ===============================================================================================
def _read_stem_as_array(stem_path):
    """
    Read an audio stem (Demucs output) into a numpy array.

    Demucs writes WAV when we invoke it without --flac. soundfile reads WAV
    natively without needing ffmpeg.

    :param stem_path: Path to the stem file (typically .wav).
    :type stem_path: Path or str
    :return: Tuple of (audio_data as float32 numpy array, sample_rate as int).
    :rtype: tuple[np.ndarray, int]
    """
    data, sr = sf.read(str(stem_path), dtype="float32", always_2d=True)
    # always_2d=True ensures shape is (n_samples, n_channels) even for mono,
    # which keeps mixing code uniform.
    return data, sr


def _write_audio(audio_data, sample_rate, output_path, fmt="wav"):
    """
    Write a numpy audio array to disk in the requested format.

    Routes WAV to soundfile (no ffmpeg) and MP3 to pydub (needs ffmpeg).

    :param audio_data: Audio samples, shape (n_samples, n_channels), float32 in [-1, 1].
    :type audio_data: np.ndarray
    :param sample_rate: Sample rate in Hz.
    :type sample_rate: int
    :param output_path: Destination path.
    :type output_path: Path or str
    :param fmt: 'wav' or 'mp3'.
    :type fmt: str
    """
    output_path = str(output_path)

    if fmt == "wav":
        # soundfile writes WAV losslessly with no ffmpeg dependency.
        # subtype='PCM_16' matches Demucs's default output bit depth and keeps
        # files a sensible size (float32 WAV would be 2x bigger with no benefit
        # for end-user playback).
        sf.write(output_path, audio_data, sample_rate, subtype="PCM_16")

    elif fmt == "mp3":
        # MP3 encoding requires an encoder (LAME). pydub shells out to ffmpeg,
        # which brokers this for us. Convert numpy array -> pydub AudioSegment
        # -> MP3 file.
        # pydub expects int16 samples interleaved as bytes.
        samples_int16 = (audio_data * 32767).astype(np.int16)
        n_channels = samples_int16.shape[1] if samples_int16.ndim > 1 else 1
        segment = AudioSegment(
            samples_int16.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,  # 2 bytes = 16 bit
            channels=n_channels,
        )
        # '-q:a 0' = best quality VBR for LAME.
        segment.export(output_path, format="mp3", parameters=["-q:a", "0"])

    else:
        raise ValueError(f"Unsupported output format: {fmt!r}. Expected 'wav' or 'mp3'.")


# ===============================================================================================
def separate_audio(
    input_audio_path: str, output_format: str = "wav", drumless: bool = False, mute: list = None, all_stems: bool = False, output_dir: str = None
) -> dict:
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
    :param output_dir: Destination folder. Defaults to CWD/separated_stems, unless specified by user
    :type output_dir: str, optional
    :return: Dictionary of paths to generated files (e.g., ``{'drums': path, 'mix': path}``).
    :rtype: dict
    """
    input_path = Path(input_audio_path)
    if not input_path.exists():
        raise FileNotFoundError(f"Input audio path not found: {input_audio_path}")

    # 1. Define output dir. If no path specified in user a default director
    if output_dir is None:
        # base_output_dir = Path.cwd() / "processed_stems" / input_path.stem
        base_output_dir = Path.cwd() / input_path.stem
    else:
        base_output_dir = Path(output_dir) / input_path.stem

    base_output_dir.mkdir(parents=True, exist_ok=True)

    # Temp dir for raw demucs output(s)
    temp_demucs_dir = base_output_dir / "temp_demucs"

    print(f"Starting Demucs separation for: {input_path.name}...")
    start_time = time.monotonic()

    # 2. Run Demucs
    ### --- LEGACY_CODE (V1) --- BEFORE DECOUPLING FFMPEG FROM STEM_SPLITTER
    ## default command (no backend handling).
    # Crashed on torchcodec ABI.
    # command = [
    #     "demucs",
    #     "-o", str(temp_demucs_dir),
    #     "-n", DEMUCS_MODEL,
    #     "--flac",
    #     str(input_path)
    # ]
    #
    ### --- LEGACY_CODE (V2) --- BEFORE DECOUPLING FFMPEG FROM STEM_SPLITTER
    ## tried --backend soundfile. Demucs CLI doesn't support it.
    # command = [
    #     "demucs",
    #     "-o", str(temp_demucs_dir),
    #     "-n", DEMUCS_MODEL,
    #     "--flac",
    #     "--backend", DEMUCS_BACKEND,
    #     str(input_path)
    # ]
    #
    ### --- LEGACY_CODE (V3) --- BEFORE DECOUPLING FFMPEG FROM STEM_SPLITTER
    ## plain invocation but with --flac. Meant decoding the intermediate stems required ffmpeg (even
    ## when end user wanted WAV), because pydub had to decode FLAC. Removed --flac so Demucs writes
    ## WAV directly, which soundfile can read without ffmpeg.
    # command = [
    #     "demucs",
    #     "-o", str(temp_demucs_dir),
    #     "-n", DEMUCS_MODEL,
    #     "--flac",
    #     str(input_path)
    # ]
    #

    # Demucs writes WAV (its default). soundfile reads WAV without
    # ffmpeg, so the WAV output path through this module is now ffmpeg-free.
    command = ["demucs", "-o", str(temp_demucs_dir), "-n", DEMUCS_MODEL, str(input_path)]
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        shutil.rmtree(temp_demucs_dir, ignore_errors=True)
        # Surface BOTH stdout and stderr. Demucs writes the progress bar to stderr,
        # so the real error often sits at the END of stderr, not the start.
        # --- LEGACY: raise RuntimeError(f"Demucs failed: {e.stderr}")
        raise RuntimeError(f"Demucs failed (exit code {e.returncode}).\n--- STDOUT ---\n{e.stdout}\n--- STDERR ---\n{e.stderr}")
    except FileNotFoundError:
        raise FileNotFoundError("The 'demucs' command was not found. Please install it.")

    print(f"Demucs raw separation finished in {((time.monotonic() - start_time) / 60):.2f} minutes.")

    # 3. Locate Raw Stems
    # Demucs structure: output_dir / model_name / song_name / {stem}.flac
    raw_stem_dir = temp_demucs_dir / DEMUCS_MODEL / input_path.stem

    available_stems = ["drums", "bass", "other", "vocals"]
    stem_paths = {}

    for stem in available_stems:
        ### --- LEGACY_CODE --- BEFORE DECOUPLING FFMPEG FROM STEM_SPLITTER
        ## when we passed --flac to Demucs, stems were .flac.
        ## Demucs now writes .wav (its default) so we look for that extension.
        # path = raw_stem_dir / f"{stem}.flac"
        path = raw_stem_dir / f"{stem}.wav"
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
        stems_to_exclude.add("drums")

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
        results["mix"] = str(output_path)

        # The user requested: "saves the extracted element too"
        # So if we mute 'drums', we should also save the 'drums' stem separately.
        for excluded in stems_to_exclude:
            if excluded in stem_paths:
                stem_out_name = f"{input_path.stem}_only_{excluded}.{output_format}"
                stem_out_path = base_output_dir / stem_out_name
                ### --- LEGACY CODE -- BEFORE FFMPEG DECOUPLING FROM STEM_SPLITTER
                # pydub route (needs ffmpeg even for WAV output).
                # AudioSegment.from_file(stem_paths[excluded]).export(
                #     str(stem_out_path), format=output_format,
                #     parameters=["-q:a", "0"] if output_format == "mp3" else None
                # )
                # New route: soundfile for WAV (no ffmpeg), pydub only for MP3.
                audio_data, sr = _read_stem_as_array(stem_paths[excluded])
                _write_audio(audio_data, sr, stem_out_path, fmt=output_format)
                results[f"{excluded}_stem"] = str(stem_out_path)

    # 6. Handle "--all-stems"
    if all_stems:
        print("Exporting all individual stems...")
        for stem, path in stem_paths.items():
            # Avoid re-doing work if we already exported it in step 5
            expected_name = f"{input_path.stem}_only_{stem}.{output_format}"
            if (base_output_dir / expected_name).exists():
                continue

            out_path = base_output_dir / expected_name
            ### --- LEGACY CODE -- BEFORE FFMPEG DECOUPLING FROM STEM_SPLITTER
            #  pydub route.
            # AudioSegment.from_file(path).export(
            #     str(out_path), format=output_format,
            #     parameters=["-q:a", "0"] if output_format == "mp3" else None
            # )
            audio_data, sr = _read_stem_as_array(path)
            _write_audio(audio_data, sr, out_path, fmt=output_format)
            results[f"{stem}_stem"] = str(out_path)

    # 7. Default Case: No specific mute/drumless requested, but separate_audio was called.
    # Usually this is called for transcription (just need drums).
    # If no results yet, implies we just want the drums for processing or all stems were requested.
    if not results and not all_stems:
        # Default behaviour: Just extract drums (for transcription)
        # We return the raw path (converted if necessary)
        drum_out_name = f"{input_path.stem}_drums.{output_format}"
        drum_out_path = base_output_dir / drum_out_name
        ### --- LEGACY CODE -- BEFORE FFMPEG DECOUPLING FROM STEM_SPLITTER
        # AudioSegment.from_file(stem_paths['drums']).export(
        #     str(drum_out_path), format=output_format
        # )
        audio_data, sr = _read_stem_as_array(stem_paths["drums"])
        _write_audio(audio_data, sr, drum_out_path, fmt=output_format)
        results["drums"] = str(drum_out_path)

    # Cleanup Temp Demucs Folder
    shutil.rmtree(temp_demucs_dir, ignore_errors=True)

    print(f"Separation complete. Outputs saved in: {base_output_dir}")
    return results


# ===============================================================================================
# def extract_drum_stem(input_audio_path: str) -> str:
def extract_drum_stem(input_audio_path: str, output_dir: str = None) -> str:
    """
    Legacy wrapper for the transcription pipeline.
    Separates a full audio track using the Demucs command-line tool
    and returns the file path to the isolated drum stem.

    :param input_audio_path: The file path to the user's full song.
    :type input_audio_path: str
    :return: The file path to the extracted 'drums.wav' stem.
    :rtype: str
    """

    # 1. Define Output Directory
    ## If user does not specify output_dir in command then stores output(s) to cwd
    ## --- LEGACY_CODE ---
    ## Create a temporary directory to store the separation output.
    ## Use this for storing in /var/ folder on local machine, 'ie /var/folders/m0/_mjkpjps6lq_13m2l6sfckw40000gn/T/tmpp8b3ez_e/htdemucs/'
    ## MIGHT RESTORE THIS POST-TESTING

    # temp_output_dir = tempfile.mkdtemp()

    ### OR...

    # 1. Define a local output directory, ie put the outputs where you want them
    ## MIGHT COMMENT OUT AGAIN, POST-TESTING
    # output_dir = Path("./outputs/stems_test")

    if output_dir is None:
        # output_dir = Path.cwd() / "stems"
        output_dir = Path.cwd()
    else:
        output_dir = Path(output_dir)
    # Create the directory if it doesn't exist
    # output_dir.mkdir(parents=True, exist_ok=True)

    # Use this path as the output directory
    temp_output_dir = str(output_dir)

    # 2. Build the Demucs command
    # --- LEGACY CODE (v1): default command with --flac. Required ffmpeg to decode
    # --- the FLAC output; also had torchcodec crash issues (fixed by torch<2.9 pin).
    # command = [
    #     "demucs",
    #     "-o", str(temp_output_dir),
    #     "-n", DEMUCS_MODEL,
    #     "--flac",
    #     str(input_audio_path)
    # ]
    # --- LEGACY v2: tried --backend soundfile. Demucs CLI doesn't support it.
    # Current: plain invocation, Demucs writes WAV natively. No ffmpeg needed
    # for the drum extraction path.
    command = ["demucs", "-o", str(temp_output_dir), "-n", DEMUCS_MODEL, str(input_audio_path)]
    # 3. Run the Demucs separation process
    # print("\n# ------------------------------------------------------------------------------------")
    # print("\n# PLEASE NOTE: This is currently a test script. Original Demucs is no longer being maintained (owned by Meta/Facebook).
    # Owners have forked and maintain occasionally: https://github.com/adefossez/demucs. The usage of demucs is therefore subject to some uncertainty.
    #  We may decide to build our own stem_splitter model in DrumScript in order to ensure the long-term stability of the package, and to continue to
    # make it as lightweight as possible.")

    print(f"Starting Demucs separation for: {input_audio_path}...")

    ## ---- Timer block, might remove later --------------------------------------------------------------
    start_time = time.monotonic()  # Start timer, MIGHT REMOVE LATER ONCE FINISHED DEBUGGING

    try:
        subprocess.run(command, check=True, capture_output=True, text=True)

        end_time = time.monotonic()  # <-- 3. Stop the timer
        duration = end_time - start_time
        print(f"Demucs separation finished in {(duration / 60):.2f} minutes.")
    ## ----------------------------------------------------------------------------------------------------
    # --- Step 3.5 - Convert FLAC files to MP3 ---
    # --- LEGACY: FLAC-to-MP3 conversion block. Used to run when we passed
    # --- --flac to Demucs; the output was FLAC and we converted to MP3 via
    # --- a separate ffmpeg subprocess. Now Demucs outputs WAV directly, and
    # --- format conversion (when actually wanted) is handled by the calling
    # --- code via _write_audio(). This block is dead code kept for reference.
    # print("Converting stems to MP3...")
    # input_filename_stem = Path(input_audio_path).stem
    # stems_folder = Path(temp_output_dir) / DEMUCS_MODEL / input_filename_stem
    # flac_files = list(stems_folder.glob("*.flac"))
    # if not flac_files:
    #     print("Warning: No .flac files found to convert.")
    # for flac_file in flac_files:
    #     mp3_file = flac_file.with_suffix(".mp3")
    #     convert_command = [
    #         "ffmpeg",
    #         "-i", str(flac_file),
    #         "-q:a", "0",
    #         str(mp3_file),
    #         "-y",
    #     ]
    #     subprocess.run(convert_command, check=True, capture_output=True, text=True)
    # print(f"Successfully converted {len(flac_files)} stems to MP3.")

    except subprocess.CalledProcessError as e:
        # --- LEGACY: print(f"Demucs separation failed with error: {e.stderr}")
        # --- LEGACY: raise RuntimeError(f"Demucs failed to process the audio. Error: {e.stderr}")
        print(f"Demucs separation failed (exit code {e.returncode}).")
        print(f"--- STDOUT ---\n{e.stdout}")
        print(f"--- STDERR ---\n{e.stderr}")
        shutil.rmtree(temp_output_dir, ignore_errors=True)  # Clean up
        raise RuntimeError(f"Demucs failed to process the audio (exit {e.returncode}).\nSTDERR: {e.stderr}")

    except FileNotFoundError:
        shutil.rmtree(temp_output_dir, ignore_errors=True)  # Clean up
        raise FileNotFoundError("The 'demucs' command was not found. Is it installed correctly in your environment's PATH?")

    # 4. Find and return the path to the drum file
    input_filename_stem = Path(input_audio_path).stem

    # --- LEGACY: Demucs used to output FLAC because we passed --flac. Now it
    # --- writes WAV, which soundfile can read with no ffmpeg dependency.
    # expected_drum_path = Path(temp_output_dir) / DEMUCS_MODEL / input_filename_stem / "drums.flac"
    expected_drum_path = Path(temp_output_dir) / DEMUCS_MODEL / input_filename_stem / "drums.wav"

    if not expected_drum_path.exists():
        # shutil.rmtree(temp_output_dir, ignore_errors=True) # Clean up
        shutil.rmtree(temp_output_dir)  # Clean up
        raise FileNotFoundError(f"Demucs ran, but the drum output file was not found at {expected_drum_path}")

    print(f"Drum stem extracted successfully to: {expected_drum_path}")

    # Return the full path to the drum file.
    return str(expected_drum_path)


# ===============================================================================================
def mix_stems(stems_dict, stems_to_mix, output_path, fmt="wav"):
    """

    Uses soundfile + numpy so the WAV output path is ffmpeg-free. MP3 output
    still passes through pydub/ffmpeg via the _write_audio helper.

    :param stems_dict: Dictionary mapping stem names to file paths.
    :type stems_dict: dict
    :param stems_to_mix: List of stem names to combine.
    :type stems_to_mix: list
    :param output_path: Destination path, if provided by user, otherwise assumes cwd
    :type output_path: Path
    :param fmt: Output format ('wav' or 'mp3').
    :type fmt: str
    """
    # --- LEGACY v1: pydub-based mixing. Required ffmpeg to decode the .flac
    # --- intermediates produced by Demucs (we used to pass --flac), so even
    # --- WAV output paths were bottlenecked on ffmpeg. Now replaced by
    # --- numpy-based summation on WAV stems.
    # combined = AudioSegment.from_file(stems_dict[stems_to_mix[0]])
    # for stem_name in stems_to_mix[1:]:
    #     if stem_name in stems_dict:
    #         track = AudioSegment.from_file(stems_dict[stem_name])
    #         combined = combined.overlay(track)
    # combined.export(str(output_path), format=fmt,
    #                 parameters=["-q:a", "0"] if fmt == "mp3" else None)
    # return output_path

    # New approach: read each stem as a numpy array, sum them element-wise,
    # and clip to valid float range. Equivalent to pydub's overlay() for
    # our use case (stems from the same source, identical length and rate).
    first_stem_path = stems_dict[stems_to_mix[0]]
    mixed, sample_rate = _read_stem_as_array(first_stem_path)

    for stem_name in stems_to_mix[1:]:
        if stem_name not in stems_dict:
            continue
        track, sr = _read_stem_as_array(stems_dict[stem_name])
        # Sanity check: Demucs always outputs at the same sample rate and
        # length for all stems of a given input, so these should match.
        if sr != sample_rate:
            raise ValueError(f"Sample rate mismatch while mixing: {sample_rate} vs {sr} for stem {stem_name}. Cannot mix stems with different rates.")
        if track.shape != mixed.shape:
            raise ValueError(f"Shape mismatch while mixing: {mixed.shape} vs {track.shape} for stem {stem_name}.")
        mixed = mixed + track

    # Clip to [-1, 1] so samples stay in valid range if the summed stems
    # exceed full scale. (Simple clipping; for production-grade mixing you
    # might want gain reduction or a soft limiter, but clipping is what
    # pydub.overlay() effectively did too.)
    np.clip(mixed, -1.0, 1.0, out=mixed)

    _write_audio(mixed, sample_rate, output_path, fmt=fmt)
    return output_path


# ===============================================================================================
## Extended legacy orchestration script, ie before adding in the extraction/mute drums etc functionality,
## Expanded with more advanced functionality for stem extraction
if __name__ == "__main__":
    import argparse
    # from datetime import datetime

    ## Banner / timestamp (moved here from module top-level so it only fires when this file is run
    ## DIRECTLY via `python3 -m drumscript.audio_processor.stem_splitter ...`, not on every `from
    ## drumscript ## audio_processor.stem_splitter import ...`)

    # datetimestamp = datetime.now()
    # print("\n# ------------------------------------------------------------------------------------")
    # print(f'\ndate/time: {datetimestamp}')

    parser = argparse.ArgumentParser(description="Extract stems from an audio file.")
    parser.add_argument("input_file", help="Path to the input audio file.")
    parser.add_argument("-o", "--output_dir", default=None, help="Directory to save the stems.")
    parser.add_argument("--drumless", action="store_true", help="Generate a mix without drums.")
    parser.add_argument("--mp3", action="store_true", help="Output as MP3 instead of WAV.")
    parser.add_argument("--all", action="store_true", help="Export all individual stems.")

    args = parser.parse_args()

    if not Path(args.input_file).exists():
        print(f"Error: File not found at {args.input_file}")
        sys.exit(1)

    fmt = "mp3" if args.mp3 else "wav"

    separate_audio(input_audio_path=args.input_file, output_format=fmt, drumless=args.drumless, all_stems=args.all, output_dir=args.output_dir)
### --- LEGACY_CODE --- MAIN BLOCK
# if __name__ == "__main__":
#
# Allows the script to be run directly for testing.
# Default arguments if not specified otherwise are: .wav for output format, extract all stems and output all separately and NO concatenation of stems
#
# Usage:
#   python drumscript/audio_processor/stem_splitter.py "path/to/song.mp3" (OR .wav, as required)
#
# if len(sys.argv) < 2:
# print("Usage: python stem_splitter.py <path_to_audio_file>")
#    print("Usage: python stem_splitter.py <file> [--drumless] [--mp3] [--all]")
#    sys.exit(1)

# input_file = sys.argv[1]

# if not Path(input_file).exists():
#   print(f"Error: File not found at {input_file}")
#   sys.exit(1)

# dl = "--drumless" in sys.argv
# mp3 = "--mp3" in sys.argv
# all_s = "--all" in sys.argv

# --- LEGACY: this line was ACCIDENTALLY at module scope (not indented into
# --- the commented-out __main__ block), so it would NameError on every
# --- `import stem_splitter` because `mp3` is undefined here. Commented out.
# fmt = "mp3" if mp3 else "wav"
# separate_audio(input_file, output_format=fmt, drumless=dl, all_stems=all_s)

## The following block was for testing when the original demucs-extraction stem_splitter.py was built
# temp_drum_file_path = None
# temp_dir_to_clean = None
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
# finally:
# Clean up the temporary directory AFTER the test
# if temp_dir_to_clean and Path(temp_dir_to_clean).exists():
# try:
#   shutil.rmtree(temp_dir_to_clean)
#   print(f"Successfully cleaned up temporary directory.")
# except OSError as e:
#   print(f"Error cleaning up directory {temp_dir_to_clean}: {e}")
# else:
#   print("No temporary directory to clean up.")

# ===============================================================================================
