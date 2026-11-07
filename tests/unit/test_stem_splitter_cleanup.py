"""
What these tests pin
--------------------
1. No error path may delete the directory Demucs was told to write into, nor
   anything in it that DrumScript did not create.
2. The leaf folder Demucs itself creates may still be cleaned up.
3. Demucs is invoked through the current interpreter rather than a console
   script on PATH, which is why the reporter's install could not find it.

The tests drive the real error paths with Demucs stubbed out. Nothing here
needs Demucs, torch or any audio.
"""

import subprocess
from unittest.mock import patch

import pytest

from drumscript.audio_processor import stem_splitter
from drumscript.audio_processor.stem_splitter import DEMUCS_MODEL, extract_drum_stem

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def working_dir(tmp_path, monkeypatch):
    """
    A stand-in for the user's working directory, holding files they care about.

    The point of the bug was that these files had nothing to do with DrumScript
    and were destroyed anyway, so they are what the assertions check for.
    """
    (tmp_path / "song.flac").write_bytes(b"not really audio")
    (tmp_path / "tax_return.pdf").write_bytes(b"important")
    (tmp_path / "photos").mkdir()
    (tmp_path / "photos" / "holiday.jpg").write_bytes(b"irreplaceable")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def assert_user_files_survived(working_dir):
    """The whole point of #356. Every one of these is a file DrumScript did not create."""
    assert working_dir.is_dir(), "the working directory itself was deleted"
    assert (working_dir / "song.flac").is_file(), "the user's input audio was deleted"
    assert (working_dir / "tax_return.pdf").is_file(), "an unrelated user file was deleted"
    assert (working_dir / "photos" / "holiday.jpg").is_file(), "an unrelated user directory was emptied"


# =============================================================================
# The three error paths
# =============================================================================


class TestErrorPathsDoNotDeleteTheWorkingDirectory:
    """Each error path in extract_drum_stem, driven with Demucs stubbed out."""

    def test_demucs_not_installed(self, working_dir):
        """
        The reporter's exact case: Demucs missing, nothing written yet.

        Before the fix this deleted the working directory and raised afterwards,
        so the user saw the error message and lost the folder anyway.
        """
        # Arrange / Act
        with patch("subprocess.run", side_effect=FileNotFoundError("demucs")):
            with pytest.raises(FileNotFoundError):
                extract_drum_stem(str(working_dir / "song.flac"))

        # Assert
        assert_user_files_survived(working_dir)

    def test_demucs_runs_but_fails(self, working_dir):
        """A non-zero exit from Demucs must not cost the user their directory."""
        # Arrange
        failure = subprocess.CalledProcessError(returncode=1, cmd=["demucs"], output="", stderr="boom")

        # Act
        with patch("subprocess.run", side_effect=failure):
            with pytest.raises(RuntimeError):
                extract_drum_stem(str(working_dir / "song.flac"))

        # Assert
        assert_user_files_survived(working_dir)

    def test_demucs_succeeds_but_writes_no_drum_stem(self, working_dir):
        """
        The third path, and the worst of the three.

        It called ``shutil.rmtree`` with no ``ignore_errors``, so it deleted the
        directory outright rather than skipping anything it could not remove.
        """
        # Arrange / Act
        with patch("subprocess.run", return_value=subprocess.CompletedProcess([], 0, "", "")):
            with pytest.raises(FileNotFoundError):
                extract_drum_stem(str(working_dir / "song.flac"))

        # Assert
        assert_user_files_survived(working_dir)

    def test_explicit_output_dir_is_also_safe(self, working_dir, tmp_path):
        """
        A directory the caller named is theirs too, not ours to delete.

        The default is ``Path.cwd()``, but a caller passing ``output_dir``
        explicitly was equally exposed.
        """
        # Arrange
        chosen = tmp_path / "my_stems"
        chosen.mkdir()
        (chosen / "keep_me.txt").write_text("user data")

        # Act
        with patch("subprocess.run", side_effect=FileNotFoundError("demucs")):
            with pytest.raises(FileNotFoundError):
                extract_drum_stem(str(working_dir / "song.flac"), output_dir=str(chosen))

        # Assert
        assert chosen.is_dir(), "the caller's chosen output directory was deleted"
        assert (chosen / "keep_me.txt").is_file(), "a file in the caller's output directory was deleted"


# =============================================================================
# Cleanup still has to do its job
# =============================================================================


