"""
DrumScript: A Python-based suite of tools related to drum audio
"""

# 1. Import internal functions
from .audio_processor.audio_loader import load_audio, normalise_audio
from .audio_processor.stem_splitter import extract_drum_stem
from .audio_processor.tempo_detector import estimate_tempo as _internal_estimate
from .utils.ffmpeg_installer import install_ffmpeg


# 2. Create the user-friendly wrappers
def stem_split(audio_path, output_dir=".", full=False):
    """
    Public wrapper for stem splitting.
    """
    return extract_drum_stem(audio_path, output_dir=output_dir, full=full)


def tempo_detector(audio_input, full=False):
    """
    Public wrapper for tempo detection.

    Args:
        audio_input (str or np.array): File path OR loaded audio data.
        full (bool): Return detailed stats if True.
    """
    # Handle case where user passes a file path string
    if isinstance(audio_input, str):
        y, sr = load_audio(audio_input, sr=44100)
        y = normalise_audio(y)
    else:
        # Assume it's already loaded audio data (tuple or array)
        # Note: Your internal estimate_tempo needs (audio, sr)
        # If input is just data, we assume default SR or user must provide it.
        # For simplicity here, let's assume file path usage as primary.
        y = audio_input
        sr = 44100

    bpm = _internal_estimate(y, sr)

    if full:
        return {"bpm": bpm, "sr": sr}
    return bpm


# 3. Expose them to the top level
__all__ = ["stem_split", "tempo_detector", "install_ffmpeg"]
