"""
Integration tests for ``drumscript.transcribe`` and the CLI entry point.

What's special about this file
------------------------------
Unlike ``tests/unit/test_transcribe.py``, **nothing is mocked here**. Audio is
really loaded, onsets are really detected, events are really classified, and
PDF/JSON/MIDI files are really written to disk.

That matters because the unit tests mock ``build_score``, so they can only
prove *"transcribe() reports what build_score tells it"*. They cannot prove
the files actually appear on disk. These tests close that gap.

Two tiers
---------
``TestTranscribeRealAudio`` and ``TestBuildScoreRealOutputs`` use a synthesised
**drum-only** loop, so Demucs is never invoked. They are marked ``integration``
but **not** ``slow`` — they finish in seconds and therefore still run under
``pytest -m "not slow"`` (which is what CI uses). This gives the v0.2.0
``_TranscribeResult`` change genuine end-to-end coverage in CI.

``TestCliStemFlagsReal`` **does** invoke Demucs and is marked ``slow`` as well,
plus skipped entirely when the ``demucs`` CLI is not on PATH.

Why this file exists
--------------------
v0.2.0 changed two things that unit tests cannot fully verify:

1. ``transcribe()`` now returns ``_TranscribeResult`` reporting PDF/JSON/MIDI.
   Only a real run proves those three files exist.
2. The CLI's stem flags (``--drumless`` / ``--all-stems`` / ``--mute``) were
   moved out of an error handler and into the primary path. Before the fix
   they silently did nothing on the happy path.

How to run
----------
::

    pytest tests/integration/test_transcribe_real.py -v   # this file
    pytest -m "not slow"                                  # includes the fast tier
    pytest -m integration                                 # everything here
"""

import shutil
import warnings
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

import drumscript as ds

DEMUCS_AVAILABLE = shutil.which("demucs") is not None

# Applies to every test in the module. Individual classes add `slow` on top
# where they actually need Demucs.
pytestmark = pytest.mark.integration


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def drum_only_loop(tmp_path_factory):
    """A synthesised **drum-only** loop: kick on beats, snare on offbeats.

    Drum-only means ``transcribe()`` can run with ``full_song=False``, so no
    stem separation and no Demucs. Module-scoped so it is generated once.

    Deliberately synthetic: these tests assert on *plumbing* (were the files
    written, are the paths reported) rather than transcription accuracy, which
    would make them brittle. Accuracy belongs in the benchmark suite.
    """
    sr = 44100
    duration_s = 4.0
    n_samples = int(sr * duration_s)
    rng = np.random.default_rng(seed=42)
    audio = np.zeros(n_samples, dtype=np.float32)

    # Kick every 0.5s (120 BPM)
    for t in np.arange(0, duration_s, 0.5):
        start = int(t * sr)
        decay_len = int(sr * 0.15)
        env = np.exp(-np.linspace(0, 5, decay_len))
        kick = np.sin(2 * np.pi * 60 * np.linspace(0, decay_len / sr, decay_len)) * env * 0.6
        end = min(start + decay_len, n_samples)
        audio[start:end] += kick[: end - start].astype(np.float32)

    # Snare on the offbeats
    for t in np.arange(0.25, duration_s, 0.5):
        start = int(t * sr)
        decay_len = int(sr * 0.10)
        env = np.exp(-np.linspace(0, 8, decay_len))
        snare = (rng.uniform(-0.5, 0.5, decay_len) * env).astype(np.float32)
        end = min(start + decay_len, n_samples)
        audio[start:end] += snare[: end - start]

    tmp_dir = tmp_path_factory.mktemp("integration_transcribe_audio")
    path = tmp_dir / "drum_only_loop.wav"
    sf.write(str(path), audio, sr)
    return path


# =============================================================================
# transcribe() end-to-end — no Demucs required
# =============================================================================


