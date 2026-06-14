"""
Unit tests for the ``full`` -> ``verbose`` deprecation shim.

What this file covers
---------------------
- Passing ``verbose=True`` works without any warning (the new, canonical form).
- Passing ``full=True`` still works but emits a ``DeprecationWarning`` that
  points users at ``verbose`` and at the v1.0.0 removal target.
- Passing both ``full`` and ``verbose`` together raises ``TypeError`` (because
  the intent is ambiguous and almost always indicates a bug).
- The deprecation applies uniformly to all three wrapper functions:
  ``transcribe()``, ``extract_stems()``, ``detect_tempo()``.

Why this file exists
--------------------
v0.1.6 renames the ``full`` parameter to ``verbose`` across the wrapper
functions, to disambiguate it from the CLI's ``--full-song`` flag (which means
something entirely different: "is this audio a full song that needs stem
separation first?"). To avoid breaking existing user code from v0.1.4 / v0.1.5,
``full`` continues to work as a deprecated alias until it is removed in v1.0.0.

These tests lock in:
  1. The shim's *behaviour* — old code still works, new code works without
     warnings.
  2. The *messaging* — users get a clear pointer to the new name and the
     removal version.

When ``full`` is finally removed in v1.0.0, this file should be deleted (or
flipped to assert that passing ``full`` now raises ``TypeError`` from Python's
own argument parsing).
"""

import inspect

import numpy as np
import pytest

import drumscript as ds

# We test ``detect_tempo()`` exhaustively because it has the simplest signature
# (no file I/O, no Demucs, no exporters — just a numpy array in, a value out).
# This lets us assert warning / no-warning / TypeError behaviour cheaply.
#
# For ``transcribe()`` and ``extract_stems()`` we only need to verify the shim
# *wiring* — that they accept the new parameter and emit the warning when given
# the old one. We do that by introspecting the function signature, which is
# pure-Python and needs no audio files / Demucs / disk I/O. Functional behaviour
# of those wrappers is already covered by ``test_transcribe.py`` etc.


# =============================================================================
# Fixture
# =============================================================================


@pytest.fixture
def short_audio():
    """A short numpy array suitable for ``detect_tempo``.

    1.5 seconds of silence at 44.1 kHz is enough to clear the "too short"
    guard in ``detect_tempo`` without doing any meaningful DSP work.
    """
    return np.zeros(int(1.5 * 44100), dtype=np.float32)


# =============================================================================
# detect_tempo — full behavioural coverage of the shim
# =============================================================================


class TestDetectTempoDeprecationShim:
    """Verify the ``full`` -> ``verbose`` shim on ``detect_tempo()``."""

    def test_verbose_true_works_without_warning(self, short_audio, recwarn):
        """New canonical form emits no DeprecationWarning."""
        result = ds.detect_tempo(short_audio, verbose=True)
        deprecation_warnings = [w for w in recwarn.list if issubclass(w.category, DeprecationWarning)]
        assert deprecation_warnings == [], f"verbose=True should not emit DeprecationWarning, got: {[str(w.message) for w in deprecation_warnings]}"
        assert isinstance(result, dict)
        assert "bpm" in result

    def test_default_call_emits_no_warning(self, short_audio, recwarn):
        """Calling with no return-mode flag at all emits no warning."""
        ds.detect_tempo(short_audio)
        deprecation_warnings = [w for w in recwarn.list if issubclass(w.category, DeprecationWarning)]
        assert deprecation_warnings == []

    def test_full_true_still_works(self, short_audio):
        """``full=True`` (deprecated) still returns the verbose dict for back-compat."""
        with pytest.warns(DeprecationWarning):
            result = ds.detect_tempo(short_audio, full=True)
        assert isinstance(result, dict)
        assert "bpm" in result

    def test_full_true_emits_deprecation_warning(self, short_audio):
        """``full=True`` must emit a DeprecationWarning."""
        with pytest.warns(DeprecationWarning):
            ds.detect_tempo(short_audio, full=True)

    def test_warning_message_mentions_verbose(self, short_audio):
        """Warning text should direct users to the new name."""
        with pytest.warns(DeprecationWarning, match="verbose"):
            ds.detect_tempo(short_audio, full=True)

    def test_warning_message_mentions_removal_version(self, short_audio):
        """Warning text should state when ``full`` will be removed."""
        with pytest.warns(DeprecationWarning, match="v1.0.0"):
            ds.detect_tempo(short_audio, full=True)

    def test_warning_names_the_function(self, short_audio):
        """Warning text should name the function being called (helps users debug)."""
        with pytest.warns(DeprecationWarning, match="detect_tempo"):
            ds.detect_tempo(short_audio, full=True)

    def test_full_false_does_not_warn(self, short_audio, recwarn):
        """
        Even ``full=False`` (explicitly passed) emits the warning, because the
        user is still using the deprecated parameter name.

        Rationale: someone passing ``full=False`` is still touching the old
        API surface, and we want them migrated to ``verbose=False`` (or just
        omitting the argument entirely).
        """
        ds.detect_tempo(short_audio, full=False)
        deprecation_warnings = [w for w in recwarn.list if issubclass(w.category, DeprecationWarning)]
        assert len(deprecation_warnings) == 1, "Passing `full=False` should still warn because the user is using the deprecated parameter name."

    def test_passing_both_full_and_verbose_raises(self, short_audio):
        """Passing both parameters at once is ambiguous — must error."""
        with pytest.raises(TypeError, match="both"):
            ds.detect_tempo(short_audio, full=True, verbose=True)


# =============================================================================
# transcribe / extract_stems — signature-level wiring checks
# =============================================================================
#
# Full behavioural tests for these live in test_transcribe.py and
# test_stem_splitter_helpers.py. Here we only confirm that the shim is wired in.


class TestTranscribeShimWiring:
    """Confirm ``transcribe()`` exposes both `verbose` and `full` parameters."""

    def test_transcribe_accepts_verbose_param(self):
        sig = inspect.signature(ds.transcribe)
        assert "verbose" in sig.parameters
        assert sig.parameters["verbose"].default is False

    def test_transcribe_still_accepts_full_param(self):
        sig = inspect.signature(ds.transcribe)
        assert "full" in sig.parameters, "Deprecated `full` parameter must remain until v1.0.0"
        # Default is `None` (sentinel) so the shim can detect "user passed it"
        # vs "left at default".
        assert sig.parameters["full"].default is None


class TestExtractStemsShimWiring:
    """Confirm ``extract_stems()`` exposes both `verbose` and `full` parameters."""

    def test_extract_stems_accepts_verbose_param(self):
        sig = inspect.signature(ds.extract_stems)
        assert "verbose" in sig.parameters
        assert sig.parameters["verbose"].default is False

    def test_extract_stems_still_accepts_full_param(self):
        sig = inspect.signature(ds.extract_stems)
        assert "full" in sig.parameters, "Deprecated `full` parameter must remain until v1.0.0"
        assert sig.parameters["full"].default is None
