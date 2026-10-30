"""
Tests for ``drumscript.notation_generator.midi_exporter.export_to_midi``.

Why this file exists
--------------------
``export_to_midi`` is the one function that turns classified events into an
actual file on disk, and until now it had no unit tests of its own. It is
reached from three directions, so a break here is a break everywhere:

- ``build_score()``, on every normal transcription
- ``build_score(midi_only=True)``, on a MIDI-only run
- ``export_midi()``, the public API, for a score the caller already has

The headline case below is the bare-filename bug carried over from #348.
``os.path.dirname("my_drums.mid")`` returns an empty string, and
``os.makedirs("")`` raises ``FileNotFoundError``. So any caller who passed a
filename with no directory in it got a crash rather than a MIDI file. The fix
guards the ``makedirs`` call; ``test_bare_filename_with_no_directory`` is what
stops it regressing.

These tests write into ``tmp_path`` and assert on the file that lands there.
They do not assert on transcription accuracy, which belongs in the benchmarks.
"""

import os

import pretty_midi
import pytest

from drumscript.notation_generator.constants import DRUM_NOTATION_MAP
from drumscript.notation_generator.midi_exporter import export_to_midi

pytestmark = pytest.mark.integration


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def events():
    """A small, deliberately boring set of events: kick, snare, kick."""
    return [
        {"time_sec": 0.0, "instruments": ["kick"]},
        {"time_sec": 0.5, "instruments": ["snare"]},
        {"time_sec": 1.0, "instruments": ["kick"]},
    ]


# =============================================================================
# The bare-filename fix (#348)
# =============================================================================


class TestOutputPathHandling:
    """Where the file is asked to go, and whether it gets there."""

    def test_bare_filename_with_no_directory(self, events, tmp_path, monkeypatch):
        """
        A filename with no directory part must work.

        This is the #348 fix. ``os.path.dirname("my_drums.mid")`` is ``""`` and
        ``os.makedirs("")`` raises ``FileNotFoundError``, so before the guard
        this raised instead of writing anything.
        """
        # Arrange
        monkeypatch.chdir(tmp_path)

        # Act
        export_to_midi(classified_events=events, output_path="my_drums.mid")

        # Assert
        assert (tmp_path / "my_drums.mid").is_file()

    def test_makedirs_is_not_called_for_a_bare_filename(self, events, tmp_path, monkeypatch):
        """
        Pins the mechanism, not just the symptom.

        Asserting only that the file appears would still pass if someone
        "fixed" this by wrapping the whole thing in a bare ``except``. This
        fails if ``makedirs`` is ever called with an empty string again.
        """
        # Arrange
        monkeypatch.chdir(tmp_path)
        calls = []
        real_makedirs = os.makedirs

        def spy(path, *args, **kwargs):
            calls.append(path)
            return real_makedirs(path, *args, **kwargs)

        monkeypatch.setattr("drumscript.notation_generator.midi_exporter.os.makedirs", spy)

        # Act
        export_to_midi(classified_events=events, output_path="my_drums.mid")

        # Assert
        assert "" not in calls, f"makedirs was called with an empty path: {calls}"

    def test_creates_a_missing_output_directory(self, events, tmp_path):
        """A nested directory that does not exist yet is created, not an error."""
        # Arrange
        target = tmp_path / "does" / "not" / "exist" / "drums.mid"

        # Act
        export_to_midi(classified_events=events, output_path=str(target))

        # Assert
        assert target.is_file()

    def test_existing_directory_is_reused(self, events, tmp_path):
        """An existing directory must not raise, which is what exist_ok is for."""
        # Arrange
        target = tmp_path / "drums.mid"
        export_to_midi(classified_events=events, output_path=str(target))

        # Act
        export_to_midi(classified_events=events, output_path=str(target))

        # Assert
        assert target.is_file()


# =============================================================================
# The contents of the file
# =============================================================================


