from unittest.mock import patch

from drumscript.main import main


def test_midi_only_exports_midi_without_running_normal_pipeline(capsys):
    with patch(
        "drumscript.main.export_midi",
        return_value="outputs/song.mid",
    ) as mock_export:
        main(
            "song.wav",
            full_song=True,
            is_rudiment=True,
            midi_only=True,
        )

    mock_export.assert_called_once_with(
        "song.wav",
        from_audio=True,
        full_song=True,
        is_rudiment=True,
    )

    captured = capsys.readouterr()
    assert "MIDI-only export complete: outputs/song.mid" in captured.out
    assert "Starting DrumScript" not in captured.out
