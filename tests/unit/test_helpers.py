"""
Unit tests for ``drumscript.notation_generator.helpers``.

What this file covers
---------------------
- ``round_to_nearest_subdivision``: pure math, easy.
- ``get_note_duration_name``: pure math, but **see the warning below**.
- ``calculate_cents_difference``: pure math, easy.
- ``format_drum_event``: depends on ``DRUM_NOTATION_MAP`` from constants.

KNOWN ISSUE — get_note_duration_name
------------------------------------
``helpers.py`` reads ``constants.DURATION_WHOLE``, ``constants.DURATION_HALF``,
``constants.DURATION_QUARTER``, etc., but those constants are **commented out**
in ``constants.py`` at the time of writing.

This means ``get_note_duration_name`` will currently raise ``AttributeError``
on first call. The test below (``test_get_note_duration_name_known_values``)
is written to *fail* until you fix that — it's intentionally kept un-skipped
so the broken state stays visible.

To fix: uncomment these lines in ``drumscript/notation_generator/constants.py``::

    DURATION_WHOLE = 4.0
    DURATION_HALF = 2.0
    DURATION_QUARTER = 1.0
    DURATION_EIGHTH = 0.5
    DURATION_SIXTEENTH = 0.25
    DURATION_THIRTY_SECOND = 0.125
"""

import pytest

from drumscript.notation_generator.helpers import (
    calculate_cents_difference,
    format_drum_event,
    get_note_duration_name,
    round_to_nearest_subdivision,
)


# =============================================================================
# round_to_nearest_subdivision
# =============================================================================


class TestRoundToNearestSubdivision:
    """Tests for the rhythm quantisation helper."""

    @pytest.mark.parametrize(
        "input_beats,subdivision,expected",
        [
            # subdivision=4 means a 16th-note grid (4.0 / 4 = 1.0 beat unit).
            # Wait — actually the function reads:
            #   unit_duration_in_beats = 4.0 / subdivision
            # so subdivision=4 => unit = 1.0 beat (i.e. quarter notes).
            # subdivision=16 => unit = 0.25 beats (i.e. 16th notes).
            (0.0, 4, 0.0),  # zero stays zero
            (1.0, 4, 1.0),  # exact value unchanged
            (1.4, 4, 1.0),  # rounds down to nearest quarter
            (1.6, 4, 2.0),  # rounds up
            (0.24, 16, 0.25),  # snaps to nearest 16th
            (0.51, 16, 0.5),  # snaps down to half-beat
            (0.13, 16, 0.25),  # snaps up
            (2.0, 8, 2.0),  # exact value at coarser subdivision
        ],
    )
    def test_quantises_to_grid(self, input_beats, subdivision, expected):
        """Various combinations of input and grid resolution."""
        result = round_to_nearest_subdivision(input_beats, subdivision)
        assert result == pytest.approx(expected)

    def test_zero_subdivision_raises(self):
        """Subdivision of zero would divide by zero — must error explicitly."""
        with pytest.raises(ValueError, match="zero"):
            round_to_nearest_subdivision(1.0, 0)

    def test_negative_input_handled(self):
        """Negative beat values should still quantise correctly."""
        # -0.7 beats with subdivision=4 (unit=1.0) should round to -1.0
        result = round_to_nearest_subdivision(-0.7, 4)
        assert result == pytest.approx(-1.0)


# =============================================================================
# get_note_duration_name
# =============================================================================