class TestMidiContents:
    """What actually lands in the .mid."""

    def test_writes_a_readable_midi_file(self, events, tmp_path):
        """The output must be something a DAW can open, not just bytes on disk."""
        # Arrange
        target = tmp_path / "drums.mid"

        # Act
        export_to_midi(classified_events=events, output_path=str(target), tempo=120.0)

        # Assert
        parsed = pretty_midi.PrettyMIDI(str(target))
        assert parsed.instruments, "no instrument track was written"

    def test_track_is_flagged_as_drums(self, events, tmp_path):
        """
        ``is_drum`` puts the track on MIDI channel 10.

        Without it a DAW loads the notes onto a melodic instrument and the
        whole point of the export is lost.
        """
        # Arrange
        target = tmp_path / "drums.mid"

        # Act
        export_to_midi(classified_events=events, output_path=str(target))

        # Assert
        assert parsed_track(target).is_drum is True

    def test_one_note_per_instrument_hit(self, events, tmp_path):
        """Three single-instrument events produce three notes."""
        # Arrange
        target = tmp_path / "drums.mid"

        # Act
        export_to_midi(classified_events=events, output_path=str(target))

        # Assert
        assert len(parsed_track(target).notes) == 3

    def test_simultaneous_instruments_each_get_a_note(self, tmp_path):
        """
        One onset carrying two instruments must write two notes.

        A kick and a hi-hat struck together is one event but two drums, and a
        DAW needs both pitches.
        """
        # Arrange
        target = tmp_path / "drums.mid"
        events = [{"time_sec": 0.0, "instruments": ["kick", "hi_hat_closed"]}]

        # Act
        export_to_midi(classified_events=events, output_path=str(target))

        # Assert
        notes = parsed_track(target).notes
        assert len(notes) == 2
        assert len({n.pitch for n in notes}) == 2, "both hits landed on the same pitch"

    def test_pitches_follow_the_notation_map(self, events, tmp_path):
        """Pitches come from DRUM_NOTATION_MAP, not from anything invented here."""
        # Arrange
        target = tmp_path / "drums.mid"
        expected = {DRUM_NOTATION_MAP["kick"]["midi_program"], DRUM_NOTATION_MAP["snare"]["midi_program"]}

        # Act
        export_to_midi(classified_events=events, output_path=str(target))

        # Assert
        assert {n.pitch for n in parsed_track(target).notes} == expected

    def test_unknown_instruments_are_skipped_not_fatal(self, tmp_path):
        """
        An instrument the map does not know is dropped quietly.

        The classifier emits ``unknown`` when it cannot decide, and one
        undecidable hit must not cost you the whole file.
        """
        # Arrange
        target = tmp_path / "drums.mid"
        events = [
            {"time_sec": 0.0, "instruments": ["kick"]},
            {"time_sec": 0.5, "instruments": ["unknown"]},
        ]

        # Act
        export_to_midi(classified_events=events, output_path=str(target))

        # Assert
        assert len(parsed_track(target).notes) == 1

    def test_empty_event_list_still_writes_a_file(self, tmp_path):
        """
        Silence in, empty MIDI out, no exception.

        build_score reports a path only when the write succeeded, so this
        failing would be reported as a missing MIDI rather than an empty one.
        """
        # Arrange
        target = tmp_path / "drums.mid"

        # Act
        export_to_midi(classified_events=[], output_path=str(target))

        # Assert
        assert target.is_file()

    @pytest.mark.parametrize("tempo", [60.0, 120.0, 174.0])
    def test_tempo_is_written_into_the_file(self, events, tmp_path, tempo):
        """
        The detected tempo must survive into the MIDI, or the DAW grid is wrong.

        Read via ``get_tempo_changes()``, which returns what was actually written
        to the tempo track. ``estimate_tempo()`` is not used here: it infers a
        tempo from note spacing and returns 120 for all three of these, which
        would make the test pass whatever we wrote.
        """
        # Arrange
        target = tmp_path / f"drums_{int(tempo)}.mid"

        # Act
        export_to_midi(classified_events=events, output_path=str(target), tempo=tempo)

        # Assert
        _, tempi = pretty_midi.PrettyMIDI(str(target)).get_tempo_changes()
        assert tempi[0] == pytest.approx(tempo, rel=0.001)

    def test_note_times_match_the_events(self, events, tmp_path):
        """Onset times must land where the classifier said they were."""
        # Arrange
        target = tmp_path / "drums.mid"

        # Act
        export_to_midi(classified_events=events, output_path=str(target))

        # Assert
        starts = sorted(n.start for n in parsed_track(target).notes)
        assert starts == pytest.approx([0.0, 0.5, 1.0], abs=0.01)


# =============================================================================
# Helper
# =============================================================================


def parsed_track(path):
    """Reads a written MIDI file back and returns its single drum track."""
    return pretty_midi.PrettyMIDI(str(path)).instruments[0]
