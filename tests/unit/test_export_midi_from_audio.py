import pathlib
from unittest.mock import patch

import numpy as np
import pytest

from drumscript import export_midi


class TestExportMidiFromAudioErrors:
    """Tests for invalid inputs in audio-to-MIDI export mode."""

    def test_rejects_non_path_input(self):
        with pytest.raises(TypeError, match="score must be a path"):
            export_midi(123, from_audio=True)

    def test_missing_audio_file_raises(self, tmp_path):
        missing_file = tmp_path / "missing.wav"

        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            export_midi(missing_file, from_audio=True)


class TestExportMidiFromAudio:
    """Tests for exporting audio directly to MIDI."""

    @patch("drumscript.midi_exporter.export_to_midi")
    @patch("drumscript.classify_events")
    @patch("drumscript.detect_onsets")
    @patch("drumscript._internal_estimate")
    @patch("drumscript.normalise_audio")
    @patch("drumscript.load_audio")
    def test_exports_audio_to_midi(
        self,
        mock_load_audio,
        mock_normalise_audio,
        mock_estimate,
        mock_detect_onsets,
        mock_classify_events,
        mock_export,
        tmp_path,
        monkeypatch,
    ):

        monkeypatch.chdir(tmp_path)
        audio_file = tmp_path / "drums.wav"
        audio_file.touch()

        mock_load_audio.return_value = (np.zeros(22050), 22050)
        mock_normalise_audio.return_value = np.zeros(22050)
        mock_estimate.return_value = 120.0
        mock_detect_onsets.return_value = [0.0, 0.5]
        mock_classify_events.return_value = ["kick", "snare"]

        result = export_midi(audio_file, from_audio=True)

        expected_path = (tmp_path / "outputs" / "drums.mid").resolve()

        assert result == str(expected_path)
        mock_load_audio.assert_called_once()
        mock_classify_events.assert_called_once()
        mock_export.assert_called_once()

        export_kwargs = mock_export.call_args.kwargs
        assert export_kwargs["tempo"] == 120.0
        assert export_kwargs["classified_events"] == ["kick", "snare"]
        assert export_kwargs["output_path"] == str(pathlib.Path("outputs") / "drums.mid")

    @patch("drumscript.midi_exporter.export_to_midi")
    @patch("drumscript.classify_events")
    @patch("drumscript.detect_onsets")
    @patch("drumscript._internal_estimate")
    @patch("drumscript.normalise_audio")
    @patch("drumscript.load_audio")
    @patch("drumscript.extract_drum_stem")
    def test_full_song_extracts_drum_stem(
        self,
        mock_extract,
        mock_load_audio,
        mock_normalise_audio,
        mock_estimate,
        mock_detect_onsets,
        mock_classify_events,
        mock_export,
        tmp_path,
        monkeypatch,
    ):

        monkeypatch.chdir(tmp_path)
        audio_file = tmp_path / "song.wav"
        audio_file.touch()
        drum_stem = tmp_path / "drum_stem.wav"
        mock_extract.return_value = str(drum_stem)
        mock_load_audio.return_value = (np.zeros(22050), 22050)
        mock_normalise_audio.return_value = np.zeros(22050)
        mock_estimate.return_value = 120.0
        mock_detect_onsets.return_value = [0.0]
        mock_classify_events.return_value = ["kick"]

        export_midi(audio_file, from_audio=True, full_song=True)

        mock_extract.assert_called_once_with(str(audio_file))
        mock_load_audio.assert_called_once_with(str(drum_stem), sr=44100)

    @patch("drumscript.midi_exporter.export_to_midi")
    @patch("drumscript.classify_rudiment_events")
    @patch("drumscript.detect_onsets")
    @patch("drumscript._internal_estimate")
    @patch("drumscript.normalise_audio")
    @patch("drumscript.load_audio")
    def test_rudiment_mode_uses_rudiment_classifier(
        self,
        mock_load_audio,
        mock_normalise_audio,
        mock_estimate,
        mock_detect_onsets,
        mock_classify_rudiment,
        mock_export,
        tmp_path,
        monkeypatch,
    ):

        monkeypatch.chdir(tmp_path)
        audio_file = tmp_path / "rudiment.wav"
        audio_file.touch()
        mock_load_audio.return_value = (np.zeros(22050), 22050)
        mock_normalise_audio.return_value = np.zeros(22050)
        mock_estimate.return_value = 100.0
        mock_detect_onsets.return_value = [0.0]
        mock_classify_rudiment.return_value = ["snare"]

        export_midi(audio_file, from_audio=True, is_rudiment=True)

        mock_classify_rudiment.assert_called_once()
        mock_export.assert_called_once()

    @patch("drumscript.pdf_exporter")
    @patch("drumscript.xml_exporter")
    @patch("drumscript.midi_exporter.export_to_midi")
    @patch("drumscript.classify_events", return_value=["kick"])
    @patch("drumscript.detect_onsets", return_value=[0.0])
    @patch("drumscript._internal_estimate", return_value=120.0)
    @patch("drumscript.normalise_audio", side_effect=lambda audio: audio)
    @patch("drumscript.load_audio")
    def test_midi_only_does_not_generate_pdf_or_json(
        self,
        mock_load_audio,
        mock_normalise_audio,
        mock_estimate,
        mock_detect_onsets,
        mock_classify_events,
        mock_export,
        mock_xml_exporter,
        mock_pdf_exporter,
        tmp_path,
        monkeypatch,
    ):

        monkeypatch.chdir(tmp_path)
        audio_file = tmp_path / "drums.wav"
        audio_file.touch()
        mock_load_audio.return_value = (np.zeros(22050), 44100)

        export_midi(audio_file, from_audio=True)

        mock_export.assert_called_once()
        mock_pdf_exporter.assert_not_called()
        mock_xml_exporter.assert_not_called()
