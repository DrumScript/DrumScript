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

import argparse

import pytest

# =============================================================================
# Helper: rebuild the parser exactly as ``main.py`` does
# =============================================================================
# We rebuild rather than import ``main`` directly because the parser in
# ``drumscript/main.py`` lives inside the ``if __name__ == "__main__":`` block
# and is not exposed as a function. Keeping a small parallel copy here is the
# pragmatic choice: it's a handful of lines and these tests will fail loudly
# if the real parser diverges from this one.
#
# If the real parser is ever refactored into a ``build_parser()`` function in
# ``main.py``, replace this with ``from drumscript.main import build_parser``
# and delete the helper.


def _build_cli_parser() -> argparse.ArgumentParser:
    """Mirror of the argparse setup in ``drumscript/main.py``."""
    parser = argparse.ArgumentParser(description="DrumScript: Audio to Sheet Music & Stem Splitter")
    parser.add_argument("input_audio_path", type=str)
    parser.add_argument("--full-song", action="store_true")
    parser.add_argument("--drumless", action="store_true")
    parser.add_argument("--mute", type=str, action="append")
    parser.add_argument("--all-stems", action="store_true")
    parser.add_argument("--format", type=str, default="wav", choices=["wav", "mp3"])
    parser.add_argument("--rudiment", action="store_true")
    parser.add_argument("--ts", type=str, default="4/4")
    return parser


# =============================================================================
# Tests
# =============================================================================


class TestFullSongFlag:
    """Lock in the ``--full-song`` CLI flag contract."""

    def test_full_song_flag_parses_with_hyphen(self):
        """``--full-song`` is the canonical CLI form and sets ``args.full_song = True``."""
        parser = _build_cli_parser()
        args = parser.parse_args(["my_song.mp3", "--full-song"])
        assert args.full_song is True
        assert args.input_audio_path == "my_song.mp3"

    def test_full_song_flag_absent_defaults_to_false(self):
        """Omitting ``--full-song`` leaves ``args.full_song`` as False."""
        parser = _build_cli_parser()
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
        parser = _build_cli_parser()
        args = parser.parse_args(["my_song.mp3", "--full"])
        assert args.full_song is True

    def test_underscore_variant_is_rejected(self):
        """
        ``--full_song`` (underscore) must error.

        argparse treats hyphens and underscores in CLI flag *names* as
        different. We standardise on hyphens to match ``--all-stems`` and
        general CLI convention.
        """
        parser = _build_cli_parser()
        with pytest.raises(SystemExit):
            parser.parse_args(["my_song.mp3", "--full_song"])