class TestTranscribeRealAudio:
    """Real end-to-end runs of ``ds.transcribe()`` on drum-only audio."""

    def test_writes_all_three_output_files(self, drum_only_loop, tmp_path):
        """The three reported paths must exist on disk after a real run."""
        result = ds.transcribe(str(drum_only_loop), output_dir=str(tmp_path))

        assert "pdf_path" in result
        assert "json_path" in result
        assert "midi_path" in result

        for key in ("pdf_path", "json_path", "midi_path"):
            path = Path(result[key])
            assert path.exists(), f"{key} was reported but not written: {path}"
            assert path.stat().st_size > 0, f"{key} was written but is empty: {path}"

    def test_reported_paths_have_correct_extensions(self, drum_only_loop, tmp_path):
        result = ds.transcribe(str(drum_only_loop), output_dir=str(tmp_path))

        assert result["pdf_path"].endswith(".pdf")
        assert result["json_path"].endswith(".json")
        assert result["midi_path"].endswith(".mid")

    def test_json_output_is_valid_and_populated(self, drum_only_loop, tmp_path):
        """The JSON sidecar should parse and contain the classified events."""
        import json

        result = ds.transcribe(str(drum_only_loop), output_dir=str(tmp_path))

        with open(result["json_path"]) as f:
            events = json.load(f)

        assert isinstance(events, list)
        assert len(events) > 0, "No events written to JSON — classification produced nothing"
        assert "time_sec" in events[0]
        assert "instruments" in events[0]

    def test_result_still_behaves_as_string_with_deprecation(self, drum_only_loop, tmp_path):
        """The v0.2.0 back-compat shim: str() works but warns."""
        result = ds.transcribe(str(drum_only_loop), output_dir=str(tmp_path))

        with pytest.warns(DeprecationWarning, match="pdf_path"):
            as_string = str(result)

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            assert Path(str(result)).exists()
        assert as_string.endswith(".pdf")

    def test_os_pathlike_interface_works(self, drum_only_loop, tmp_path):
        """``__fspath__`` should let the result be used anywhere a path is."""
        import os

        result = ds.transcribe(str(drum_only_loop), output_dir=str(tmp_path))

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            assert os.path.exists(result)

    def test_verbose_returns_real_analysis_data(self, drum_only_loop, tmp_path):
        """``verbose=True`` should carry genuine tempo/onset/event data."""
        result = ds.transcribe(str(drum_only_loop), output_dir=str(tmp_path), verbose=True)

        assert isinstance(result["tempo"], float)
        assert result["tempo"] > 0
        assert len(result["onsets"]) > 0
        assert len(result["events"]) > 0
        assert result["sample_rate"] > 0
        assert result["time_signature"] == "4/4"
        assert Path(result["pdf_path"]).exists()

    def test_custom_output_filename_is_honoured(self, drum_only_loop, tmp_path):
        result = ds.transcribe(
            str(drum_only_loop),
            output_dir=str(tmp_path),
            output_filename="my_custom_score",
        )

        assert Path(result["pdf_path"]).name == "my_custom_score.pdf"
        assert Path(result["json_path"]).name == "my_custom_score.json"
        assert Path(result["midi_path"]).name == "my_custom_score.mid"
        assert Path(result["pdf_path"]).exists()

    def test_creates_nested_output_dir(self, drum_only_loop, tmp_path):
        nested = tmp_path / "a" / "b" / "c"
        assert not nested.exists()

        result = ds.transcribe(str(drum_only_loop), output_dir=str(nested))

        assert nested.exists()
        assert Path(result["pdf_path"]).parent == nested

    def test_custom_time_signature_runs_end_to_end(self, drum_only_loop, tmp_path):
        result = ds.transcribe(str(drum_only_loop), output_dir=str(tmp_path), time_signature="6/8")

        assert Path(result["pdf_path"]).exists()

    def test_missing_file_raises_before_any_work(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            ds.transcribe(str(tmp_path / "nope.wav"), output_dir=str(tmp_path))


# =============================================================================
# build_score() written-path contract — no Demucs required
# =============================================================================


class TestBuildScoreRealOutputs:
    """``build_score()`` reports exactly the files it wrote (v0.2.0, #7)."""

    def test_returns_all_three_paths_on_success(self, tmp_path):
        from drumscript.notation_generator import score_builder

        events = [
            {"time_sec": 0.0, "instruments": ["kick"], "debug_features": {}},
            {"time_sec": 0.5, "instruments": ["snare"], "debug_features": {}},
        ]
        out = tmp_path / "score.pdf"

        written = score_builder.build_score(
            detected_events=events,
            tempo=120.0,
            output_path=str(out),
        )

        assert isinstance(written, dict), "build_score should return a dict of written paths"
        for key in ("pdf_path", "json_path", "midi_path"):
            assert key in written, f"{key} missing from build_score return"
            assert Path(written[key]).exists(), f"{key} reported but not on disk"

    def test_every_reported_path_actually_exists(self, tmp_path):
        """The core guarantee: never report a file that was not written."""
        from drumscript.notation_generator import score_builder

        events = [{"time_sec": 0.0, "instruments": ["kick"], "debug_features": {}}]
        written = score_builder.build_score(
            detected_events=events,
            tempo=100.0,
            output_path=str(tmp_path / "guarantee.pdf"),
        )

        missing = [k for k, v in written.items() if not Path(v).exists()]
        assert missing == [], f"build_score reported paths that do not exist: {missing}"


# =============================================================================
# CLI stem flags — requires Demucs
# =============================================================================


@pytest.mark.slow
@pytest.mark.skipif(not DEMUCS_AVAILABLE, reason="demucs CLI not found on PATH")
class TestCliStemFlagsReal:
    """The v0.2.0 fix: stem flags must work on the happy path, not only after an error.

    Before the fix these flags were handled *inside* an ``except`` block, so
    ``drumscript song.mp3 --drumless`` ran the transcription pipeline, succeeded,
    and exited without ever producing a backing track — silently.
    """

    def test_drumless_produces_backing_track_and_no_score(self, drum_only_loop, tmp_path, monkeypatch):
        from drumscript import main as ds_main

        monkeypatch.chdir(tmp_path)
        ds_main.main(str(drum_only_loop), drumless=True)

        produced = list(tmp_path.rglob("*no_drums*"))
        assert produced, "No drumless backing track was produced"

        # Stems-only was requested, so transcription must not have run.
        assert list(tmp_path.rglob("*_transcription.pdf")) == []

    def test_all_stems_produces_stem_files(self, drum_only_loop, tmp_path, monkeypatch):
        from drumscript import main as ds_main

        monkeypatch.chdir(tmp_path)
        ds_main.main(str(drum_only_loop), all_stems=True)

        stems = list(tmp_path.rglob("*.wav"))
        assert len(stems) >= 4, f"Expected at least 4 stem files, found {len(stems)}"

    def test_full_song_transcribes_after_separation(self, drum_only_loop, tmp_path, monkeypatch):
        from drumscript import main as ds_main

        monkeypatch.chdir(tmp_path)
        ds_main.main(str(drum_only_loop), full_song=True)

        assert list(tmp_path.rglob("*_transcription.pdf")), "No score produced for --full-song"
