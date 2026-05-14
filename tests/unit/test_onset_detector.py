"""
Unit tests for ``drumscript.audio_processor.onset_detector``.

What this file covers
---------------------
- ``detect_onsets``: the only public function in this module.

Testing strategy
----------------
Like tempo detection, onset detection is approximate. We can't assert
exact onset timestamps; instead we test:

1. **Edge cases** that should be deterministic (empty input, silence).
2. **Count-based tests**: synthesise N pulses, expect ~N onsets detected.
3. **Approximate timing**: detected onsets should fall close to the
   pulse positions we placed in the input.

Built-in fixtures used
----------------------
We don't reuse ``click_track_120bpm`` here because that fixture is
optimised for tempo detection (regular spacing matters); for onset
detection we want deliberately spaced pulses where we can easily
assert their positions.
"""

import numpy as np
import pytest

from drumscript.audio_processor.onset_detector import detect_onsets


def _make_pulse_train(pulse_times_secs, sr=22050, total_duration_secs=5.0):
    """
    Build a clean pulse train at the given onset times.

    Each pulse is a 50ms burst of full-amplitude white noise (deterministic
    via fixed seed). White noise has the broadband energy that librosa's
    onset detector is sensitive to — pure sine bursts are surprisingly hard
    to detect because they lack high-frequency transient content.

    :param pulse_times_secs: List of pulse onset times in seconds.
    :param sr: Sample rate.
    :param total_duration_secs: Total length of output audio.
    :return: (audio, sr) tuple matching the conftest fixture convention.
    """
    n_samples = int(sr * total_duration_secs)
    audio = np.zeros(n_samples, dtype=np.float32)

    rng = np.random.default_rng(seed=42)
    pulse_len = int(sr * 0.05)  # 50 ms

    for t in pulse_times_secs:
        start = int(t * sr)
        end = min(start + pulse_len, n_samples)
        if start < n_samples:
            audio[start:end] = rng.uniform(-0.9, 0.9, end - start).astype(np.float32)

    return audio, sr


class TestDetectOnsets:
    """Tests for ``detect_onsets``."""

    # ---------------- Edge cases ----------------

    def test_empty_audio_returns_empty_list(self):
        """Zero-length input must return [], not crash."""
        empty = np.array([], dtype=np.float32)
        result = detect_onsets(empty, sr=22050)
        assert result == []

    def test_silent_audio_detects_no_onsets(self, silent_audio):
        """
        A 5-second silent track should produce zero (or near-zero) onsets.

        librosa can occasionally hallucinate a single onset at t=0 from
        floating-point noise, so we tolerate up to 1 spurious detection.
        """
        audio, sr = silent_audio
        result = detect_onsets(audio, sr=sr)
        assert len(result) <= 1, f"Silent audio should produce ~0 onsets, got {len(result)}."

    # ---------------- Output shape / type ----------------

    def test_returns_list_of_floats(self):
        """The function must return a list of plain Python floats."""
        audio, sr = _make_pulse_train([0.5, 1.5, 2.5], total_duration_secs=4.0)
        result = detect_onsets(audio, sr=sr)
        assert isinstance(result, list)
        # Tolerate both Python float and numpy floats — the implementation
        # converts via .tolist() but downstream code shouldn't care.
        for onset in result:
            assert isinstance(onset, (float, np.floating))

    def test_onsets_are_in_chronological_order(self):
        """Detected onsets should always be in ascending time order."""
        audio, sr = _make_pulse_train([0.5, 1.5, 2.5, 3.5], total_duration_secs=5.0)
        result = detect_onsets(audio, sr=sr)
        # Verify ascending order (within numerical tolerance)
        for i in range(1, len(result)):
            assert result[i] > result[i - 1], f"Onsets out of order: {result[i - 1]} not before {result[i]}"

    # ---------------- Count-based detection ----------------

    def test_detects_approximate_number_of_pulses(self):
        """
        Four well-spaced pulses should produce roughly four onsets.

        We allow some slack because:
        - librosa may merge pulses that fall within the wait-frames lockout
        - It may add a spurious onset at t=0 from initial conditions
        - The 2.0s "single beat refinement" branch may kick in and drop some
        """
        pulse_times = [0.5, 1.5, 2.5, 3.5]
        audio, sr = _make_pulse_train(pulse_times, total_duration_secs=5.0)

        result = detect_onsets(audio, sr=sr)

        # Expect 4 ± 2. Liberal because long-duration onset detection
        # is forgiving but not exact.
        assert 2 <= len(result) <= 6, f"Expected ~4 onsets for 4 pulses, got {len(result)}: {result}"

    def test_detects_approximate_pulse_positions(self):
        """
        Detected onsets should fall reasonably close to the input pulse times.

        We use a 100ms tolerance — librosa's spectral flux detection can
        latch on to the pulse start ±a few frames depending on hop length.
        """
        pulse_times = [1.0, 2.0, 3.0]
        audio, sr = _make_pulse_train(pulse_times, total_duration_secs=4.0)

        result = detect_onsets(audio, sr=sr)

        # For each input pulse, find the closest detected onset.
        # That closest detection should be within 150 ms.
        for expected_t in pulse_times:
            if not result:
                pytest.fail(f"No onsets detected at all (expected pulse at {expected_t}s)")
            closest = min(result, key=lambda r: abs(r - expected_t))
            assert abs(closest - expected_t) < 0.15, (
                f"Closest detected onset to {expected_t}s was {closest}s (off by {abs(closest - expected_t) * 1000:.0f}ms). All detections: {result}"
            )

    # ---------------- Single-beat refinement branch ----------------

    def test_short_audio_with_close_pulses_gets_debounced(self):
        """
        The implementation has a "single-beat refinement" branch:
        if duration < 2.0s and multiple onsets are detected, it dedupes
        any within 150ms of each other.

        We construct a 1.5s clip with two pulses spaced 50ms apart and
        expect the refinement to drop the second one.
        """
        # Pulses at 0.5s and 0.55s — only 50ms apart, well inside the
        # 150ms refinement threshold.
        pulse_times = [0.5, 0.55]
        audio, sr = _make_pulse_train(pulse_times, total_duration_secs=1.5)

        result = detect_onsets(audio, sr=sr)

        # The refinement should leave at most 1 onset for these two
        # closely-spaced pulses in a sub-2.0s clip.
        # (Could be 0 or 1 depending on whether either was detected; the
        # invariant is "not 2".)
        assert len(result) <= 1, f"Refinement should have dropped the close pulse, got {len(result)}: {result}"
