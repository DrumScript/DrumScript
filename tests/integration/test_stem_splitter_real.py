"""
Integration tests for ``drumscript.audio_processor.stem_splitter``.

What's special about this file
------------------------------
These tests **actually run Demucs** as a subprocess. They are:

- **Slow** (~30 seconds per test on CPU, much faster on GPU/MPS)
- **Heavy** (downloads the htdemucs model on first run, ~100MB)
- **Dependent on ffmpeg** being installed on the system

For all those reasons, they are tagged with both ``@pytest.mark.slow``
and ``@pytest.mark.integration`` so they're **opt-in** rather than
running on every ``pytest`` invocation.

How to run
----------
::

    # Run only fast unit tests (default for development):
    pytest -m "not slow"

    # Run only integration tests:
    pytest -m integration

    # Run everything including slow tests (e.g. before a release):
    pytest

When to run these
-----------------
- Before merging a PR that touches stem_splitter or any audio I/O
- Before tagging a release
- After upgrading Demucs, soundfile, pydub, or ffmpeg
- When debugging "why does my unit-tested code fail in production"

NOT before
----------
- Every commit (too slow — would kill your dev loop)
- Every save (you'd want to throw your laptop)

Why integration tests still matter
----------------------------------
Unit tests can't catch problems like:

- Demucs CLI flags changing in a new version
- Output directory layout changes
- Subtle WAV format incompatibilities between sf.write and Demucs's loader
- ffmpeg version mismatches

The unit tests verify "our code does the right thing assuming Demucs
behaves as expected"; these tests verify "Demucs actually behaves as
expected on this machine".
"""

import shutil
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from drumscript.audio_processor.stem_splitter import (
    extract_drum_stem,
    separate_audio,
)

# =============================================================================
# Module-level skip if Demucs isn't on PATH
# =============================================================================
#
# Without this, integration tests fail noisily on machines where Demucs
# isn't installed. With it, they're cleanly skipped with a clear reason.
DEMUCS_AVAILABLE = shutil.which("demucs") is not None
pytestmark = [
    pytest.mark.slow,
    pytest.mark.integration,
    pytest.mark.skipif(
        not DEMUCS_AVAILABLE,
        reason="demucs CLI not found on PATH; skipping integration tests",
    ),
]


# =============================================================================
# Fixtures specific to integration tests
# =============================================================================


@pytest.fixture(scope="module")
def short_drum_loop_wav(tmp_path_factory):
    """
    A short synthesised drum-like WAV for Demucs to chew on.

    Module-scoped: the same file is reused across every test in this
    module so we only generate it once. Demucs takes the same time
    regardless of input length (within reason), so we keep this short.

    8 seconds is the practical minimum — Demucs will refuse very short
    inputs because its model expects longer context windows.
    """
    sr = 44100
    duration_s = 8.0
    n_samples = int(sr * duration_s)

    # Build a synthesised "drum loop" with a kick-snare pattern at 120 BPM.
    # The actual content doesn't need to sound musical — Demucs will still
    # try to separate it. We just need enough variety that Demucs has
    # something to work with.
    rng = np.random.default_rng(seed=42)
    audio = np.zeros(n_samples, dtype=np.float32)

    # Add a kick on every beat (120 BPM = 2Hz = every 0.5s)
    for t in np.arange(0, duration_s, 0.5):
        start = int(t * sr)
        # Low-frequency thump
        decay_len = int(sr * 0.15)
        env = np.exp(-np.linspace(0, 5, decay_len))
        kick_freq = 60
        kick = np.sin(2 * np.pi * kick_freq * np.linspace(0, decay_len / sr, decay_len)) * env * 0.5
        end = min(start + decay_len, n_samples)
        audio[start:end] += kick[: end - start].astype(np.float32)

    # Add a snare on offbeats (every 0.5s offset by 0.25s)
    for t in np.arange(0.25, duration_s, 0.5):
        start = int(t * sr)
        # White-noise burst
        decay_len = int(sr * 0.10)
        env = np.exp(-np.linspace(0, 8, decay_len))
        snare = (rng.uniform(-0.4, 0.4, decay_len) * env).astype(np.float32)
        end = min(start + decay_len, n_samples)
        audio[start:end] += snare[: end - start]

    # Stereo by duplication (Demucs prefers stereo)
    stereo = np.column_stack([audio, audio])

    # Persist to disk in a session-shared temp dir
    tmp_dir = tmp_path_factory.mktemp("integration_audio")
    path = tmp_dir / "synthesised_drum_loop.wav"
    sf.write(str(path), stereo, sr)
    return path


# =============================================================================
# extract_drum_stem (legacy wrapper)
# =============================================================================


