"""
Unit tests for the helpers in ``drumscript.audio_processor.stem_splitter``.

What this file covers
---------------------
- ``_read_stem_as_array``: WAV → numpy round-trip (no ffmpeg).
- ``_write_audio`` (WAV path only): numpy → WAV (no ffmpeg).
- ``mix_stems``: combines multiple stems into one output.

What this file does NOT cover
-----------------------------
- ``_write_audio`` MP3 path: requires ffmpeg → integration test.
- ``extract_drum_stem`` and ``separate_audio``: shell out to Demucs →
  integration test (or unit test with subprocess.run mocked).

REGRESSION TEST WARNING
-----------------------
``test_mix_stems_actually_mixes_all_stems`` is a regression test for the
``mix_stems`` indentation bug fixed on 28 April 2026. The bug caused only
the first stem to ever be mixed in (the rest of the for-loop body had
fallen out of the loop). This test would have caught it on the first
``pytest`` run — please don't delete it, even if it looks "obvious".
"""

import numpy as np
import pytest
import soundfile as sf

from drumscript.audio_processor.stem_splitter import (
    _read_stem_as_array,
    _write_audio,
    mix_stems,
)

# =============================================================================
# _read_stem_as_array
# =============================================================================


class TestReadStemAsArray:
    """Tests for the private ``_read_stem_as_array`` helper."""

    def test_reads_wav_to_float32(self, small_wav_file):
        """The returned array must be float32 — Demucs and downstream math expect it."""
        data, sr = _read_stem_as_array(small_wav_file)
        assert data.dtype == np.float32

    def test_returns_2d_array_for_mono_input(self, small_wav_file):
        """
        ``always_2d=True`` is set explicitly in the implementation. This test
        asserts that even mono input comes back with shape ``(n_samples, 1)``,
        which keeps mixing code uniform across mono and stereo files.
        """
        data, _ = _read_stem_as_array(small_wav_file)
        assert data.ndim == 2
        # The fixture is mono, so channel count should be 1.
        assert data.shape[1] == 1

    def test_returns_correct_sample_rate(self, small_wav_file, sine_wave):
        """Sample rate should round-trip exactly through the file."""
        _, expected_sr = sine_wave
        _, actual_sr = _read_stem_as_array(small_wav_file)
        assert actual_sr == expected_sr

    def test_accepts_string_path_and_pathlib_path(self, small_wav_file):
        """Both ``str`` and ``Path`` inputs should work — soundfile is fussy here."""
        # Path object
        data1, sr1 = _read_stem_as_array(small_wav_file)
        # String
        data2, sr2 = _read_stem_as_array(str(small_wav_file))

        np.testing.assert_array_equal(data1, data2)
        assert sr1 == sr2


# =============================================================================
# _write_audio (WAV path only)
# =============================================================================


