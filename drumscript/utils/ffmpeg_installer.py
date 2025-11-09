# DrumScript/utils/ffmpeg_installer.py

import os
import platform
import subprocess
import shutil

def is_ffmpeg_installed() -> bool:
    """
    Checks if FFmpeg is installed and accessible in the system's PATH.

    Returns:
        bool: True if FFmpeg (ffmpeg and ffprobe) is found, False otherwise.
    """
    # Check for 'ffmpeg' executable
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        print(f"FFmpeg executable found at: {ffmpeg_path}")
    else:
        print("FFmpeg executable not found in PATH.")
        return False

    # Also check for 'ffprobe' as it's often used alongside ffmpeg by librosa/pydub
    ffprobe_path = shutil.which("ffprobe")
    if ffprobe_path:
        print(f"FFprobe executable found at: {ffprobe_path}")
    else:
        print("FFprobe executable not found in PATH.")
        return False

    # Optional: Verify FFmpeg version by running it
    try:
        # Run ffmpeg -version and check for non-zero exit code
        subprocess.run(["ffmpeg", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("FFmpeg seems to be working correctly.")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("FFmpeg found but is not runnable or encountered an error. It might be corrupted or improperly installed.")
        return False

def install_ffmpeg() -> None:
    """
    Checks for FFmpeg installation and provides OS-specific instructions if not found.
    For Linux/macOS, it can offer to attempt an installation via package manager (requires sudo).
    For Windows, it provides manual download instructions.

    This function is intended to be called by the user or a setup script,
    not as an automatic silent installer due to permission requirements.
    """
    print("\n--- Checking for FFmpeg installation ---")

    if is_ffmpeg_installed():
        print("FFmpeg is already installed and detected in your system's PATH.")
        print("You are ready to process all audio file types with DrumScript.")
        return

    print("\nFFmpeg is NOT detected in your system's PATH.")
    print("FFmpeg is required by DrumScript to process MP3 and other non-WAV audio files.")
    print("WAV files can usually be processed without FFmpeg.")

    system = platform.system()

    if system == "Linux":
        print("\n--- Installation instructions for Linux (Debian/Ubuntu-based) ---")
        print("1. Update package lists:")
        print("   sudo apt update")
        print("2. Install FFmpeg:")
        print("   sudo apt install ffmpeg")
        user_choice = input("Attempt to install FFmpeg using 'sudo apt install ffmpeg' now? (y/N): ").lower()
        if user_choice == 'y':
            try:
                print("Attempting to run: sudo apt install ffmpeg...")
                # Use shell=True for sudo commands to work as expected, but be cautious
                subprocess.run(["sudo", "apt", "install", "-y", "ffmpeg"], check=True)
                print("\nFFmpeg installation attempt finished. Please re-run this check.")
                print("You may need to restart your terminal for PATH changes to take effect.")
            except subprocess.CalledProcessError as e:
                print(f"Error during automated FFmpeg installation: {e}")
                print("Please try installing manually using the commands above.")
            except FileNotFoundError:
                print("Apt command not found. Are you on a Debian/Ubuntu-based system?")
                print("Please install FFmpeg manually for your specific Linux distribution.")
        else:
            print("Please install FFmpeg manually using the instructions above.")

    elif system == "Darwin": # macOS
        print("\n--- Installation instructions for macOS (using Homebrew) ---")
        print("1. Install Homebrew (if you don't have it):")
        print("   /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
        print("2. Install FFmpeg using Homebrew:")
        print("   brew install ffmpeg")
        user_choice = input("Attempt to install FFmpeg using 'brew install ffmpeg' now? (y/N): ").lower()
        if user_choice == 'y':
            try:
                print("Attempting to run: brew install ffmpeg...")
                subprocess.run(["brew", "install", "ffmpeg"], check=True)
                print("\nFFmpeg installation attempt finished. Please re-run this check.")
                print("You may need to restart your terminal for PATH changes to take effect.")
            except subprocess.CalledProcessError as e:
                print(f"Error during automated FFmpeg installation: {e}")
                print("Please try installing manually using the commands above.")
            except FileNotFoundError:
                print("Homebrew command not found. Is Homebrew installed?")
                print("Please install FFmpeg manually using the instructions above.")
        else:
            print("Please install FFmpeg manually using the instructions above.")

    elif system == "Windows":
        print("\n--- Installation instructions for Windows ---")
        print("1. Download FFmpeg binaries from the official website:")
        print("   Go to https://ffmpeg.org/download.html")
        print("   Click on the Windows icon and then select a 'release build' provider (e.g., gyan.dev or BtbN).")
        print("2. Extract the downloaded ZIP file to a location like C:\\ffmpeg.")
        print("   You should have a folder structure like C:\\ffmpeg\\bin containing ffmpeg.exe, ffprobe.exe, etc.")
        print("3. Add the 'bin' folder (e.g., C:\\ffmpeg\\bin) to your System PATH environment variable.")
        print("   - Search for 'Environment Variables' in Windows search bar.")
        print("   - Click 'Edit the system environment variables'.")
        print("   - Click 'Environment Variables...' button.")
        print("   - Under 'System variables', find and select the 'Path' variable, then click 'Edit...'.")
        print("   - Click 'New' and paste the path to your FFmpeg 'bin' folder (e.g., C:\\ffmpeg\\bin).")
        print("   - Click 'OK' on all dialogs.")
        print("4. Restart your Command Prompt/PowerShell or IDE to ensure PATH changes take effect.")
        print("\nOnce installed, re-run 'drumscript.install_ffmpeg()' to verify.")

    else:
        print(f"\n--- Installation instructions for {system} ---")
        print("Please consult your operating system's documentation for installing FFmpeg.")
        print("You can typically find pre-built binaries on https://ffmpeg.org/download.html")
        print("Ensure FFmpeg executables (ffmpeg, ffprobe) are added to your system's PATH.")

    print("\n--- FFmpeg check complete ---")

# You would ideally put this function in DrumScript/utils/ffmpeg_installer.py
# and then expose it via DrumScript/__init__.py for easy import.