# drumscript/__init__py

"""
DrumScript: A Python-based suite of tools for drum audio analysis and transcription.
"""

# 1. Import internal functions
# We use 'noqa' or try/except blocks in some setups, but here direct import is fine, provided the dependencies (librosa, etc.) are installed.
from .audio_processor.audio_loader import load_audio
from .audio_processor.audio_loader import normalise_audio
from .audio_processor.stem_splitter import extract_drum_stem
from .audio_processor.stem_splitter import separate_audio
from .audio_processor.tempo_detector import estimate_tempo as _internal_estimate
from .notation_generator.constants import SAMPLE_RATE
from .utils.ffmpeg_installer import install_ffmpeg
from .drum_classifier.classify import classify_events
from .notation_generator.score_builder import build_score
from .notation_generator.pdf_exporter import export_pdf

# 2. Create user-friendly wrappers

# def stem_split(audio_path, output_dir=None, full=False):
def extract_stems(audio_path, output_format="wav", drumless=False, mute=None, all_stems=False, full=False):
    """
    Public wrapper for stem splitting.

    :param audio_path: Path to the audio file.
    :type audio_path: str
    :param output_format: 'wav' or 'mp3', defaults to 'wav'.
    :type output_format: str, optional
    :param drumless: Extract a track with NO drums (plus the isolated drum track).
    :type drumless: bool, optional
    :param mute: List of stems to mute (e.g. ['bass']).
    :type mute: list, optional
    :param all_stems: If True, export all separated stems individually.
    :type all_stems: bool, optional
    :param full: Returns detailed dictionary if True.
    :type full: bool, optional
    :return: Path to the extracted file or a dictionary of results if full=True.
    :rtype: str or dict

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


def detect_tempo(audio_input, full=False):
    """
    Public wrapper for tempo detection.

    :param audio_input: File path OR loaded audio data.
    :type audio_input: str or np.ndarray
    :param full: Return detailed stats if True.
    :type full: bool, optional
    :return: The estimated BPM (float) or a dictionary of stats.
    :rtype: float or dict
    
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
__all__ = [
    "detect_tempo",
    "detect_onsets",
    "classify_events",
    "build_score",
    "detect_tempo",
    "export_pdf",
    "extract_stems",
    "extract_features",
    "install_ffmpeg",
    "load_audio",
    "separate_stems",
]

__version__ = "0.1.2"