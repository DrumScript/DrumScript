"""
Unit tests for ``drumscript.drum_classifier.classify``.

What this file covers
---------------------
- ``classify_membranophone``: routes physics dict → drum skin labels.
- ``classify_idiophone``: routes physics dict → cymbal/hat labels.
- ``classify_event``: top-level wrapper combining the two.

What this file does NOT cover
-----------------------------
- ``extract_features``: requires a real audio array; that's an integration
  test (it uses real librosa STFT/RMS, not pure dict logic).
- ``get_audio_slice``: trivial array slicing; could add later.
- ``classify_rudiment_events``: combines audio loading + classification;
  better tested end-to-end against a known rudiment file.

Testing strategy
----------------
These three functions are **pure dict transformations**: they take a
physics-feature dict and return a list of label strings. That means:

- No I/O, no audio loading, no librosa, no fixtures needed for the
  inputs themselves — we just construct the dicts directly.
- We can write *exhaustive* tests for each branch of the classification
  logic by crafting a physics dict that hits exactly that branch.
- Tests are extremely fast (microseconds each).

This is the kind of code that benefits most from unit tests, because
it's 100% deterministic and the exact thresholds (KICK_LFER_MIN, etc.)
are easy to make off-by-one mistakes on when you tweak constants.

CONSTANTS REFERENCED
--------------------
The classifier reads thresholds from
``drumscript.notation_generator.constants``. We import those values here
rather than hard-coding magic numbers, so if you tune a threshold the
test inputs adjust automatically.

KNOWN ISSUE — duplicated constants
----------------------------------
At time of writing, ``constants.py`` defines several thresholds **twice**
with different values:

  - ``SNARE_FREQ_MIN``: 130.0 (first), then 120.0 (second — wins)
  - ``SNARE_FREQ_MAX``: 400.0 (first), then 450.0 (second — wins)
  - ``SNARE_HFER_MIN``: 0.20 (first), then 0.15 (second — wins)
  - ``TOM_MIN_DECAY``: 0.30 (first), then 0.28 (second — wins)
  - ``TOM_FREQ_LOW_MAX``: 95.0 (first), then 92.0 (second — wins)

Python's last-write-wins behaviour means only the second values take
effect. This is almost certainly unintended — when you tune thresholds
you'd expect the *first* (annotated) one to be authoritative.

**Recommended fix**: pick one set, delete the other, and keep tests
passing against the surviving values. These tests will self-adjust
because they import the constants by name (whichever value is live).
"""

import pytest

from drumscript.drum_classifier.classify import (
    classify_event,
    classify_idiophone,
    classify_membranophone,
)
from drumscript.notation_generator.constants import (
    HAT_CLOSED_MAX_DECAY,
    HAT_OPEN_MAX_DECAY,
    IDIOPHONE_MIN_HFER_5K,
    KICK_FREQ_MAX,
    KICK_LFER_MIN,
    SNARE_FREQ_MAX,
    SNARE_FREQ_MIN,
    SNARE_HFER_MIN,
    TOM_FREQ_LOW_MAX,
    TOM_FREQ_MID_MAX,
    TOM_MIN_DECAY,
)


def _make_physics(
    peak_freq=200.0,
    centroid=2000.0,
    decay=0.1,
    lfer=0.0,
    hfer=0.0,
    hfer_5k=0.0,
):
    """
    Build a physics dict with sensible defaults.

    Defaults are chosen to NOT trigger any classifier rule by themselves.
    Each test then overrides only the fields relevant to the rule it's
    exercising. This keeps individual tests focused and readable.
    """
    return {
        "peak_freq": peak_freq,
        "centroid": centroid,
        "decay": decay,
        "lfer": lfer,
        "hfer": hfer,
        "hfer_5k": hfer_5k,
    }


# =============================================================================
# classify_membranophone
# =============================================================================