class TestWriteAudioWav:
    """
    Tests for the WAV output path of ``_write_audio``.

    MP3 path is not tested here — it goes through pydub/ffmpeg and belongs
    in integration tests.
    """

    def test_writes_wav_file(self, tmp_path, stereo_constant_audio):
        """Basic round-trip: write a numpy array, file should exist."""
        audio, sr = stereo_constant_audio
        output = tmp_path / "out.wav"

        _write_audio(audio, sr, output, fmt="wav")

        assert output.exists()
        assert output.stat().st_size > 0

    def test_round_trip_preserves_sample_rate(self, tmp_path, stereo_constant_audio):
        """Sample rate should survive write→read unchanged."""
        audio, sr = stereo_constant_audio
        output = tmp_path / "out.wav"

        _write_audio(audio, sr, output, fmt="wav")
        loaded, loaded_sr = sf.read(str(output), always_2d=True)

        assert loaded_sr == sr

    def test_round_trip_preserves_amplitude_approximately(self, tmp_path, stereo_constant_audio):
        """
        Round-trip should preserve sample values to within 16-bit quantisation.

        We write as PCM_16 (per the implementation), so we expect a tiny
        amount of quantisation loss but not actual signal change.
        """
        audio, sr = stereo_constant_audio
        output = tmp_path / "out.wav"

        _write_audio(audio, sr, output, fmt="wav")
        loaded, _ = sf.read(str(output), always_2d=True)

        # 16-bit quantisation ≈ 1/32768 ≈ 3e-5. Use 1e-4 to be safe.
        np.testing.assert_allclose(loaded, audio, atol=1e-4)

    def test_invalid_format_raises(self, tmp_path, stereo_constant_audio):
        """Unknown format strings should error explicitly."""
        audio, sr = stereo_constant_audio
        output = tmp_path / "out.xyz"

        with pytest.raises(ValueError, match="Unsupported"):
            _write_audio(audio, sr, output, fmt="xyz")

    def test_accepts_string_and_path_outputs(self, tmp_path, stereo_constant_audio):
        """Both ``str`` and ``Path`` outputs should be accepted."""
        audio, sr = stereo_constant_audio

        # Path
        out1 = tmp_path / "a.wav"
        _write_audio(audio, sr, out1, fmt="wav")
        # String
        out2 = tmp_path / "b.wav"
        _write_audio(audio, sr, str(out2), fmt="wav")

        assert out1.exists()
        assert out2.exists()


# =============================================================================
# mix_stems  ← THE BIG ONE
# =============================================================================


