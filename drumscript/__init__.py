# drumscript/__init__.py

"""
DrumScript: A Python-based suite of tools for drum audio analysis and transcription.

This top-level module exposes the primary high-level wrappers for end-to-end
transcription, as well as the core low-level building blocks for custom DSP pipelines.
"""

import pathlib

# from pathlib import Path
# 1. Import internal functions
from .audio_processor.audio_loader import load_audio, normalise_audio
from .audio_processor.feature_extractor import extract_features
from .audio_processor.onset_detector import detect_onsets
from .audio_processor.stem_splitter import extract_drum_stem, separate_audio
from .audio_processor.tempo_detector import estimate_tempo as _internal_estimate
from .drum_classifier.classify import classify_events, classify_rudiment_events
from .notation_generator import midi_exporter, pdf_exporter, score_builder, xml_exporter
from .notation_generator.constants import SAMPLE_RATE
from .notation_generator.score_builder import build_score
from .utils.ffmpeg_installer import install_ffmpeg


# 2. Create user-friendly wrappers
def extract_stems(audio_path, output_dir=None, output_format="wav", drumless=False, mute=None, all_stems=False, full=False):
    """
    Extracts drum stems and optionally separates the full track into constituent parts.

    This function serves as a high-level wrapper around the Demucs source separation model.
    It allows for quick isolation of drum tracks for transcription, or the creation of
    "drumless" backing tracks for practice.

    :param audio_path: Path to the input audio file.
    :type audio_path: str
    :param output_dir: Directory to save the output files. Defaults to current working directory.
    :type output_dir: str, optional
    :param output_format: Export format, 'wav' or 'mp3'. Defaults to 'wav'.
    :type output_format: str, optional
    :param drumless: If True, extracts a track with NO drums (plus the isolated drum track).
    :type drumless: bool, optional
    :param mute: List of specific stems to mute (e.g., ['bass', 'vocals']).
    :type mute: list, optional
    :param all_stems: If True, exports all separated stems individually.
    :type all_stems: bool, optional
    :param full: If True, returns a detailed dictionary of all output paths.
    :type full: bool, optional

    :return: Path to the extracted file, or a dictionary of results if full=True.
    :rtype: str or dict

    .. note::
       Source separation is computationally heavy. On a standard CPU, extracting stems
       from a 3-minute song may take a few minutes.

    **Examples:**

    Extract just the drum stem to the current directory:

    .. code-block:: python

       import drumscript as ds
       drum_path = ds.extract_stems("my_song.mp3")

    Create a drumless backing track in MP3 format:

    .. code-block:: python

       results = ds.extract_stems(
           "my_song.mp3",
           drumless=True,
           output_format="mp3",
           full=True
       )
       print(f"Backing track saved to: {results['mix']}")
    """
    if output_dir is None:
        output_dir = pathlib.Path.cwd() / "stems"
    else:
        output_dir = pathlib.Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # result_path = extract_drum_stem(audio_path, output_dir=str(output_dir))

    # results = separate_audio(
    #   audio_path=audio_path, output_format=output_format, drumless=drumless, mute=mute, all_stems=all_stems, output_dir=str(output_dir)

    results = separate_audio(
        audio_path=audio_path,
        output_format=output_format,
        drumless=drumless,
        mute=mute,
        all_stems=all_stems,
        output_dir=str(output_dir),
    )

    # drum_path = results.get("drums") or results.get("drums_stem")

    # if full:
    #   return {"status": "success", "drum_stem_path": result_path, "original_file": audio_path,
    # "output_directory": str(output_dir)}

    drum_path = results.get("drums") or results.get("drums_stem")
    if full:
        return {
            "status": "success",
            "drum_stem_path": drum_path,
            "original_file": audio_path,
            "output_directory": str(output_dir),
        }
    # return result_path or results.get("drums") or results.get("drums_stem")
    return drum_path

    # if full:
    #   return {
    #       "status": "success",
    #       "drum_stem_path": results.get("drums") or results.get("drums_stem"),
    #       "original_file": audio_path,
    #       "output_directory": str(output_dir),
    #   }

    # return results.get("drums") or results.get("drums_stem")


