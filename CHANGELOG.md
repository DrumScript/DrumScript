# Changelog

<!--date_added:thurs-28-may-2026-->
<!--date:updated:friday-10-july-2026-->


All notable changes to DrumScript will be documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
DrumScript follows [Semantic Versioning](https://semver.org/).

---
## Unreleased

### [0.2.0] - July 2026 - Target: *In progress*

### Fixed

* Adjusted documentation so that when version appears in documentation it is no longer hardcoded, but linked to `import importlib.metadata` in `drumscript/__init__.py` [Reduces maintenance burden on contributors]
* Updated version in pyproject.toml from `v0.1.5` to `v0.1.6` (This should have been changed *prior* to pypi release of v0.1.6 on Thursday 18 June 2026)
* Fixed `create_backing_track` runbook; replaced and tidied functions in drumscript_interactive_notebook on Colab

### Changed

* Updated table ordering in `docs/index.md` to match right sidebar ordering and added missing sidebar navigation point for tempogram-detection
* Amended documentation to remove bold markdown formatting for H1 references feeding into the side-nav bar visual presentation, for all except `DrumScript CLI Reference`; fixed ordering side in toctree (docs/index.md) for `User Guide` submenu to 1. remove duplicated `usage` reference in toctree and 2. reorder items alphabetically. Amended right hand navbar so that H2 links are now alphabetical.
* Updated and tidied the examples for extract stems in README.md; split example up into extract stems and backing track function examples.
* Standardised git tag naming convention from `drumscript__vX.Y.Z-alpha` to `vX.Y.Z` (e.g. `v0.1.6`). Old tags remain on remote (branch protection prevents deletion) but are ignored by the `docs.yml` workflow which only triggers on `v*`.

### Added

* Versioned documentation deployment via `docs.yml` GitHub Actions workflow (`docs/versioned-deploy` branch):
  - Documentation now deploys to version-specific folders on `gh-pages` (e.g. `/v0.1.6/`, `/v0.2.0/`)
  - Tag pushes (`v*`) deploy to both `/<tag>/` and `/latest/` folders
  - Main branch pushes deploy to `/dev/` folder (bleeding-edge docs)
  - Root `index.html` auto-generated on tag push, redirects to `/latest/`
  - `keep_files: true` ensures older version folders are never deleted
  - Existing root-level docs remain untouched until explicit cleanup
  - Contributor and Developer updated guidance

### Audited

* Did full audit of all `drumscript` code to ensure `full-flag` / `full_flag` consistency throughout, following v0.1.6 release fix replacing `full=True` with `verbose=True` (`DeprecationShim`)

---

### [0.2.0+] - August 2026 - Target: TBC

> First minor-version bump. 
><!--> Signals the start of the breaking-change track for --full flag (replaced by --verbose) ahead of v1.0.0 beta.-->

#### Planned — Bug Fixes
- Cymbal and hi-hat stem rendering: note tails and heads correctly aligned
- `ds.transcribe()` only outputs PDF, not the documented `.json` / `.midi` / `.xml`
- `main.py` structural bug: duplicated pipeline inside `except` block needs removing, error handling needs restructuring
- `drumscript/main.py` (~line 26) `.wav` comment. Check if this is actually true across all scripts in `drumscript/` modular code.

#### Planned — Changes
- Transcription function docstrings to be updated to make clear that drum-only audio is expected as standard input
- README to be updated to clarify expected input for transcription functions
- Example notebooks to be updated to reflect expected drum-only audio input
- Better audio samples needed for runbooks — not synthetic, which has created messy outputs
- Runbook presentation to be tidied: one variable per line, properly tested
- Improve documentation: clearer docstrings for the `rudiment` flag/functionality
- Check if `is_rudiment` applies to `score_builder` function — is it relevant, per `drumscript/main.py`?
- Refactor `main.py` argparse block into a `build_parser()` function so `tests/unit/test_cli_args.py` can import the real parser instead of mirroring it

#### Planned — Additions
- CHANGELOG reference to be added to README and Sphinx docs
- `output_midi`, `output_json`, `output_xml` flags to be added to `transcribe()` for multi-format export
- Expanded benchmark dataset coverage (ENST-Drums, MDB-Drums) building on the IDMT-SMT-Drums V2 foundation shipped in v0.1.6
- Code-to-DrumScript label mapping expanded beyond `KD`/`SD`/`HH` to cover full-kit classes (toms, crash, ride)

#### Planned — Investigation
- **Onset timing precision**: investigate user feedback on score generation. Though quantisation is used, look at the extent to which slight imperfections in onset detection cause notes to be placed at incorrect positions in the score (e.g. snare hit at 0.503s instead of 0.500s generates spurious rests). https://github.com/DrumScript/DrumScript/issues/274

---

### [1.0.0] - Beta release - Target: TBD

#### Planned — Removed (breaking)
- `full` parameter removed entirely from `transcribe()`, `extract_stems()`, and `detect_tempo()`. Users must use `verbose` instead.
- Deprecation warning removed (no longer needed)
- `tests/unit/test_deprecation_warnings.py` deleted (or flipped to assert `full` now raises `TypeError`)

---

## Released

### [0.1.6] - June 2026

> **`v0.1.6` is the final v0.1.*x* release.** 
> After this, the next release jumps to v0.2.0 to signal the deprecation shim for the `full` → `verbose` removal.

#### Added
- Deprecation shim for `full` parameter on the Python API:
  - New `verbose` parameter added to `transcribe()`, `extract_stems()`, and `detect_tempo()` as the canonical replacement for `full`
  - Passing `full=True` (or `full=False`) continues to work but emits a `DeprecationWarning` directing users to `verbose`
  - Warning explicitly names the v1.0.0 (beta) removal target so users have a clear migration timeline
  - Passing both `full` and `verbose` together raises `TypeError` (ambiguous, almost certainly a bug)
  - Internal helper `_resolve_verbose_flag()` centralises the resolution logic so it cannot drift between wrappers
  - Docstrings updated to mark `verbose` as primary and `full` as deprecated
- **PR #273 by nanaoto** — IDMT-SMT-Drums V2 benchmark runner with `mir_eval` scaffolding:
  - `benchmarks/run.py` entrypoint with dataset adapter dispatch, evaluation loop, CSV/JSON archive with git commit tracking
  - `drumscript/datasets/` package: `BenchmarkItem` dataclass and IDMT adapter (XML/SVL annotation parsing)
  - `benchmarks/README.md` documenting conventions, dataset setup, and planned dataset coverage
  - Unit tests for benchmark runner (`test_benchmarks_run.py`) and IDMT dataset adapter (`test_idmt_dataset.py`)
  - `mir_eval` added as a dev dependency
- New unit test file `tests/unit/test_deprecation_warnings.py` (13 tests)
- New unit test file `tests/unit/test_cli_args.py` (4 tests)

#### Fixed
- Commented-out dead code removed from `drumscript/__init__.py` and `drumscript/main.py`
- Flag inconsistency between `drumscript/main.py` and `drumscript/__init__.py` resolved: `argparse` in main block updated so the CLI flag is now `--full-song` (hyphenated, consistent with `--all-stems`). Auto-converts to `args.full_song` matching the Python API parameter name.


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