class TestGetNoteDurationName:
    """
    Tests for ``get_note_duration_name``.

    NOTE: These tests will fail with AttributeError until DURATION_*
    constants are uncommented in constants.py. See module docstring.
    """

    def test_known_values(self):
        """
        Each well-known beat-fraction should map to the expected name.

        Tempo BPM is required by the signature but unused by the current
        implementation, so we pass a placeholder 120.
        """
        # Once you've added the DURATION_* constants, these should all pass.
        assert get_note_duration_name(4.0, 120) == "whole"
        assert get_note_duration_name(2.0, 120) == "half"
        assert get_note_duration_name(1.0, 120) == "quarter"
        assert get_note_duration_name(0.5, 120) == "eighth"
        assert get_note_duration_name(0.25, 120) == "16th"
        assert get_note_duration_name(0.125, 120) == "32nd"

    def test_unknown_duration_returns_fallback_string(self):
        """A non-standard duration should return the fallback format."""
        result = get_note_duration_name(0.375, 120)  # dotted eighth, not in map
        # Implementation returns "<value> beats" as the fallback.
        assert "beats" in result
        assert "0.375" in result


# =============================================================================
# calculate_cents_difference
# =============================================================================


class TestCalculateCentsDifference:
    """Tests for the frequency-to-cents conversion."""

    def test_same_frequency_is_zero_cents(self):
        """Two identical frequencies should differ by zero cents."""
        assert calculate_cents_difference(440.0, 440.0) == pytest.approx(0.0)

    def test_octave_up_is_1200_cents(self):
        """An octave is exactly 1200 cents by definition."""
        assert calculate_cents_difference(440.0, 880.0) == pytest.approx(1200.0)

    def test_octave_down_is_negative_1200_cents(self):
        """Going down an octave should give negative cents."""
        assert calculate_cents_difference(440.0, 220.0) == pytest.approx(-1200.0)

    def test_perfect_fifth_is_about_702_cents(self):
        """
        A just-intonation perfect fifth (ratio 3:2) is ~701.96 cents.

        This catches sign errors and log-base errors at once: equal-temperament
        fifths are 700 cents, so 702 is the just-intonation reference value.
        """
        result = calculate_cents_difference(440.0, 660.0)
        assert result == pytest.approx(701.955, abs=0.01)

    @pytest.mark.parametrize("bad_freq1,bad_freq2", [(0, 440), (440, 0), (-1, 440), (440, -1)])
    def test_non_positive_frequencies_raise(self, bad_freq1, bad_freq2):
        """Zero or negative frequencies are unphysical — must error explicitly."""
        with pytest.raises(ValueError, match="positive"):
            calculate_cents_difference(bad_freq1, bad_freq2)


# =============================================================================
# format_drum_event
# =============================================================================


class TestFormatDrumEvent:
    """Tests for the event-formatting helper."""

    def test_known_drum_type_returns_full_dict(self):
        """A drum type in DRUM_NOTATION_MAP should return all expected fields."""
        result = format_drum_event("kick", 1.234)

        # Must contain the input data...
        assert result["drum_type"] == "kick"
        assert result["onset_time_seconds"] == pytest.approx(1.234)

        # ...plus all the notation fields pulled from the map.
        assert "midi_pitch" in result
        assert "note_head_type" in result
        assert "staff_position" in result
        assert "display_name" in result

    def test_kick_has_correct_midi_program(self):
        """A specific value-check, so we'd notice if the map got mangled."""
        result = format_drum_event("kick", 0.0)
        assert result["midi_pitch"] == 36  # General MIDI kick

    def test_snare_has_correct_midi_program(self):
        """Same idea for snare."""
        result = format_drum_event("snare", 0.0)
        assert result["midi_pitch"] == 38  # General MIDI snare

    def test_unknown_drum_type_falls_back_to_kick(self, capsys):
        """
        Unknown drum types should warn and use kick's properties as fallback.

        ``capsys`` is a built-in pytest fixture that captures stdout/stderr,
        so we can assert the warning was actually printed.
        """
        result = format_drum_event("nonexistent_drum_type", 0.5)

        # Should have printed a warning to stdout.
        captured = capsys.readouterr()
        assert "Warning" in captured.out

        # Should have fallen back to kick's MIDI program.
        assert result["midi_pitch"] == 36
        # But the original drum_type is preserved in the output.
        assert result["drum_type"] == "nonexistent_drum_type"