def detect_tempo(audio_path, full=False):
    """
    Estimates the global tempo (BPM) of a given audio file or pre-loaded audio array.

    This function utilizes spectral onset envelope detection to accurately
    estimate the global tempo of a percussive track.

    :param audio_path: File path (str) OR a pre-loaded audio data array (np.ndarray).
    :type audio_path: str or np.ndarray
    :param full: Return a detailed stats dictionary instead of just the float if True.
    :type full: bool, optional

    :return: The estimated BPM, or a dictionary containing the BPM and sample rate.
    :rtype: float or dict

    .. note::
       Passing a pre-loaded ``np.ndarray`` is significantly faster if you are running
       multiple analysis functions on the exact same audio file.

    **Examples:**

    Detect tempo directly from a file:

    .. code-block:: python

       import drumscript as ds
       bpm = ds.detect_tempo("drum_loop.wav")
       print(f"Tempo: {bpm} BPM")

    Detect tempo from a pre-loaded array:

    .. code-block:: python

       y, sr = ds.load_audio("drum_loop.wav")
       stats = ds.detect_tempo(y, full=True)
       print(stats['bpm'])
    """
    if isinstance(audio_path, str):
        y, sr = load_audio(audio_path, sr=SAMPLE_RATE)
        # y, sr = load_audio(audio_path)
        y = normalise_audio(y)
    else:
        y = audio_path
        sr = SAMPLE_RATE

    bpm = _internal_estimate(y, sr)

    if full:
        return {"bpm": bpm, "sr": sr}
    return bpm


def transcribe(
    audio_path,
    *,
    full_song=False,
    time_signature="4/4",
    is_rudiment=False,
    output_dir="outputs",
    output_filename=None,
    full=False,
):
    """
    Run the full DrumScript transcription pipeline end-to-end.

    Loads audio → optionally extracts the drum stem → detects tempo and onsets →
    classifies hits → builds the score → writes PDF output.

    :param audio_path: Path to the input audio file (full song or isolated drum stem).
    :type audio_path: str
    :param full_song: If True, run Demucs stem separation first to isolate the drum
        track. Set to False if your input is already an isolated drum stem.
    :type full_song: bool, optional
    :param time_signature: Time signature string in 'N/D' form (e.g. '4/4', '6/8').
    :type time_signature: str, optional
    :param is_rudiment: If True, use the simpler classifier optimised for isolated
        single beats and rudiments rather than full polyphonic drum patterns.
    :type is_rudiment: bool, optional
    :param output_dir: Directory to save the PDF output. Created if it doesn't exist.
        Defaults to 'outputs/'.
    :type output_dir: str, optional
    :param output_filename: Output filename without extension. Defaults to
        '<input_stem>_transcription'.
    :type output_filename: str, optional
    :param full: If True, return a dict with all intermediate results (tempo, onsets,
        events, paths) instead of just the PDF path.
    :type full: bool, optional

    :return: Path to the generated PDF, or a dict of full results if full=True.
    :rtype: str or dict

    **Examples:**

    Quick transcription of an isolated drum stem:

    .. code-block:: python

       import drumscript as ds
       pdf = ds.transcribe("drum_loop.wav")

    Full song with stem separation, custom output, full results:

    .. code-block:: python

       result = ds.transcribe(
           "full_song.mp3",
           full_song=True,
           time_signature="6/8",
           output_dir="./my_transcriptions",
           full=True,
       )
       print(f"PDF: {result['pdf_path']}")
       print(f"Detected tempo: {result['tempo']:.1f} BPM")
       print(f"Onsets: {len(result['onsets'])}")
    """
    audio_path = str(audio_path)
    input_stem = pathlib.Path(audio_path).stem

    # Validate input exists before doing anything
    if not pathlib.Path(audio_path).exists():
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    # 1. Stem separation (optional)
    working_path = audio_path
    if full_song:
        print("...Separating drum stem...")
        working_path = extract_drum_stem(audio_path)

    # 2. Load + normalise
    print("...Loading & analysing audio...")
    # y, sr = load_audio(working_path)
    y, sr = load_audio(working_path, sr=SAMPLE_RATE)
    y = normalise_audio(y)

    # 3. Tempo + onsets
    # tempo = estimate_tempo(y, sr)
    tempo = _internal_estimate(y, sr)
    onsets = detect_onsets(y, sr)
    print(f"   -> Tempo: {tempo:.1f} BPM | Onsets: {len(onsets)}")

    # 4. Classify
    if is_rudiment:
        print("   -> Classifier: rudiment / single-beat engine")
        classified_events = classify_rudiment_events(y, sr, onsets)
    else:
        print("   -> Classifier: standard polyphonic engine")
        classified_events = classify_events(y, sr, onsets)
    print(f"   -> Classified {len(classified_events)} events")

    # 5. Re-shape events for the score builder
    detected_events = [
        {
            "time_sec": ev["time_sec"],
            "instruments": ev["instruments"],
            "debug_features": ev["debug_features"],
        }
        for ev in classified_events
    ]

    # 6. Build & export
    output_dir = pathlib.Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    fname = output_filename or f"{input_stem}_transcription"
    pdf_path = output_dir / f"{fname}.pdf"

    print(f"...Building score: {pdf_path}")
    score_builder.build_score(
        detected_events=detected_events,
        tempo=tempo,
        output_path=str(pdf_path),
        time_signature=time_signature,
    )
    print("--- Done ---")

    if full:
        return {
            "pdf_path": str(pdf_path),
            "audio_path": audio_path,
            "drum_stem_path": working_path if full_song else None,
            "tempo": tempo,
            "onsets": onsets,
            "events": detected_events,
            "time_signature": time_signature,
            "sample_rate": sr,
        }
    return str(pdf_path)


