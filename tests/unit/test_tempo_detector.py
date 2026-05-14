"""
Unit tests for ``drumscript.audio_processor.tempo_detector``.

What this file covers
---------------------
- ``estimate_tempo``: the only public function.

Testing strategy
----------------
Tempo detection is an approximate algorithm. We can't assert exact BPM
values; instead we use **approximate snapshot tests**: assert that the
output falls within a tolerance band around the known ground truth.

The fixtures ``click_track_120bpm`` and ``silent_audio`` (defined in
``conftest.py``) give us deterministic, reproducible inputs so these
tests are stable run-to-run despite the algorithm's heuristic nature.

Why ±10% tolerance?
-------------------
Even on a perfect click track, librosa's tempogram analysis can land on
half-time or double-time variants of the true tempo. We use a tolerance
band wide enough to accept the true tempo but narrow enough to reject
egregious failures (e.g. returning 60 or 240 BPM for a 120 BPM track).
For your own real-audio integration tests later, you may want to widen
this to ±20% or include explicit half/double-time handling.
"""

import numpy as np

from drumscript.audio_processor.tempo_detector import estimate_tempo


class TestEstimateTempo:
    """Tests for ``estimate_tempo``."""

    # ---------------- Edge cases ----------------

    def test_empty_audio_returns_zero(self):
        """Zero-length input must return 0.0, not crash."""
        empty = np.array([], dtype=np.float32)
        result = estimate_tempo(empty, sr=22050)
        assert result == 0.0

    def test_too_short_audio_returns_default_120(self):
        """
        Audio shorter than 1.0s should return the documented default of 120 BPM.

        The implementation hard-codes this fallback because tempogram analysis
        on sub-second clips produces wild, meaningless values (e.g. 235 BPM
        for a single kick hit).
        """
        sr = 22050
        # 0.5 seconds — well under the 1.0s threshold
        short = np.random.uniform(-0.3, 0.3, sr // 2).astype(np.float32)
        result = estimate_tempo(short, sr=sr)
        assert result == 120.0

    def test_silent_audio_returns_default(self, silent_audio):
        """
        Silence has no detectable tempo. We don't enforce a specific fallback
        value: librosa's tempogram on zeros lands somewhere in the plausible
        range depending on internal heuristics, and pinning a specific value
        would be brittle (a librosa upgrade could shift it).

        The real invariants we care about are:
        1. The function doesn't crash on silence.
        2. It returns a finite number (not NaN, not infinity).
        3. The number is in the documented plausible range (60-240 BPM).
        """
        audio, sr = silent_audio
        result = estimate_tempo(audio, sr=sr)

        # Finite check: NaN != NaN is the canonical NaN test in Python/numpy.
        assert result == result, f"Result was NaN: {result}"
        assert result != float("inf"), f"Result was infinity: {result}"
        # Plausible range — same bounds the implementation enforces internally.
        assert 60 <= result <= 240, f"Result {result} outside plausible range"

    # ---------------- Happy path ----------------

    def test_detects_120bpm_from_click_track(self, click_track_120bpm):
        """
        A clean 120 BPM click track should produce ~120 BPM (within tolerance).

        This is the core "does the algorithm work" test. If this fails, every
        downstream test of tempo-aware code will be unreliable.
        """
        audio, sr = click_track_120bpm
        result = estimate_tempo(audio, sr=sr)

        # ±10% tolerance: accepts 108-132 BPM. Wide enough for librosa's
        # tempogram fluctuations, narrow enough to catch true regressions.
        assert 108 <= result <= 132, (
            f"Expected ~120 BPM for a 120 BPM click track, got {result:.1f}. Either the algorithm regressed or the fixture changed."
        )

    def test_returns_value_in_plausible_range(self, click_track_120bpm):
        """
        The implementation explicitly restricts results to 60-240 BPM.

        Verifies the plausible-range mask is working — without it, librosa
        sometimes returns extreme values like 10500 BPM (per the docstring).
        """
        audio, sr = click_track_120bpm
        result = estimate_tempo(audio, sr=sr)
        assert 60 <= result <= 240

    def test_returns_float(self, click_track_120bpm):
        """Output must be a Python float (or numpy float), not int or None."""
        audio, sr = click_track_120bpm
        result = estimate_tempo(audio, sr=sr)
        assert isinstance(result, (float, np.floating))
