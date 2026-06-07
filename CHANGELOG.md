
# Changelog

<!--date_added:thurs-28-may-2026-->
<!--date:updated:sun-07-june-2026-->


All notable changes to DrumScript will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
DrumScript follows [Semantic Versioning](https://semver.org/).

---
## Unreleased

### [0.1.6] - June 2026 - Target: 14 June 2026
#### Planned — Bug Fixes
- Cymbal and hi-hat stem rendering: note tails and heads correctly aligned
- `ds.transcribe()` only outputs PDF, not the documented `.json` / `.midi` / `.xml`
- `main.py` structural bug: duplicated pipeline inside `except` block needs removing, error handling needs restructuring
- Flag inconsistency: `full=True` means "return detailed dict" in Python API but `--full` means "full song / separate stems" in CLI — rename to `verbose=True` (or `detail=True` / `return_dict=True`) across all wrapper functions (`transcribe`, `extract_stems`, `detect_tempo`)

#### Planned — Changes
- Transcription function docstrings to be updated to make clear that drum-only audio is expected as standard input
- README to be updated to clarify expected input for transcription functions
- Example notebooks to be updated to reflect expected drum-only audio input
- Better audio samples needed for runbooks — not synthetic, which has created messy outputs
- Runbook presentation to be tidied: one variable per line, properly tested
- Commented-out dead code to be removed from `drumscript/__init__.py` and `drumscript/main.py`

#### Planned — Additions
- CHANGELOG reference to be added to README and Sphinx docs
- `output_midi`, `output_json`, `output_xml` flags to be added to `transcribe()` for multi-format export

#### Moved to Future Release (PR reviews requested of contributor)
- PR #273 by nanaoto (IDMT-SMT-Drums V2 benchmark runner with `mir_eval` scaffolding) (pending items)

### [0.1.7] - June/July 2026 - Target: TBD

#### Planned
- IDMT-SMT-Drums V2 benchmark runner (`benchmarks/run.py`) with `mir_eval` scaffolding (PR #273 by nanaoto)
- `drumscript/datasets/` package: `BenchmarkItem` dataclass and IDMT adapter
- Unit tests for benchmark runner and IDMT dataset adapter
- `benchmarks/README.md` documenting conventions and dataset setup
- **Onset timing precision**: investigate user-feedback on score generation. Though quantisation is used, look at the extent to which there are slight imperfections in onset detection cause notes to be placed at incorrect positions in the score (e.g. snare hit at 0.503s instead of 0.500s generates spurious rests). https://github.com/DrumScript/DrumScript/issues/274
 
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