class TestExtractDrumStemReal:
    """Real Demucs runs through the legacy ``extract_drum_stem`` function."""

    def test_produces_drum_stem_file(self, short_drum_loop_wav, tmp_path):
        """End-to-end: Demucs runs, drums.wav appears at the expected path."""
        result = extract_drum_stem(str(short_drum_loop_wav), output_dir=str(tmp_path))

        # The function should return a path string
        assert isinstance(result, str)
        result_path = Path(result)
        assert result_path.exists()
        assert result_path.suffix == ".wav"

    def test_drum_stem_is_nonempty_audio(self, short_drum_loop_wav, tmp_path):
        """The produced WAV should contain actual audio samples."""
        result = extract_drum_stem(str(short_drum_loop_wav), output_dir=str(tmp_path))

        audio, sr = sf.read(result)
        assert audio.shape[0] > 0
        assert sr > 0
        # The drum stem shouldn't be all zeros — Demucs should have
        # extracted SOMETHING from the input. If it's silent, either
        # Demucs failed or the model wasn't run.
        assert np.max(np.abs(audio)) > 0.001

    def test_drum_stem_is_shorter_or_equal_to_input(self, short_drum_loop_wav, tmp_path):
        """Sanity check: output length should match the input (no truncation)."""
        result = extract_drum_stem(str(short_drum_loop_wav), output_dir=str(tmp_path))

        original, original_sr = sf.read(str(short_drum_loop_wav))
        stem, stem_sr = sf.read(result)

        # Demucs preserves sample rate
        assert stem_sr == original_sr
        # Length should match within a small tolerance
        # (Demucs sometimes pads to a multiple of its hop length)
        assert abs(stem.shape[0] - original.shape[0]) < stem_sr  # < 1 sec slack


# =============================================================================
# separate_audio (full-feature function)
# =============================================================================


class TestSeparateAudioReal:
    """Real Demucs runs through the full-featured ``separate_audio`` function."""

    def test_default_call_returns_drums(self, short_drum_loop_wav, tmp_path):
        """Default call (no flags) should produce just the drum stem."""
        result = separate_audio(
            audio_path=str(short_drum_loop_wav),
            output_dir=str(tmp_path),
        )

        assert isinstance(result, dict)
        assert "drums" in result
        assert Path(result["drums"]).exists()

    def test_drumless_creates_mix_and_drum_stem(self, short_drum_loop_wav, tmp_path):
        """``drumless=True`` should produce both the no-drums mix AND the isolated drums."""
        result = separate_audio(
            audio_path=str(short_drum_loop_wav),
            output_dir=str(tmp_path),
            drumless=True,
        )

        # The drumless mix
        assert "mix" in result
        mix_path = Path(result["mix"])
        assert mix_path.exists()
        assert "no_drums" in mix_path.name

        # The isolated drum stem (saved alongside the mix)
        assert "drums_stem" in result
        assert Path(result["drums_stem"]).exists()

    def test_all_stems_creates_four_files(self, short_drum_loop_wav, tmp_path):
        """``all_stems=True`` should create one file per Demucs stem (4 total)."""
        result = separate_audio(
            audio_path=str(short_drum_loop_wav),
            output_dir=str(tmp_path),
            all_stems=True,
        )

        # htdemucs produces drums, bass, other, vocals — four stems.
        expected_keys = {"drums_stem", "bass_stem", "other_stem", "vocals_stem"}
        actual_keys = set(result.keys())
        assert expected_keys.issubset(actual_keys), f"Expected all four stems in result. Got: {actual_keys}"

        # All four files should physically exist
        for key in expected_keys:
            assert Path(result[key]).exists(), f"Missing file: {result[key]}"

    def test_mute_bass_creates_no_bass_mix(self, short_drum_loop_wav, tmp_path):
        """``mute=['bass']`` should produce a mix with the bass excluded."""
        result = separate_audio(
            audio_path=str(short_drum_loop_wav),
            output_dir=str(tmp_path),
            mute=["bass"],
        )

        assert "mix" in result
        mix_name = Path(result["mix"]).name
        assert "no_bass" in mix_name

        # The excluded bass stem should also be saved separately
        assert "bass_stem" in result

    def test_temp_demucs_dir_is_cleaned_up(self, short_drum_loop_wav, tmp_path):
        """
        Implementation detail: separate_audio should clean up its
        temp_demucs working directory after success.

        This catches regressions where the cleanup line gets accidentally
        commented out or moved out of scope.
        """
        separate_audio(
            audio_path=str(short_drum_loop_wav),
            output_dir=str(tmp_path),
        )

        # Walk the output dir looking for any leftover temp_demucs dir
        leftover = list(tmp_path.rglob("temp_demucs"))
        assert leftover == [], f"Found leftover temp_demucs directories: {leftover}. separate_audio() should clean these up after running."
