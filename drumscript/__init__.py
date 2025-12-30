# drumscript/__init__py
# This script serves to make drumscript module a Python package
# DrumScript: A Python-based suite of tools related to drum audio


# 1. Import internal functions
# We use 'noqa' or try/except blocks in some setups, but here direct import is fine...
# ...provided the dependencies (librosa, etc.) are installed.
from .audio_processor.audio_loader import load_audio, normalise_audio
from .audio_processor.stem_splitter import extract_drum_stem, separate_audio # includes new fct for creating drumless backing track
from .audio_processor.tempo_detector import estimate_tempo as _internal_estimate
from .notation_generator.constants import SAMPLE_RATE
from .utils.ffmpeg_installer import install_ffmpeg

# 2. Create user-friendly wrappers

# def stem_split(audio_path, output_dir=None, full=False):
def stem_split(audio_path, output_format="wav", drumless=False, mute=None, all_stems=False, full=False):
    """
    Public wrapper for stem splitting.

        Args:
        audio_path (str): Path to audio file.
        output_format (str): 'wav' or 'mp3'.
        drumless (bool): Extract a track with NO drums (plus the isolated drum track).
        mute (list): List of stems to mute (e.g. ['bass']).
        all_stems (bool): If True, export all separated stems individually.
        full (bool): Returns detailed dictionary if True.

    Please note: Currently, the internal engine uses a default output directory.
    The 'output_dir' argument is kept here for future API compatibility but
    is currently not passed to the underlying function to avoid errors.
    """
    # CALLING INTERNAL FUNCTION
    # Please note: `extract_drum_stem` ONLY accepts 'input_audio_path'. ie. It returns a string (the path to the file).
    result_path = extract_drum_stem(audio_path)

    results = separate_audio(
        input_audio_path=audio_path, 
        output_format=output_format, 
        drumless=drumless, 
        mute=mute, 
        all_stems=all_stems
    )

    if full:
        return {
            "status": "success",
            "drum_stem_path": result_path,
            "original_file": audio_path,
        }

    return result_path or results.get('drums') or results.get('drums_stem')


def tempo_detector(audio_input, full=False):
    """
    Public wrapper for tempo detection.

    Args:
        audio_input (str or np.array): File path OR loaded audio data.
        full (bool): Return detailed stats if True.
    """
    # Handle case where user passes a file path string
    if isinstance(audio_input, str):
        # Use internal drumscript loader which returns tuple (audio, sr), imported directly from drumscript/notation_generator/constants.py as single source of truth throughout package
        y, sr = load_audio(audio_input, sr=SAMPLE_RATE)
        y = normalise_audio(y)
    else:
        # Assume it's already loaded audio data (array)
        y = audio_input
        sr = SAMPLE_RATE # SAMPLE_RATE variable loaded from notation_generator/constants.py to maintain single source of truth

    # CALLING INTERNAL FUNCTION
    bpm = _internal_estimate(y, sr)

    if full:
        return {"bpm": bpm, "sr": sr}
    return bpm


# 3. Expose them to the top level
__all__ = ["stem_split", "tempo_detector", "install_ffmpeg"]