class TestCleanupStillRemovesWhatDemucsCreated:
    """Not deleting the parent must not mean leaving partial output behind."""

    def test_partial_demucs_output_is_removed(self, working_dir):
        """A half-written Demucs folder is ours, so it goes."""
        # Arrange
        partial = working_dir / DEMUCS_MODEL / "song"
        partial.mkdir(parents=True)
        (partial / "bass.wav").write_bytes(b"partial output")

        # Act
        with patch("subprocess.run", side_effect=FileNotFoundError("demucs")):
            with pytest.raises(FileNotFoundError):
                extract_drum_stem(str(working_dir / "song.flac"))

        # Assert
        assert not partial.exists(), "partial Demucs output was left behind"
        assert_user_files_survived(working_dir)

    def test_cleanup_helper_ignores_a_directory_it_did_not_create(self, tmp_path):
        """Called against a directory with no Demucs output, it must do nothing at all."""
        # Arrange
        (tmp_path / "untouched.txt").write_text("data")

        # Act
        stem_splitter._cleanup_demucs_output(str(tmp_path), "song.flac")

        # Assert
        assert tmp_path.is_dir()
        assert (tmp_path / "untouched.txt").is_file()

    def test_empty_model_folder_is_removed(self, working_dir):
        """
        Demucs creates its model folder before it reads the audio.

        A failure at the audio-loading stage therefore leaves an empty ``htdemucs/``
        sitting in the user's directory. Cosmetic rather than harmful, but still ours.
        """
        # Arrange
        model_dir = working_dir / DEMUCS_MODEL
        model_dir.mkdir()

        # Act
        with patch("subprocess.run", side_effect=FileNotFoundError("demucs")):
            with pytest.raises(FileNotFoundError):
                extract_drum_stem(str(working_dir / "song.flac"))

        # Assert
        assert not model_dir.exists(), "an empty Demucs model folder was left behind"
        assert_user_files_survived(working_dir)

    def test_model_folder_with_unrelated_content_is_kept(self, working_dir):
        """
        The safety property behind using ``rmdir()`` rather than ``rmtree()``.

        A user who happens to keep their own folder of this name, with files in it,
        keeps it. ``rmdir()`` refuses to remove a non-empty directory.
        """
        # Arrange
        model_dir = working_dir / DEMUCS_MODEL
        model_dir.mkdir()
        (model_dir / "my_notes.txt").write_text("mine, not DrumScript's")

        # Act
        with patch("subprocess.run", side_effect=FileNotFoundError("demucs")):
            with pytest.raises(FileNotFoundError):
                extract_drum_stem(str(working_dir / "song.flac"))

        # Assert
        assert model_dir.is_dir(), "a non-empty directory was removed"
        assert (model_dir / "my_notes.txt").is_file(), "a user file inside it was removed"


# =============================================================================
# How Demucs is invoked
# =============================================================================


class TestDemucsIsInvokedAsAModule:
    """
    ``uv tool install drumscript`` links DrumScript's entry point but not Demucs's.

    The package is installed and importable, but the ``demucs`` console script is
    not on PATH, which is why the reporter hit the missing-command path at all.
    Running it through the current interpreter removes that dependency.
    """

    def test_command_uses_the_current_interpreter(self, working_dir):
        """The command must be ``<python> -m demucs ...``, not a bare ``demucs``."""
        # Arrange / Act
        with patch("subprocess.run", side_effect=FileNotFoundError("x")) as mock_run:
            with pytest.raises(FileNotFoundError):
                extract_drum_stem(str(working_dir / "song.flac"))

        # Assert
        command = mock_run.call_args[0][0]
        assert command[1:3] == ["-m", "demucs"], f"expected a module invocation, got {command[:3]}"
        assert command[0] != "demucs", "still relying on the console script being on PATH"

    def test_missing_module_gives_an_actionable_message(self, working_dir):
        """
        A missing Demucs now surfaces as a non-zero exit, so the message matters.

        Without this the user gets a raw Python traceback pasted into the error.
        """
        # Arrange
        failure = subprocess.CalledProcessError(returncode=1, cmd=["python", "-m", "demucs"], output="", stderr="No module named demucs")

        # Act
        with patch("subprocess.run", side_effect=failure):
            with pytest.raises(RuntimeError, match="Demucs is not installed"):
                extract_drum_stem(str(working_dir / "song.flac"))

        # Assert
        assert_user_files_survived(working_dir)
