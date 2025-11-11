import subprocess
import time
import sys
from pathlib import Path

def test_flac_to_mp3_conversion(input_flac_path: str):
    """
    Tests the conversion time of a single FLAC file to MP3
    using the high-quality ffmpeg setting.
    """
    
    print("\n#=============================================================================================")
    print("--- Starting FLAC to MP3 Conversion Test ---")
    
    flac_file = Path(input_flac_path)
    if not flac_file.exists():
        print(f"Error: Input file not found at {flac_file}")
        return

    # Define the output file path (e.g., "drums.mp3")
    mp3_file = flac_file.with_suffix(".mp3")

    # This is the high-quality (and likely very slow) command
    # we are testing. -q:a 0 is VBR (Variable Bitrate) at max quality.
    convert_command = [
        "ffmpeg",
        "-i", str(flac_file),  # Input file
        "-q:a", "0",          # Set quality to highest VBR
        str(mp3_file),        # Output file
        "-y"                  # Overwrite output file if it exists
    ]

    print(f"Converting: {flac_file.name}")
    print(f"To:         {mp3_file.name}")
    print(f"Command:    {' '.join(convert_command)}")

    start_time = time.monotonic()
    
    try:
        # Run the conversion
        subprocess.run(convert_command, check=True, capture_output=True, text=True)
        
        end_time = time.monotonic()
        duration = end_time - start_time
        
        if mp3_file.exists():
            print("\n--- TEST SUCCESSFUL ---")
            print(f"File conversion finished in {duration:.2f} seconds.")
            print(f"Output file created at: {mp3_file}")
            # Clean up the created MP3 file
            mp3_file.unlink()
            print("Cleaned up test MP3 file.")
            print("\n#=============================================================================================")
        else:
            print("\n--- TEST FAILED ---")
            print("Conversion ran but output file was not created.")
            print("\n#=============================================================================================")

    except subprocess.CalledProcessError as e:
        print("\n--- TEST FAILED ---")
        print(f"FFmpeg command failed with error: {e.stderr}")
        print("\n#=============================================================================================")
    except FileNotFoundError:
        print("\n--- TEST FAILED ---")
        print("The 'ffmpeg' command was not found. Is it in your PATH?")
        print("\n#=============================================================================================")
    except Exception as e:
        print(f"\n--- TEST FAILED ---")
        print(f"An unexpected error occurred: {e}")
        print("\n#=============================================================================================")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_converter.py <path_to_your_flac_file>")
        sys.exit(1)
    
    test_flac_file = sys.argv[1]
    test_flac_to_mp3_conversion(test_flac_file)