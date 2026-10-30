"""
Unit tests for ``drumscript.main`` CLI argument parsing.

What this file covers
---------------------
- The CLI flag is ``--full-song`` (hyphen, CLI convention) and parses to
  ``args.full_song`` (underscore, Python attribute) via argparse's automatic
  hyphen-to-underscore conversion.
- The legacy bare ``--full`` flag is rejected. This flag was renamed in v0.1.6
  to disambiguate the CLI from the Python API's ``full=True`` (which means
  "return detailed dict", an entirely different concept).
- The underscore variant ``--full_song`` is rejected. We enforce the hyphen
  convention for consistency with ``--all-stems`` and standard CLI norms
  (git, pip, docker, ffmpeg etc. all use hyphens, not underscores).
- The ``--midi-only`` flag is accepted and defaults to False.

Why this file exists
--------------------
The ``--full`` / ``--full-song`` / ``--full_song`` / ``full_song=True`` /
``full=True`` namespace caused real confusion during the v0.1.6 refactor.
These tests lock in the current behaviour so future edits (human or AI-assisted)
cannot silently reintroduce the ambiguity.

What this file does NOT cover
-----------------------------
- The Python API's ``full=True`` and ``full_song=True`` parameters — those
  are covered in ``test_transcribe.py``.
- End-to-end behaviour of ``main()`` — these tests only exercise the
  argument parser.
"""

from unittest.mock import patch

import pytest

from drumscript.main import build_parser, cli

# =============================================================================
# Tests
# =============================================================================


class TestFullSongFlag:
    """Lock in the ``--full-song`` CLI flag contract."""

    def test_full_song_flag_parses_with_hyphen(self):
        """``--full-song`` is the canonical CLI form and sets ``args.full_song = True``."""
        parser = build_parser()
        args = parser.parse_args(["my_song.mp3", "--full-song"])
        assert args.full_song is True
        assert args.input_audio_path == "my_song.mp3"

    def test_full_song_flag_absent_defaults_to_false(self):
        """Omitting ``--full-song`` leaves ``args.full_song`` as False."""
        parser = build_parser()
        args = parser.parse_args(["my_song.mp3"])
        assert args.full_song is False

    def test_legacy_bare_full_flag_still_works_as_prefix(self):
        """
        ``--full`` is accepted as an unambiguous prefix of ``--full-song``.

        Before v0.1.6 the CLI used ``--full`` to mean "full song". It was
        renamed to ``--full-song`` to disambiguate from the Python API's
        ``full=True`` (return detailed dict).

        argparse's default behaviour is to accept unambiguous flag prefixes,
        so ``--full`` continues to work as backwards-compat shorthand. If
        another ``--full*`` flag is ever added (e.g. ``--full-mix``), this
        test will fail — which is the correct signal to either rename one of
        them or call the parser with ``allow_abbrev=False``.
        """
        parser = build_parser()
        args = parser.parse_args(["my_song.mp3", "--full"])
        assert args.full_song is True

    def test_underscore_variant_is_rejected(self):
        """
        ``--full_song`` (underscore) must error.

        argparse treats hyphens and underscores in CLI flag *names* as
        different. We standardise on hyphens to match ``--all-stems`` and
        general CLI convention.
        """
        parser = build_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["my_song.mp3", "--full_song"])


class TestMidiOnlyFlag:
    """Tests for the ``--midi-only`` CLI flag."""

    def test_midi_only_flag_parses(self):
        parser = build_parser()
        args = parser.parse_args(["my_song.mp3", "--midi-only"])

        assert args.midi_only is True
        assert args.input_audio_path == "my_song.mp3"

    def test_midi_only_flag_defaults_to_false(self):
        parser = build_parser()
        args = parser.parse_args(["my_song.mp3"])

        assert args.midi_only is False

    def test_midi_only_cli_calls_export_midi(self, monkeypatch):
        """The CLI should route --midi-only to direct audio-to-MIDI export."""
        monkeypatch.setattr(
            "sys.argv",
            ["drumscript", "my_song.wav", "--midi-only"],
        )

        with patch(
            "drumscript.main.export_midi",
            return_value="outputs/my_song.mid",
        ) as mock_export:
            cli()

        mock_export.assert_called_once_with(
            "my_song.wav",
            from_audio=True,
            full_song=False,
            is_rudiment=False,
        )
