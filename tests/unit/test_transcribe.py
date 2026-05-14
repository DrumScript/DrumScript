"""
Unit tests for ``drumscript.transcribe`` — the high-level E2E wrapper.

What this file covers
---------------------
- Return-type contract (str vs dict depending on ``full`` flag).
- Output path construction (default and custom ``output_dir`` / ``output_filename``).
- Flag routing: ``is_rudiment`` dispatches to the correct classifier.
- Flag routing: ``full_song`` triggers stem separation.
- Error handling: missing input file.

What this file does NOT cover
-----------------------------
- Actual audio quality / classifier accuracy (that's integration-level).
- Real Demucs stem separation (slow, needs model download).

All heavy dependencies (load_audio, detect_onsets, classify_*, build_score,
extract_drum_stem) are mocked so these tests run in <1 second with no GPU,
no ffmpeg, no model weights.
"""

from unittest.mock import patch

import numpy as np
import pytest
import soundfile as sf

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def drum_wav(tmp_path):
    """Write a tiny WAV file to disk and return its path as a string."""
    sr = 22050
    audio = np.random.default_rng(0).random(sr, dtype=np.float32) * 0.5
    path = tmp_path / "test_drum.wav"
    sf.write(str(path), audio, sr)
    return str(path)


@pytest.fixture
def mock_pipeline():
    """
    Patch every heavy dependency that ``transcribe()`` calls internally.

    Yields a dict of the mock objects so individual tests can inspect
    call counts, call args, or override return values.
    """
    fake_onsets = np.array([0.0, 0.5, 1.0, 1.5])
    fake_events = [
        {
            "time_sec": t,
            "instruments": ["kick"],
            "debug_features": {"peak_freq": 80.0},
        }
        for t in fake_onsets
    ]

    patches = {
        "load": patch(
            "drumscript.load_audio",
            return_value=(np.zeros(22050, dtype=np.float32), 22050),
        ),
        "norm": patch(
            "drumscript.normalise_audio",
            side_effect=lambda y: y,
        ),
        "tempo": patch(
            "drumscript._internal_estimate",
            return_value=120.0,
        ),
        "onsets": patch(
            "drumscript.detect_onsets",
            return_value=fake_onsets,
        ),
        "classify": patch(
            "drumscript.classify_events",
            return_value=fake_events,
        ),
        "classify_rud": patch(
            "drumscript.classify_rudiment_events",
            return_value=fake_events,
        ),
        "build": patch(
            "drumscript.score_builder.build_score",
        ),
        "stem": patch(
            "drumscript.extract_drum_stem",
            side_effect=lambda p: p,  # returns same path
        ),
    }

    mocks = {}
    for key, p in patches.items():
        mocks[key] = p.start()

    yield mocks

    for p in patches.values():
        p.stop()


# =============================================================================
# Return type contract
# =============================================================================


class TestTranscribeReturnType:
    """``transcribe()`` returns a path string by default, or a dict if ``full=True``."""

    def test_returns_string_by_default(self, drum_wav, tmp_path, mock_pipeline):
        from drumscript import transcribe

        result = transcribe(drum_wav, output_dir=str(tmp_path))

        assert isinstance(result, str)
        assert result.endswith(".pdf")

    def test_returns_dict_when_full(self, drum_wav, tmp_path, mock_pipeline):
        from drumscript import transcribe

        result = transcribe(drum_wav, output_dir=str(tmp_path), full=True)

        assert isinstance(result, dict)
        assert "pdf_path" in result
        assert "tempo" in result
        assert "onsets" in result
        assert "events" in result
        assert "sample_rate" in result
        assert "time_signature" in result

    def test_full_dict_tempo_is_float(self, drum_wav, tmp_path, mock_pipeline):
        from drumscript import transcribe

        result = transcribe(drum_wav, output_dir=str(tmp_path), full=True)

        assert isinstance(result["tempo"], float)
        assert result["tempo"] == pytest.approx(120.0)


# =============================================================================
# Output path construction
# =============================================================================


class TestTranscribeOutputPaths:
    """Verify output directory creation and filename logic."""

    def test_default_output_filename(self, drum_wav, tmp_path, mock_pipeline):
        from drumscript import transcribe

        result = transcribe(drum_wav, output_dir=str(tmp_path))

        expected = str(tmp_path / "test_drum_transcription.pdf")
        assert result == expected

    def test_custom_output_filename(self, drum_wav, tmp_path, mock_pipeline):
        from drumscript import transcribe

        result = transcribe(
            drum_wav,
            output_dir=str(tmp_path),
            output_filename="my_score",
        )

        expected = str(tmp_path / "my_score.pdf")
        assert result == expected

    def test_creates_output_dir_if_missing(self, drum_wav, tmp_path, mock_pipeline):
        from drumscript import transcribe

        nested = tmp_path / "a" / "b" / "c"
        assert not nested.exists()

        transcribe(drum_wav, output_dir=str(nested))

        assert nested.exists()


# =============================================================================
# Flag routing
# =============================================================================


class TestTranscribeFlagRouting:
    """Verify that flags dispatch to the correct internal functions."""

    def test_rudiment_flag_calls_rudiment_classifier(self, drum_wav, tmp_path, mock_pipeline):
        from drumscript import transcribe

        transcribe(drum_wav, output_dir=str(tmp_path), is_rudiment=True)

        mock_pipeline["classify_rud"].assert_called_once()
        mock_pipeline["classify"].assert_not_called()

    def test_default_calls_standard_classifier(self, drum_wav, tmp_path, mock_pipeline):
        from drumscript import transcribe

        transcribe(drum_wav, output_dir=str(tmp_path), is_rudiment=False)

        mock_pipeline["classify"].assert_called_once()
        mock_pipeline["classify_rud"].assert_not_called()

    def test_full_song_triggers_stem_separation(self, drum_wav, tmp_path, mock_pipeline):
        from drumscript import transcribe

        transcribe(drum_wav, output_dir=str(tmp_path), full_song=True)

        mock_pipeline["stem"].assert_called_once()

    def test_no_full_song_skips_stem_separation(self, drum_wav, tmp_path, mock_pipeline):
        from drumscript import transcribe

        transcribe(drum_wav, output_dir=str(tmp_path), full_song=False)

        mock_pipeline["stem"].assert_not_called()

    def test_time_signature_forwarded_to_build_score(self, drum_wav, tmp_path, mock_pipeline):
        from drumscript import transcribe

        transcribe(drum_wav, output_dir=str(tmp_path), time_signature="6/8")

        call_kwargs = mock_pipeline["build"].call_args
        assert call_kwargs is not None
        # build_score is called with keyword args
        assert "6/8" in str(call_kwargs)

    def test_build_score_called_exactly_once(self, drum_wav, tmp_path, mock_pipeline):
        from drumscript import transcribe

        transcribe(drum_wav, output_dir=str(tmp_path))

        mock_pipeline["build"].assert_called_once()


# =============================================================================
# Error handling
# =============================================================================


class TestTranscribeErrors:
    """Verify clean error behaviour for bad inputs."""

    def test_missing_file_raises(self, tmp_path, mock_pipeline):
        from drumscript import transcribe

        with pytest.raises((FileNotFoundError, Exception)):
            transcribe(
                str(tmp_path / "does_not_exist.wav"),
                output_dir=str(tmp_path),
            )