class TestMixStems:
    """
    Tests for ``mix_stems``.

    The first test below is a **regression test** for a real bug that
    shipped (the for-loop indentation issue). Keep it forever.
    """

    # ---------------- Regression tests ----------------

    def test_mix_stems_actually_mixes_all_stems(self, tmp_path, stem_files):
        """
        REGRESSION: ensure all stems contribute to the mix, not just the first.

        Background: a previous version of mix_stems had an indentation bug
        that caused the for-loop body to fall out of the loop entirely. As a
        result, only the first stem was ever read; the rest were silently
        dropped. The output looked plausible (a real WAV file) but was
        missing 2/3 of the audio.

        Test design: the three stems have distinct constant amplitudes
        (0.1, 0.2, 0.3) so we can detect exactly which ones got mixed in by
        looking at the output's mean amplitude. Only-first-stem behaviour
        gives mean ≈ 0.1; correct behaviour gives mean ≈ 0.6.
        """
        output = tmp_path / "mix.wav"

        mix_stems(stem_files, ["drums", "bass", "vocals"], output, fmt="wav")

        mixed, _ = sf.read(str(output), always_2d=True)
        actual_mean = float(np.mean(np.abs(mixed)))

        # Sum of amplitudes is 0.6. PCM_16 quantisation gives some slack;
        # 0.5 is well above the only-first-stem result of ~0.1 and below
        # the correct value of 0.6, so we use 0.5 as a robust threshold.
        assert actual_mean > 0.5, (
            f"Expected mixed mean amplitude near 0.6 (sum of all three stems), "
            f"got {actual_mean:.4f}. This usually means not all stems were "
            f"summed — check the for-loop in mix_stems for indentation bugs."
        )

    # ---------------- Happy-path tests ----------------

    def test_creates_output_file(self, tmp_path, stem_files):
        """The most basic check: an output WAV is actually written."""
        output = tmp_path / "mix.wav"
        mix_stems(stem_files, ["drums", "bass"], output, fmt="wav")
        assert output.exists()
        assert output.stat().st_size > 0

    def test_returns_output_path(self, tmp_path, stem_files):
        """The function should return the path to the file it wrote."""
        output = tmp_path / "mix.wav"
        result = mix_stems(stem_files, ["drums", "bass"], output, fmt="wav")
        assert result == output

    def test_mix_of_one_stem_equals_that_stem(self, tmp_path, stem_files):
        """
        Mixing a single stem should produce output identical to the input.

        This is a useful invariant: if it fails, you know your sample-rate
        or channel handling is doing something weird before any actual
        summing has happened.
        """
        output = tmp_path / "mix.wav"
        mix_stems(stem_files, ["drums"], output, fmt="wav")

        mixed, mixed_sr = sf.read(str(output), always_2d=True)
        original, original_sr = sf.read(str(stem_files["drums"]), always_2d=True)

        assert mixed_sr == original_sr
        np.testing.assert_allclose(mixed, original, atol=1e-4)

    def test_mix_clips_to_unit_range(self, tmp_path):
        """
        Output samples should never exceed [-1.0, 1.0] even if stems sum past it.

        The implementation explicitly clips, so summing two near-full-scale
        stems should still produce a valid in-range output.
        """
        sr = 22050
        n_samples = sr  # 1 second
        n_channels = 2

        # Two stems at 0.7 each — sum would be 1.4, which must clip to 1.0.
        loud_a = np.full((n_samples, n_channels), 0.7, dtype=np.float32)
        loud_b = np.full((n_samples, n_channels), 0.7, dtype=np.float32)

        path_a = tmp_path / "a.wav"
        path_b = tmp_path / "b.wav"
        sf.write(str(path_a), loud_a, sr)
        sf.write(str(path_b), loud_b, sr)

        output = tmp_path / "loud_mix.wav"
        mix_stems({"a": path_a, "b": path_b}, ["a", "b"], output, fmt="wav")

        mixed, _ = sf.read(str(output), always_2d=True)
        # Allow a tiny tolerance for PCM_16 quantisation right at the edge.
        assert np.max(np.abs(mixed)) <= 1.0 + 1e-3

    # ---------------- Error-handling tests ----------------

    def test_skips_missing_stems_silently(self, tmp_path, stem_files):
        """
        If a stem name in ``stems_to_mix`` isn't in ``stems_dict``, mix_stems
        should skip it (the implementation has an explicit ``continue``).
        """
        output = tmp_path / "mix.wav"
        # 'nonexistent' is not in stem_files — should be skipped, not raise.
        mix_stems(
            stem_files,
            ["drums", "nonexistent", "bass"],
            output,
            fmt="wav",
        )
        assert output.exists()

    def test_sample_rate_mismatch_raises(self, tmp_path):
        """
        Stems with different sample rates can't be mixed sample-by-sample —
        the implementation raises ValueError, which we verify here.
        """
        n_samples = 22050  # 1 second at 22050 Hz
        # Stem A at 22050 Hz
        stem_a = np.full((n_samples, 2), 0.1, dtype=np.float32)
        path_a = tmp_path / "a.wav"
        sf.write(str(path_a), stem_a, 22050)

        # Stem B at 44100 Hz (different rate)
        stem_b = np.full((44100, 2), 0.2, dtype=np.float32)
        path_b = tmp_path / "b.wav"
        sf.write(str(path_b), stem_b, 44100)

        output = tmp_path / "mix.wav"
        with pytest.raises(ValueError, match="[Ss]ample rate"):
            mix_stems({"a": path_a, "b": path_b}, ["a", "b"], output, fmt="wav")

    def test_shape_mismatch_raises(self, tmp_path):
        """
        Stems of different lengths can't be summed — should raise ValueError.
        """
        sr = 22050
        # 1 second
        stem_a = np.full((sr, 2), 0.1, dtype=np.float32)
        # 2 seconds — same rate, different length
        stem_b = np.full((sr * 2, 2), 0.2, dtype=np.float32)

        path_a = tmp_path / "a.wav"
        path_b = tmp_path / "b.wav"
        sf.write(str(path_a), stem_a, sr)
        sf.write(str(path_b), stem_b, sr)

        output = tmp_path / "mix.wav"
        with pytest.raises(ValueError, match="[Ss]hape"):
            mix_stems({"a": path_a, "b": path_b}, ["a", "b"], output, fmt="wav")
