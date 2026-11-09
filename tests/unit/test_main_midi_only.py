"""
Tests for ``--midi-only`` / ``midi_only=True``.

What this file pins
-------------------
- ``midi_only`` reaches ``score_builder.build_score`` from both entry points,
  the CLI via ``main()`` and the Python API via ``transcribe()``.
- ``build_score`` honours it: the MIDI export still runs, the JSON and PDF
  exports do not, and the returned mapping reports only what was written.
- The pipeline itself is unchanged. Onsets are still detected and hits still
  classified, because a MIDI file of drum notes cannot exist without that work.

Why it is written this way
--------------------------
``midi_only`` is deliberately a pass-through, not a separate code path. There
is one transcription pipeline and one place that decides which files to write.
So these tests assert the value arrives at ``build_score`` and that
``build_score`` acts on it, rather than asserting on a parallel branch.

That is the difference from the original #348 implementation, which ran its own
copy of the pipeline inside ``export_midi``. If a second pipeline ever
reappears, ``test_midi_only_still_runs_the_normal_pipeline`` below fails.
"""

import json
from unittest.mock import patch

import pytest

import drumscript as ds
from drumscript.main import main
from drumscript.notation_generator import score_builder

# LEGACY CODE FROM #348 -- KEEP FOR NOW DURING ALPHA: the previous version of this file asserted that ``main()``
# called ``export_midi(..., from_audio=True)`` and returned early, bypassing the
# pipeline entirely. That design has been replaced by a flag on the existing
# pipeline, so the assertion no longer describes the code. Kept per convention.
#
# from unittest.mock import patch
#
# from drumscript.main import main
#
#
# def test_midi_only_exports_midi_without_running_normal_pipeline(capsys):
#     with patch(
#         "drumscript.main.export_midi",
#         return_value="outputs/song.mid",
#     ) as mock_export:
#         main(
#             "song.wav",
#             full_song=True,
#             is_rudiment=True,
#             midi_only=True,
#         )
#
#     mock_export.assert_called_once_with(
#         "song.wav",
#         from_audio=True,
#         full_song=True,
#         is_rudiment=True,
#     )
#
#     captured = capsys.readouterr()
#     assert "MIDI-only export complete: outputs/song.mid" in captured.out
#     assert "Starting DrumScript" not in captured.out


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def events():
    """A minimal set of classified events, enough for build_score to write a file."""
    return [
        {"time_sec": 0.000, "instruments": ["kick"], "debug_features": {}},
        {"time_sec": 0.500, "instruments": ["snare"], "debug_features": {}},
        {"time_sec": 1.000, "instruments": ["kick"], "debug_features": {}},
    ]


# =============================================================================
# build_score: the one place that decides which files are written
# =============================================================================


class TestBuildScoreMidiOnly:
    """``build_score`` is where ``midi_only`` actually does something."""

    def test_writes_only_midi(self, events, tmp_path):
        """Under midi_only, the .mid is written and the .json and .pdf are not."""
        # Arrange
        output_path = tmp_path / "song.pdf"

        # Act
        written = score_builder.build_score(detected_events=events, tempo=120.0, output_path=str(output_path), midi_only=True)

        # Assert
        assert (tmp_path / "song.mid").is_file(), "the MIDI file is the whole point and must still be written"
        assert not (tmp_path / "song.json").exists(), "JSON must be skipped under midi_only"
        assert not (tmp_path / "song.pdf").exists(), "PDF must be skipped under midi_only"
        assert set(written) == {"midi_path"}, f"only midi_path should be reported, got {sorted(written)}"

    def test_writes_all_three_by_default(self, events, tmp_path):
        """Without the flag, nothing changes. This is the regression guard."""
        # Arrange
        output_path = tmp_path / "song.pdf"

        # Act
        written = score_builder.build_score(detected_events=events, tempo=120.0, output_path=str(output_path))

        # Assert
        assert (tmp_path / "song.mid").is_file()
        assert (tmp_path / "song.json").is_file()
        assert "midi_path" in written
        assert "json_path" in written

    def test_midi_is_identical_with_and_without_the_flag(self, events, tmp_path):
        """
        midi_only must not change the MIDI itself, only suppress the other writes.

        Quantisation happens before any export, so the same events reach the MIDI
        exporter either way. If this ever fails, the flag has leaked into the
        musical logic, which it must never do.
        """
        # Arrange / Act
        full_dir = tmp_path / "full"
        midi_dir = tmp_path / "midi"
        full_dir.mkdir()
        midi_dir.mkdir()

        score_builder.build_score(detected_events=list(events), tempo=120.0, output_path=str(full_dir / "song.pdf"))
        score_builder.build_score(detected_events=list(events), tempo=120.0, output_path=str(midi_dir / "song.pdf"), midi_only=True)

        # Assert
        assert (full_dir / "song.mid").read_bytes() == (midi_dir / "song.mid").read_bytes()

    def test_quantisation_still_happens(self, events, tmp_path):
        """
        The events are still quantised in midi_only mode.

        Proven via the JSON from a normal run compared against the event list the
        midi_only run mutated in place, since build_score quantises before it writes.
        """
        # Arrange
        normal_events = [dict(e) for e in events]
        midi_only_events = [dict(e) for e in events]

        # Act
        score_builder.build_score(detected_events=normal_events, tempo=120.0, output_path=str(tmp_path / "a.pdf"))
        score_builder.build_score(detected_events=midi_only_events, tempo=120.0, output_path=str(tmp_path / "b.pdf"), midi_only=True)

        # Assert
        assert [e["time_sec"] for e in normal_events] == [e["time_sec"] for e in midi_only_events]
        on_disk = json.loads((tmp_path / "a.json").read_text())
        assert [e["time_sec"] for e in on_disk] == [e["time_sec"] for e in midi_only_events]


