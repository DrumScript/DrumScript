
# Changelog

<!--date_added:thurs-28-may-2026-->
<!--date:updated:thurs-28-may-2026-->


All notable changes to DrumScript will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
DrumScript follows [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added

- IDMT-SMT-Drums benchmark runner with dataset adapter and unit test coverage.

---


## Planned

### [0.1.6] - June 2026

- Transcription function docstrings updated to make clear that drum-only audio is expected as standard input
- README updated to clarify expected input for transcription functions
- Example notebooks updated to reflect expected drum-only audio input
- Better audio samples used for runbooks, ie not synthetic, which has created messy outputs so far
- Cymbal and hi-hat stem rendering: note tails and heads correctly aligned

---

## Released

### [0.1.5] - May 2026

**Fixed**
- Emergency fix: transcription outputs
- Updated docstrings to clarify expected input for transcription functions

### [0.1.4] - 20 May 2026 (First PyPI publication)

**First release**
- Initial public alpha release to PyPI
- End-to-end CLI pipeline: stem separation → onset detection → classification → score generation
- Drum classification (kick, snare, hi-hat open/closed, toms, crash, ride) using deterministic spectral analysis
- PDF score generation with custom notation rendering
- MIDI and JSON export
- XML export support
- Drumless and bassless backing track generation
- Stem separation (drums, bass, vocals, other) via Demucs htdemucs 4-stem model
- Tempo detection from onset pattern
- Custom time signature support (e.g. 3/4, 6/8)
- ffmpeg-free WAV output path (soundfile + numpy)
- Google Colab notebook support

### Notes

- Alpha period: 01 June – 31 August 2026
- Beta target: v1.0.0
- TISMIR Educational Articles paper planned for beta release


---

<!--END-->