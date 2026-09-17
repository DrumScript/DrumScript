"""Unit tests for time-signature parsing in pdf_exporter (#297)."""

from drumscript.notation_generator.pdf_exporter import parse_time_signature


def test_valid_slash_form():
    assert parse_time_signature("3/4") == (3, 4)
    assert parse_time_signature("6/8") == (6, 8)
    assert parse_time_signature("4/4") == (4, 4)


def test_typo_44_warns_and_falls_back(capsys):
    assert parse_time_signature("44") == (4, 4)
    out = capsys.readouterr().out
    assert "Warning: invalid time signature '44'" in out
    assert "falling back to 4/4" in out


def test_underscore_form_warns_and_falls_back(capsys):
    assert parse_time_signature("3_4") == (4, 4)
    out = capsys.readouterr().out
    assert "Warning: invalid time signature '3_4'" in out