# =============================================================================
# The two entry points: both must forward the flag, neither may fork the pipeline
# =============================================================================


class TestMidiOnlyReachesBuildScore:
    """``midi_only`` is a pass-through. These tests pin that it passes through."""

    def test_main_forwards_midi_only(self, tmp_path):
        """The CLI path hands the flag to build_score rather than acting on it itself."""
        # Arrange
        audio = tmp_path / "song.wav"
        audio.write_bytes(b"")

        # Act
        with (
            patch("drumscript.main.audio_loader.load_audio", return_value=([0.0], 44100)),
            patch("drumscript.main.audio_loader.normalise_audio", return_value=[0.0]),
            patch("drumscript.main.tempo_detector.estimate_tempo", return_value=120.0),
            patch("drumscript.main.onset_detector.detect_onsets", return_value=[0.0]),
            patch("drumscript.main.classify_events", return_value=[]),
            patch("drumscript.main.score_builder.build_score") as mock_build,
        ):
            main(str(audio), midi_only=True)

        # Assert
        assert mock_build.call_args.kwargs["midi_only"] is True

    def test_main_defaults_to_false(self, tmp_path):
        """Omitting it leaves the existing three-file behaviour untouched."""
        # Arrange
        audio = tmp_path / "song.wav"
        audio.write_bytes(b"")

        # Act
        with (
            patch("drumscript.main.audio_loader.load_audio", return_value=([0.0], 44100)),
            patch("drumscript.main.audio_loader.normalise_audio", return_value=[0.0]),
            patch("drumscript.main.tempo_detector.estimate_tempo", return_value=120.0),
            patch("drumscript.main.onset_detector.detect_onsets", return_value=[0.0]),
            patch("drumscript.main.classify_events", return_value=[]),
            patch("drumscript.main.score_builder.build_score") as mock_build,
        ):
            main(str(audio))

        # Assert
        assert mock_build.call_args.kwargs["midi_only"] is False

    def test_transcribe_forwards_midi_only(self, tmp_path):
        """The Python API path does the same."""
        # Arrange
        audio = tmp_path / "song.wav"
        audio.write_bytes(b"")

        # Act
        with (
            patch("drumscript.load_audio", return_value=([0.0], 44100)),
            patch("drumscript.normalise_audio", return_value=[0.0]),
            patch("drumscript._internal_estimate", return_value=120.0),
            patch("drumscript.detect_onsets", return_value=[0.0]),
            patch("drumscript.classify_events", return_value=[]),
            patch("drumscript.score_builder.build_score", return_value={"midi_path": "outputs/song.mid"}) as mock_build,
        ):
            result = ds.transcribe(str(audio), midi_only=True, output_dir=str(tmp_path), verbose=True)

        # Assert
        assert mock_build.call_args.kwargs["midi_only"] is True
        assert result["midi_path"] == "outputs/song.mid"
        assert result["pdf_path"] is None, "a skipped PDF must not be reported as written"

    def test_midi_only_still_runs_the_normal_pipeline(self, tmp_path):
        """
        The guard against the #348 design returning.

        midi_only must not bypass onset detection or classification. If someone
        reintroduces a shortcut that skips them, this fails.
        """
        # Arrange
        audio = tmp_path / "song.wav"
        audio.write_bytes(b"")

        # Act
        with (
            patch("drumscript.load_audio", return_value=([0.0], 44100)),
            patch("drumscript.normalise_audio", return_value=[0.0]),
            patch("drumscript._internal_estimate", return_value=120.0),
            patch("drumscript.detect_onsets", return_value=[0.0]) as mock_onsets,
            patch("drumscript.classify_events", return_value=[]) as mock_classify,
            patch("drumscript.score_builder.build_score", return_value={"midi_path": "outputs/song.mid"}),
        ):
            ds.transcribe(str(audio), midi_only=True, output_dir=str(tmp_path), verbose=True)

        # Assert
        mock_onsets.assert_called_once()
        mock_classify.assert_called_once()
