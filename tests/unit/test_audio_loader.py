"""
Unit tests for ``drumscript.audio_processor.audio_loader``.

What this file covers
---------------------
- ``normalise_audio``: pure numpy, fully testable in isolation.
- ``load_audio``: requires a real file on disk, but we use ``tmp_path`` so
  no real audio fixtures need to be checked into the repo.

What this file does NOT cover
-----------------------------
- The ``__main__`` block of audio_loader.py (CLI entry point). Test CLI
  behaviour separately if/when you decide it's worth it; for now,
  testing the underlying functions is much higher value.
"""

import numpy as np
import pytest
import soundfile as sf

from drumscript.audio_processor.audio_loader import load_audio, normalise_audio

# =============================================================================
# normalise_audio
# =============================================================================


class TestNormaliseAudio:
    """
    Tests for ``normalise_audio``.

    Grouped into a class purely for readability — pytest treats each method
    as a separate test. Class-level grouping makes it easier to spot which
    tests cover which function, especially as files grow.
    """

    def test_normalises_to_unit_peak(self):
        """A non-silent signal should be scaled so its peak is exactly 1.0."""
        audio = np.array([0.0, 0.5, -0.25, 0.1], dtype=np.float32)
        result = normalise_audio(audio)
        assert np.isclose(np.max(np.abs(result)), 1.0)

    def test_handles_empty_array(self):
        """Empty input must return empty output without error."""
        audio = np.array([], dtype=np.float32)
        result = normalise_audio(audio)
        assert result.size == 0

    def test_handles_silent_audio(self):
        """All-zeros input must return all-zeros (no division by zero)."""
        audio = np.zeros(100, dtype=np.float32)
        result = normalise_audio(audio)
        # Silent stays silent — the function must not blow up on a zero peak.
        np.testing.assert_array_equal(result, audio)

    def test_preserves_relative_amplitudes(self):
        """The ratio between any two samples must be unchanged after scaling."""
        audio = np.array([0.0, 0.2, -0.4, 0.1], dtype=np.float32)
        result = normalise_audio(audio)
        # If sample[1]/sample[2] is preserved, the function is doing
        # uniform gain (correct) rather than something funky like clipping.
        assert np.isclose(result[1] / result[2], audio[1] / audio[2])

    def test_already_normalised_audio_unchanged(self):
        """Audio whose peak is already 1.0 should come back identical."""
        audio = np.array([1.0, -1.0, 0.5, -0.5], dtype=np.float32)
        result = normalise_audio(audio)
        np.testing.assert_array_almost_equal(result, audio)

    def test_negative_only_audio(self):
        """A signal with only negative values should still normalise to peak 1.0."""
        audio = np.array([-0.1, -0.5, -0.3], dtype=np.float32)
        result = normalise_audio(audio)
        # The peak |sample| is 0.5, so after normalisation it should hit -1.0.
        assert np.isclose(np.min(result), -1.0)
        assert np.isclose(np.max(np.abs(result)), 1.0)

    @pytest.mark.parametrize(
        "input_array,expected_peak",
        [
            (np.array([0.001, 0.002, -0.0015]), 1.0),  # tiny signal scales up
            (np.array([1000.0, -2000.0, 500.0]), 1.0),  # huge signal scales down
            (np.array([0.5, -0.5]), 1.0),  # already at half scale
        ],
    )
    def test_peak_is_always_one_for_nonzero_audio(self, input_array, expected_peak):
        """
        Regardless of input scale, output peak should always be 1.0.

        Parametrized to cover three orders of magnitude in one test function.
        Pytest will report each case as a separate test result.
        """
        result = normalise_audio(input_array.astype(np.float32))
        assert np.isclose(np.max(np.abs(result)), expected_peak)


# =============================================================================
# load_audio
# =============================================================================


class TestLoadAudio:
    """Tests for ``load_audio``."""

    def test_loads_existing_wav(self, small_wav_file, sine_wave):
        """
        Round-trip a known WAV through the loader and verify shape + rate.

        Uses two fixtures:
        - ``small_wav_file``: writes the sine wave to a temp path
        - ``sine_wave``: gives us the original audio + rate to compare against
        """
        _, original_sr = sine_wave
        audio, sr = load_audio(str(small_wav_file), sr=original_sr)

        assert sr == original_sr
        assert audio.shape[0] > 0
        # Loaded audio should be reasonably close in length to what we wrote.
        # (Resampling can shift things by a sample or two; allow a small slack.)
        assert abs(audio.shape[0] - original_sr) < 100

    def test_raises_on_missing_file(self):
        """Missing file must raise FileNotFoundError, not silently return None."""
        with pytest.raises(FileNotFoundError):
            load_audio("/nonexistent/path/to/audio.wav")

    def test_resamples_when_target_sr_differs(self, tmp_path):
        """
        Loading at a different sample rate should actually resample.

        We write a 1-second file at 44100 Hz, load at 22050 Hz, and expect
        the loaded array to be roughly half the original length.
        """
        original_sr = 44100
        target_sr = 22050
        # 1 second of low-amplitude noise — content doesn't matter, just length.
        audio = np.random.uniform(-0.3, 0.3, original_sr).astype(np.float32)
        path = tmp_path / "test_resample.wav"
        sf.write(str(path), audio, original_sr)

        result_audio, result_sr = load_audio(str(path), sr=target_sr)

        assert result_sr == target_sr
        # Half the rate => roughly half the samples.
        # Allow a small tolerance for librosa's resampling algorithm.
        assert abs(result_audio.shape[0] - original_sr // 2) < 100

    def test_loaded_audio_is_numpy_float(self, small_wav_file, sine_wave):
        """
        Output dtype must be a numpy float type.

        Downstream code (normalise, librosa feature extractors, etc.) all
        assume float input. If load_audio ever started returning int16,
        every downstream function would silently produce nonsense.
        """
        _, original_sr = sine_wave
        audio, _ = load_audio(str(small_wav_file), sr=original_sr)
        assert audio.dtype.kind == "f"  # 'f' = floating point