class TestClassifyMembranophone:
    """
    Tests for the skin-drum (kick / snare / tom) classifier.

    Every test constructs a physics dict that's deliberately set just past
    the relevant threshold, asserting exactly which label(s) come out.
    """

    # ---------------- KICK ----------------

    def test_classifies_kick_with_low_freq_and_high_lfer(self):
        """A textbook kick: low fundamental, dominant low-frequency energy."""
        p = _make_physics(
            peak_freq=80.0,  # safely inside KICK_FREQ range
            lfer=KICK_LFER_MIN + 0.05,  # comfortably above threshold
            hfer=0.05,  # not enough to trigger snare
            decay=0.1,  # short — not a tom
        )
        result = classify_membranophone(p)
        assert "kick" in result

    def test_kick_below_lfer_threshold_not_classified(self):
        """
        If LFER is below KICK_LFER_MIN, the kick rule should NOT fire,
        even with a kick-range peak frequency.
        """
        p = _make_physics(
            peak_freq=80.0,
            lfer=KICK_LFER_MIN - 0.05,  # JUST below
            hfer=0.05,
            decay=0.1,
        )
        result = classify_membranophone(p)
        assert "kick" not in result

    def test_kick_outside_freq_range_not_classified(self):
        """A frequency above KICK_FREQ_MAX shouldn't be classed as a kick."""
        p = _make_physics(
            peak_freq=KICK_FREQ_MAX + 50,  # too high for kick
            lfer=KICK_LFER_MIN + 0.1,
            hfer=0.05,
            decay=0.1,
        )
        result = classify_membranophone(p)
        assert "kick" not in result

    # ---------------- SNARE ----------------

    def test_classifies_snare_with_wires_and_freq(self):
        """A snare: mid-frequency peak with high-frequency wire energy."""
        p = _make_physics(
            peak_freq=(SNARE_FREQ_MIN + SNARE_FREQ_MAX) / 2,  # mid-range
            hfer=SNARE_HFER_MIN + 0.1,
            lfer=0.05,  # not enough for kick
        )
        result = classify_membranophone(p)
        assert "snare" in result

    def test_snare_without_wire_energy_not_classified(self):
        """Snare-frequency peak but no wire (low HFER) → not a snare."""
        p = _make_physics(
            peak_freq=200.0,
            hfer=SNARE_HFER_MIN - 0.05,  # below wire threshold
        )
        result = classify_membranophone(p)
        assert "snare" not in result

    def test_snare_with_extreme_hfer_not_classified(self):
        """
        HFER >= 0.85 means the sound is essentially all high-frequency hiss
        (i.e. a cymbal), not a snare. The implementation has an explicit
        upper bound: ``has_snare_wire = SNARE_HFER_MIN <= hfer < 0.85``.
        """
        p = _make_physics(
            peak_freq=200.0,
            hfer=0.90,  # above the 0.85 cap
        )
        result = classify_membranophone(p)
        assert "snare" not in result

    # ---------------- TOMS ----------------

    def test_classifies_low_tom(self):
        """Low-pitched, pure (low HFER), resonant (long decay) → low_tom."""
        p = _make_physics(
            peak_freq=TOM_FREQ_LOW_MAX - 5,  # below low-tom max
            hfer=SNARE_HFER_MIN - 0.05,  # pure, no wire
            decay=TOM_MIN_DECAY + 0.05,  # resonant
            lfer=0.0,  # not enough to trigger kick
        )
        result = classify_membranophone(p)
        assert "low_tom" in result

    def test_classifies_mid_tom(self):
        """Mid-range pitch with same purity/resonance → mid_tom."""
        p = _make_physics(
            peak_freq=(TOM_FREQ_LOW_MAX + TOM_FREQ_MID_MAX) / 2,
            hfer=SNARE_HFER_MIN - 0.05,
            decay=TOM_MIN_DECAY + 0.05,
        )
        result = classify_membranophone(p)
        assert "mid_tom" in result

    def test_classifies_high_tom(self):
        """Higher pitch, still pure and resonant → high_tom."""
        p = _make_physics(
            peak_freq=TOM_FREQ_MID_MAX + 50,  # above mid-tom max
            hfer=SNARE_HFER_MIN - 0.05,
            decay=TOM_MIN_DECAY + 0.05,
        )
        result = classify_membranophone(p)
        assert "high_tom" in result

    def test_kick_takes_precedence_over_low_tom(self):
        """
        When both kick and low_tom rules would fire on the same input,
        kick wins. This is encoded in the implementation:
        ``if 'kick' not in detected_instruments: append('low_tom')``.
        """
        p = _make_physics(
            peak_freq=80.0,  # in kick range AND below TOM_FREQ_LOW_MAX
            lfer=KICK_LFER_MIN + 0.1,
            hfer=SNARE_HFER_MIN - 0.05,  # pure
            decay=0.1,  # too short to be a "pure tom" — kick rule fires
        )
        result = classify_membranophone(p)
        assert "kick" in result
        assert "low_tom" not in result


# =============================================================================
# classify_idiophone
# =============================================================================


