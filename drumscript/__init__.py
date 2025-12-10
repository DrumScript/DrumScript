# drumscript/__init__py
# This script serves to make drumscript module a Python package

# DrumScript: A Python-based suite of tools related to drum audio


# 1. Import internal functions
# We use 'noqa' or try/except blocks in some setups, but here direct import is fine
# provided the dependencies (librosa, etc.) are installed.
from .audio_processor.audio_loader import load_audio, normalise_audio
from .audio_processor.stem_splitter import extract_drum_stem
from .audio_processor.tempo_detector import estimate_tempo as _internal_estimate
from .notation_generator.constants import SAMPLE_RATE
from .utils.ffmpeg_installer import install_ffmpeg

# 2. Create the user-friendly wrappers


def stem_split(audio_path, output_dir=None, full=False):
    """
    Public wrapper for stem splitting.

    NOTE: Currently, the internal engine uses a default output directory.
    The 'output_dir' argument is kept here for future API compatibility but
    is currently not passed to the underlying function to avoid errors.
    """
    # CALLING INTERNAL FUNCTION
    # Your current extract_drum_stem ONLY accepts 'input_audio_path'.
    # It returns a string (the path to the file).
    result_path = extract_drum_stem(audio_path)

    if full:
        return {
            "status": "success",
            "drum_stem_path": result_path,
            "original_file": audio_path,
        }

    return result_path


def tempo_detector(audio_input, full=False):
    """
    Public wrapper for tempo detection.

    Args:
        audio_input (str or np.array): File path OR loaded audio data.
        full (bool): Return detailed stats if True.
    """
    # Handle case where user passes a file path string
    if isinstance(audio_input, str):
        # We use your internal loader which returns (audio, sr)
        y, sr = load_audio(audio_input, sr=SAMPLE_RATE)
        y = normalise_audio(y)
    else:
        # Assume it's already loaded audio data (array)
        # Note: Your internal estimate_tempo needs (audio, sr).
        # Since we don't know the SR of the array passed, we default to 44100
        # or you could require a tuple (y, sr) as input.
        y = audio_input
        # sr = 44100
        sr = SAMPLE_RATE

    # CALLING INTERNAL FUNCTION
    bpm = _internal_estimate(y, sr)

    if full:
        return {"bpm": bpm, "sr": sr}
    return bpm


# 3. Expose them to the top level
__all__ = ["stem_split", "tempo_detector", "install_ffmpeg"]
