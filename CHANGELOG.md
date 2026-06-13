# Changelog

<!--date_added:thurs-28-may-2026-->
<!--date:updated:sat-13-june-2026-->


All notable changes to DrumScript will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
DrumScript follows [Semantic Versioning](https://semver.org/).

---

## Unreleased

### [0.1.6] - June 2026 - Target: 14 June 2026

> **Final v0.1.x release.** After this, the next release jumps to v0.2.0 to signal the breaking-change track for the `full` → `verbose` rename.

#### Planned — Bug Fixes
- Cymbal and hi-hat stem rendering: note tails and heads correctly aligned
- `ds.transcribe()` only outputs PDF, not the documented `.json` / `.midi` / `.xml`
- `main.py` structural bug: duplicated pipeline inside `except` block needs removing, error handling needs restructuring
- `drumscript/main.py` (~line 26) `.wav` comment `# .wav format as default, unless --mp3 input specified as an arg in user command`. Check if this is actually true across all scripts in `drumscript/` modular code.

#### Planned — Changes
- Transcription function docstrings to be updated to make clear that drum-only audio is expected as standard input
- README to be updated to clarify expected input for transcription functions
- Example notebooks to be updated to reflect expected drum-only audio input
- Better audio samples needed for runbooks — not synthetic, which has created messy outputs
- Runbook presentation to be tidied: one variable per line, properly tested

#### Planned — Additions
- CHANGELOG reference to be added to README and Sphinx docs
- `output_midi`, `output_json`, `output_xml` flags to be added to `transcribe()` for multi-format export
- Deprecation shim for `full` parameter (Python API):
  - Add `verbose` parameter alongside existing `full` on `transcribe()`, `extract_stems()`, and `detect_tempo()`
  - Passing `full=True` continues to work but emits a `DeprecationWarning` directing users to `verbose=True`
  - Warning states `full` will be removed in v1.0.0 (beta release)
  - Docstrings updated to mark `verbose` as primary and `full` as deprecated
  - New unit test confirms the warning is actually emitted

#### Moved to Future Release (PR reviews requested of contributor)
- PR #273 by nanaoto (IDMT-SMT-Drums V2 benchmark runner with `mir_eval` scaffolding) — moved to v0.2.0

#### Fixed
- Commented-out dead code removed from `drumscript/__init__.py` and `drumscript/main.py`
- Flag inconsistency between `drumscript/main.py` and `drumscript/__init__.py` resolved: `argparse` in main block updated so the CLI flag is now `--full-song` (hyphenated, consistent with `--all-stems`). Auto-converts to `args.full_song` matching the Python API parameter name.
- Regression test added (`tests/unit/test_cli_args.py`) locking in `--full-song` as the canonical CLI flag

---

### [0.2.0] - July/August 2026 - Target: TBD

> First minor-version bump. Signals the start of the breaking-change track ahead of v1.0.0 beta. `full` parameter still works here but warning continues.

#### Planned — Additions
- IDMT-SMT-Drums V2 benchmark runner (`benchmarks/run.py`) with `mir_eval` scaffolding (PR #273 by nanaoto)
- `drumscript/datasets/` package: `BenchmarkItem` dataclass and IDMT adapter
- Unit tests for benchmark runner and IDMT dataset adapter
- `benchmarks/README.md` documenting conventions and dataset setup

#### Planned — Changes
- Improve documentation: clearer docstrings for the `rudiment` flag/functionality
- Check if `is_rudiment` applies to `score_builder` function — is it relevant, per `drumscript/main.py`?
- QA check on recent GitHub release notes: https://github.blog/changelog/2026-05-15-github-app-installation-tokens-per-request-override-header/
- Refactor `main.py` argparse block into a `build_parser()` function so `tests/unit/test_cli_args.py` can import the real parser instead of mirroring it

#### Planned — Investigation
- **Onset timing precision**: investigate user feedback on score generation. Though quantisation is used, look at the extent to which slight imperfections in onset detection cause notes to be placed at incorrect positions in the score (e.g. snare hit at 0.503s instead of 0.500s generates spurious rests). https://github.com/DrumScript/DrumScript/issues/274

---

### [1.0.0] - Beta release - Target: TBD

#### Planned — Removed (breaking)
- `full` parameter removed entirely from `transcribe()`, `extract_stems()`, and `detect_tempo()`. Users must use `verbose` instead.
- Deprecation warning removed (no longer needed)

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