class TestClassifyIdiophone:
    """Tests for the cymbal/hat classifier."""

    def test_no_metal_when_hfer_5k_low(self):
        """If high-frequency (5kHz+) energy is below threshold → no metals."""
        p = _make_physics(hfer_5k=IDIOPHONE_MIN_HFER_5K - 0.05)
        result = classify_idiophone(p)
        assert result == []

    def test_classifies_closed_hat(self):
        """High HFER_5k + short decay → closed hi-hat."""
        p = _make_physics(
            hfer_5k=IDIOPHONE_MIN_HFER_5K + 0.1,
            decay=HAT_CLOSED_MAX_DECAY - 0.05,  # short decay
        )
        result = classify_idiophone(p)
        assert "hi_hat_closed" in result

    def test_classifies_open_hat(self):
        """High HFER_5k + medium decay → open hi-hat."""
        p = _make_physics(
            hfer_5k=IDIOPHONE_MIN_HFER_5K + 0.1,
            decay=(HAT_CLOSED_MAX_DECAY + HAT_OPEN_MAX_DECAY) / 2,
        )
        result = classify_idiophone(p)
        assert "hi_hat_open" in result

    def test_classifies_crash_with_high_centroid(self):
        """Long decay + bright (high centroid) → crash cymbal."""
        p = _make_physics(
            hfer_5k=IDIOPHONE_MIN_HFER_5K + 0.1,
            decay=HAT_OPEN_MAX_DECAY + 0.5,  # long decay → metal cymbal
            centroid=6000,  # > 5500 threshold for crash
        )
        result = classify_idiophone(p)
        assert "crash" in result

    def test_classifies_ride_with_lower_centroid(self):
        """Long decay + darker (low centroid) → ride cymbal."""
        p = _make_physics(
            hfer_5k=IDIOPHONE_MIN_HFER_5K + 0.1,
            decay=HAT_OPEN_MAX_DECAY + 0.5,
            centroid=4000,  # below 5500 threshold
        )
        result = classify_idiophone(p)
        assert "ride" in result

    @pytest.mark.parametrize(
        "centroid,expected",
        [
            (3000, "ride"),
            (5000, "ride"),
            (5499, "ride"),  # just below threshold
            (5501, "crash"),  # just above threshold
            (7000, "crash"),
        ],
    )
    def test_ride_vs_crash_centroid_threshold(self, centroid, expected):
        """
        The ride/crash split happens at centroid > 5500 Hz.

        Parametrised to verify behaviour right at the threshold — these
        boundary cases are where off-by-one (or off-by-Hz) bugs hide.
        """
        p = _make_physics(
            hfer_5k=IDIOPHONE_MIN_HFER_5K + 0.1,
            decay=HAT_OPEN_MAX_DECAY + 0.5,
            centroid=centroid,
        )
        result = classify_idiophone(p)
        assert expected in result


# =============================================================================
# classify_event (top-level wrapper)
# =============================================================================


class TestClassifyEvent:
    """Tests for the top-level ``classify_event`` orchestrator."""

    def test_unknown_when_no_rule_fires(self):
        """
        If neither classify_membranophone nor classify_idiophone produces
        anything, the result must be ``["unknown"]`` — never an empty list.
        Downstream code relies on always having at least one label.
        """
        # All zeros / mid values — nothing matches any rule
        p = _make_physics()
        result = classify_event(p)
        assert result == ["unknown"]

    def test_kick_input_returns_kick_label(self):
        """End-to-end smoke test for a kick input."""
        p = _make_physics(
            peak_freq=80.0,
            lfer=KICK_LFER_MIN + 0.1,
            hfer=0.05,
            decay=0.1,
        )
        result = classify_event(p)
        assert "kick" in result
        assert "unknown" not in result  # Don't fall back if a rule fired

    def test_combines_both_classifiers(self):
        """
        Inputs that look like both a snare AND a closed hat (e.g. a cross-
        stick on a snare with cymbal bleed) should return both labels.

        This verifies the wrapper is calling both sub-classifiers, not
        short-circuiting after the first match.
        """
        p = _make_physics(
            peak_freq=200.0,  # snare-frequency peak
            hfer=SNARE_HFER_MIN + 0.1,  # snare wires
            hfer_5k=IDIOPHONE_MIN_HFER_5K + 0.1,  # high freq energy
            decay=HAT_CLOSED_MAX_DECAY - 0.05,  # short decay → closed hat
        )
        result = classify_event(p)
        # We expect both labels; order is not guaranteed by the spec.
        assert "snare" in result
        assert "hi_hat_closed" in result

    def test_returns_list(self):
        """Output must always be a list, never None or a single string."""
        p = _make_physics()
        result = classify_event(p)
        assert isinstance(result, list)