def export_pdf(score, output_path=None, **kwargs):
    """
    Exports a generated DrumScript score object to a beautifully rendered PDF file.

    This function utilizes the ReportLab engine to generate clean, vector-based
    sheet music optimized for standard A4 printing.

    :param score: The internal score object generated by ``build_score()``.
    :type score: object
    :param output_path: The exact file path to save the PDF. Defaults to 'drumscript.pdf' in CWD.
    :type output_path: str, optional
    :return: The absolute path to the generated PDF.
    :rtype: str

    .. note::
       Because the PDF is generated using vector graphics, it can be scaled infinitely
       without any loss of quality or pixelation.

    **Example:**

    .. code-block:: python

       import drumscript as ds

       # Assuming `score` is a previously generated score object
       pdf_path = ds.export_pdf(score, output_path="./transcriptions/my_song.pdf")
    """
    if output_path is None:
        # output_path = pathlib.Path.cwd() / "drum_score.pdf"
        output_path = pathlib.Path.cwd() / "drumscript.pdf"

    return pdf_exporter.export_pdf(score, output_path=output_path, **kwargs)


def export_midi(score, output_path=None, **kwargs):
    """
    Converts a DrumScript score object into a standard MIDI file for DAW integration.

    The exported MIDI file adheres to the General MIDI (GM) Level 1 Percussion Key Map,
    ensuring immediate compatibility with virtual drum instruments like Superior Drummer,
    EZdrummer, or standard DAW drum racks.

    :param score: The internal score object generated by ``build_score()``.
    :type score: object
    :param output_path: The exact file path to save the MIDI. Defaults to 'drumscript.mid' in CWD.
    :type output_path: str, optional

    :return: The absolute path to the generated MIDI file.
    :rtype: str

    **Example:**

    .. code-block:: python

       import drumscript as ds

       # Assuming `score` is a previously generated score object
       midi_path = ds.export_midi(score, output_path="./midi_exports/my_song.mid")
    """
    if output_path is None:
        # output_path = pathlib.Path.cwd() / "drum_score.mid"
        output_path = pathlib.Path.cwd() / "drumscript.mid"

    return midi_exporter.export_to_midi(score, output_path=output_path, **kwargs)


def export_xml(score, output_path=None, **kwargs):
    """
    Exports a DrumScript score object to MusicXML format.

    MusicXML is the universal industry standard for sharing digital sheet music.
    Generating an XML file allows you to seamlessly import your DrumScript
    transcription into professional notation software like Sibelius, Finale,
    MuseScore, or Guitar Pro for further editing.

    :param score: The internal score object generated by ``build_score()``.
    :type score: object
    :param output_path: The exact file path to save the XML. Defaults to 'drumscript.xml' in CWD.
    :type output_path: str, optional

    :return: The absolute path to the generated XML file.
    :rtype: str

    .. note::
       When importing MusicXML into MuseScore, you may need to right-click the staff
       and select "Edit Drumset" to map the custom noteheads to your preference.

    **Example:**

    .. code-block:: python

       import drumscript as ds

       # Assuming `score` is a previously generated score object
       xml_path = ds.export_xml(score, output_path="./xml_scores/my_song.xml")
    """
    if output_path is None:
        output_path = pathlib.Path.cwd() / "drumscript.xml"

    return xml_exporter.export_xml(score, output_path=output_path, **kwargs)


# 3. Explicitly define the Public API (Used by Sphinx and `from drumscript import *`)
__all__ = [
    # High-level wrappers
    "transcribe",
    "extract_stems",
    "detect_tempo",
    "export_pdf",
    "export_midi",
    "export_xml",
    # Core DSP & Classification pipeline
    "load_audio",
    "normalise_audio",
    "detect_onsets",
    "extract_features",
    "classify_events",
    "classify_rudiment_events",
    "build_score",
    # Utilities
    "install_ffmpeg",
]

__version__ = "0.1.3"
