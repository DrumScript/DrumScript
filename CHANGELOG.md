# **Changelog**

<!--date_added:thurs-28-may-2026-->
<!--date:updated:mon-24-august-2026-->


* All notable changes related to the repository and pypi distribution of `DrumScript` will be documented here
* Format follows **[Keep a Changelog](https://keepachangelog.com/en/1.0.0/)** and **[Semantic Versioning](https://semver.org/)**.
>
  > **[Keep a Changelog](https://keepachangelog.com/en/1.0.0/)** standard defines this order for naming items in a **`Changelog`**:
  > - **Added** — new features
  > - **Changed** — changes to existing functionality
  > - **Deprecated** — soon-to-be removed features
  > - **Removed** — removed features
  > - **Fixed** — bug fixes
  > - **Security** — vulnerability fixes

<!-->>> $$new -> fixes$$-->


- **[Unreleased](#unreleased)**
- **[Released](#released)**
- **[Future releases](#future-releases)**

---

> ## ***Unreleased***
*[back](#changelog)*

*forthcoming/in progress* 

> Items listed below are **currently in development** but **have not been distributed on PyPi**

> ### *Additions*
* added blurb to `README.md`, `docs/index.md` and `docs/about.md` about build process and current development people

> ### *Fixes*

* **Python 3.13 not supported.** DrumScript pins `numpy<2`, and numpy 1.x has no cp313 wheels on PyPI. This caused `pip install drumscript` on Python 3.13 to fall back to a source build (which requires a C toolchain most users don't have), producing a confusing `Compiler cc cannot compile programs` error rather than a clear "unsupported Python version" message. `requires-python` lowered from `<3.14` to `<3.13` in `pyproject.toml`. Python 3.13 support planned once DrumScript migrates to `numpy>=2` (see [#303](https://github.com/DrumScript/DrumScript/issues/303)).


---

### ***Future releases***
*[back](#changelog)*

Items listed below are fully implemented and **published to pypi** under an official version

<!--#### ***August 2026 and beyond***-->

##### **[1.0.0] - Beta release - Target: late-2026**
>
###### *Additions*
- `output_midi`, `output_json`, `output_xml` flags to be added to `transcribe()` for multi-format export
- Expanded benchmark dataset coverage (ENST-Drums, MDB-Drums) building on the IDMT-SMT-Drums V2 foundation shipped in v0.1.6
- Code-to-DrumScript label mapping expanded beyond `KD`/`SD`/`HH` to cover full-kit classes (toms, crash, ride)
- Repository statistics badge (shields.io endpoint) for README and docs homepage: extend `repo-stats.yml` to write a small JSON (`schemaVersion`, `label`, `message`, `color`) to the `github-repo-stats` branch on each daily run, so shields.io can render live view/clone counts rather than a static link #296
- Check compatibility for Python 3.13 (#299)
>
###### *Changes*
- Transcription function docstrings to be updated to make clear that drum-only audio is expected as standard input
- README to be updated to clarify expected input for transcription functions
- Example notebooks to be updated to reflect expected drum-only audio input
- Better audio samples needed for runbooks — not synthetic, which has created messy outputs
- Runbook presentation to be tidied: one variable per line, properly tested
- Improve documentation: clearer docstrings for the `rudiment` flag/functionality
- Check if `is_rudiment` applies to `score_builder` function — is it relevant, per `drumscript/main.py`?
- Refactor `main.py` argparse block into a `build_parser()` function so `tests/unit/test_cli_args.py` can import the real parser instead of mirroring it
- Clarify in docs/docstrings that input format is not limited to .wav/.mp3 — any format librosa (+ ffmpeg) supports works. ffmpeg is only required for MP3 input decoding and MP3 stem output
>
  *(breaking)*
  *  `full` parameter removed entirely from `transcribe()`, `extract_stems()`, and `detect_tempo()`. Users must use `verbose` instead. 
  *  This was implemented as a deprecation shim in [v0.1.6 release](#016---june-2026)
  *  Deprecation warning for `--full= flag` will be removed
  *  `tests/unit/test_deprecation_warnings.py` deleted (or flipped to assert `full` now raises `TypeError`)
  *  From 1.0.0 (beta) the flag `verbose=` will provide dictionary-based outputs, ie for cli-users and developers.
  *  This change, originally, was made in  [v0.1.6 release](#016---june-2026) to prevent confusion between `--full` flag outputting verbose in drumscript wrappers and the `full=true` functionality for specifying within `transcribe()` function that the input audio is polyphonic (non-drum-only) and therefore requires Demucs extraction *prior* to applying DrumScript's deterministic classification model for transcription. 
  *  As a side note, and for completeness, DrumScript functions default to drum-audio only inputs. User must indicate if the input_audio is not solo drum audio.
  *  `_TranscribeResult` string compatibility removed — `transcribe()` returns a plain `dict`
  *  `docs/guide/usage.md`: the silent 4/4 fallback in `pdf_exporter.py` line 138 is a code smell independent of the docs — a user typo like `--ts 44` also silently becomes 4/4. A `print` warning in that `except ValueError` would be a small improvement on documentation #297
>
###### *Fixes*
- Cymbal and hi-hat stem rendering: note tails and heads correctly aligned
- `main.py` structural bug: duplicated pipeline inside `except` block needs removing, error handling needs restructuring
- `ds.transcribe()` return value only references PDF path, but `score_builder.build_score()` silently writes JSON + MIDI too. Output behaviour needs documenting clearly and aligning between CLI and Python API
- `ds.extract_stems(verbose=True)` does not return the backing-track path (#266). It calls `separate_audio()`, whose dict includes the backing-track path under `mix`, but then discards that dict and builds its own (`status`, `drum_stem_path`, `original_file`, `output_directory`) — dropping the one path the user asked for when calling with `drumless=True`. The backing track is created on disk but its location is never reported, so the caller has to reconstruct it from `output_directory` plus the `<input>_no_drums.<ext>` naming convention. Fix: carry the path through from `separate_audio()` under a readable key, `backing_track_path` (rather than reintroducing the terse `mix`), and update the README backing-track example to use it. Keeps the readable key names introduced in v0.2.0 while restoring the missing path (#298)
>
###### *Tests*
- **Onset timing precision**: investigate user feedback on score generation. Though quantisation is used, look at the extent to which slight imperfections in onset detection cause notes to be placed at incorrect positions in the score (e.g. snare hit at 0.503s instead of 0.500s generates spurious rests). https://github.com/DrumScript/DrumScript/issues/274
>

---
>
> ## **Released**
*[back](#changelog)*

### **[0.2.0] - August 2026**
>

> **First minor-version bump**
> 
> Signals the start of the breaking-change track for --full flag (replaced by --verbose) ahead of v1.0.0 beta.-->
>
> ### *Additions*
>
* Versioned documentation deployment via `docs.yml` GitHub Actions workflow (`docs/versioned-deploy` branch):
  - Documentation now deploys to version-specific folders on `gh-pages` (e.g. `/v0.1.6/`, `/v0.2.0/`)
  - Tag pushes (`v*`) deploy to both `/<tag>/` and `/latest/` folders
  - Main branch pushes deploy to `/dev/` folder (bleeding-edge docs)
  - Root `index.html` auto-generated on tag push, redirects to `/latest/`
  - `keep_files: true` ensures older version folders are never deleted
  - Existing root-level docs remain untouched until explicit cleanup
  - Contributor and Developer updated guidance (#283, #132, #291)
* Added version drop down to shibuya documentation (#183, #281)
* Added [repo-stats.yml](.github/workflows/repo-stats.yml) GitHub Actions workflow: daily (23:00 UTC) collection of repository traffic statistics (views, clones, stars, forks, referrers, popular paths) via [github-repo-stats](https://github.com/jgehrcke/github-repo-stats). Data persisted to `github-repo-stats` branch. Overcomes GitHub's 14-day traffic data retention limit and tracks usage
* Added `Traffic` section to [README](./README.md#traffic) with links to daily-updated repository statistics report (PDF and HTML), generated by `repo-stats.yml` via [github-repo-stats](https://github.com/jgehrcke/github-repo-stats)
* Added CHANGELOG reference to README table of contents (Sphinx docs already linked via symlink)
* `_TranscribeResult` deprecation shim class in `drumscript/__init__.py`: dict subclass with `__str__` and `__fspath__` methods that emit `DeprecationWarning` when the return value of `transcribe()` is used as a string. Provides smooth migration path from v0.1.x string return to v1.0.0 dict return.
* Added `scripts/verify_release.sh` — 56-check release verification script covering every documented CLI command and public API function, run in a clean temporary directory to catch environment assumptions (e.g. the missing-`outputs/` bug)
* Added `scripts/close_issues_v020.sh` — batch `gh issue close` script (with per-issue comments) for the GitHub issues resolved in v0.2.0
* Added timeout to jobs block in `tests.yml` and add `--no-install-recommend` to linux system dependencies job to prevent `apt-get` issues in workflow
>
> ### *Changes*
>
* Updated table ordering in `docs/index.md` to match right sidebar ordering and added missing sidebar navigation point for tempogram-detection
* Amended documentation to remove bold markdown formatting for H1 references feeding into the side-nav bar visual presentation, for all except `DrumScript CLI Reference`; fixed ordering side in toctree (docs/index.md) for `User Guide` submenu to 1. remove duplicated `usage` reference in toctree and 2. reorder items alphabetically. Amended right hand navbar so that H2 links are now alphabetical.
* Updated and tidied the examples for extract stems in README.md; split example up into extract stems and backing track function examples. (#85)
* Standardised git tag naming convention from `drumscript__vX.Y.Z-alpha` to `vX.Y.Z` (e.g. `v0.1.6`). Old tags remain on remote (branch protection prevents deletion) but are ignored by the `docs.yml` workflow which only triggers on `v*`.
* `transcribe()` non-verbose return type changed from `str` to `_TranscribeResult` (a `dict` subclass). The return value is a dict with `pdf_path`, `json_path`, and `midi_path` keys. For backwards compatibility, using the result as a string still works (returns the PDF path) but emits a `DeprecationWarning` directing users to use `result['pdf_path']` instead. String behaviour will be removed in v1.0.0.
* Updated `tests/unit/test_transcribe.py` to reflect `_TranscribeResult` return type: replaced string assertions with dict key checks, added tests for deprecation warning on string usage, added test for verbose dict including `json_path` and `midi_path`
* Updated `README.md` Quick Start examples to use new dict-based `transcribe()` return with deprecation note
* Updated `docs/guide/usage.md` section 6 with new `transcribe()` return type examples; filled in previously empty Extract Backing Track and Extract Drum-Only Audio sections
* Added repository statistics link to `docs/index.md` homepage
* Consolidated `twine` into the `dev` optional-dependency group in `pyproject.toml`; removed the now-redundant `[dependency-groups]` section
* Excluded markdown from ruff via `extend-exclude = ["*.md"]` in `pyproject.toml`. ruff >=0.16 formats Python code blocks inside `.md` files by default, which reflows deliberate one-liner snippets (e.g. `import platform; print(...)`) and collapses readable multi-line examples. No-op on the currently locked ruff 0.15.22; prevents CI breaking on a future `uv lock --upgrade`
* `drumscript/main.py` console entry point fixed: `[project.scripts]` repointed from `drumscript.main:main` to `drumscript.main:cli`. The generated console wrapper calls its target with no arguments, but `main()` requires `input_audio_path`, so `drumscript ...` raised `TypeError` on every invocation since the first PyPI release (v0.1.3). `build_parser()` and `cli()` extracted to module level; `main()` itself unchanged. (#176)
* `docs/guide/cli_reference.md` audited: added the missing `--rudiment` flag, corrected the primary entry point from `python drumscript/main.py` to the `drumscript` console command, corrected the onset_detector standalone usage note, and expanded the worked examples from 3 to 6. (#107)
* `docs/guide/usage.md`, `docs/guide/glossary.md`, `docs/guide/configuration.md` and `docs/guide/installation.md` audited and corrected: removed references to a non-existent `StemSplitter` class, `ds.AudioLoader`, `ds.main` / `python -m ds.main`, a `threshold` parameter on `detect_onsets()`, and underscore time-signature syntax; `configuration.md` rewritten to document the real configurable constants; `uv sync --all-groups` corrected to `--all-extras`. Superseded blocks commented out rather than deleted, per project convention. (#7)
* updated `transcribe.py` and `extract_stems.py` notebooks/runbooks, as well as audited the Colab notebook https://colab.research.google.com/drive/15yBGu6WURPyiH-sEQ82g_2T2wKqiIPsq#scrollTo=qpnuXCSle5V0
>
> ### *Fixes*
>
* Adjusted documentation so that when version appears in documentation it is no longer hardcoded, but linked to `import importlib.metadata` in `drumscript/__init__.py` [Reduces maintenance burden on contributors]
* Updated version in pyproject.toml from `v0.1.5` to `v0.1.6` (This should have been changed *prior* to pypi release of v0.1.6 on Thursday 18 June 2026)
* Fixed `create_backing_track` runbook; replaced and tidied functions in drumscript_interactive_notebook on Colab
* `ds.transcribe()` non-verbose return now exposes all output paths (PDF, JSON, MIDI) instead of only the PDF path. Previously, `score_builder.build_score()` silently wrote JSON and MIDI files but `transcribe()` only returned the PDF path — users had no way of knowing the other files existed
* Investigated `drumscript/main.py` (~line 26) `.wav` comment: comment was misleading — referred to stem output format, not input format. Clarified to reflect actual behaviour
* `ds.transcribe()` now reports only the output files that were actually written. `score_builder.build_score()` exports JSON, PDF and MIDI in three independent `try`/`except` blocks, so a failure in one does not stop the others — but it returned `None`, giving callers no way to tell which succeeded. `transcribe()` therefore advertised all three paths unconditionally, including files never written to disk. `build_score()` now returns a dict of the paths it successfully wrote, and `transcribe()` reports that; a non-dict return (older `build_score`, or a test double) falls back to the computed paths so existing callers are unaffected
* `release.yml` version-bump `sed` anchored to leading whitespace. The previous pattern matched any line containing `__version__ = "X.Y.Z"`, so it rewrote the commented-out historical line alongside the live fallback in `drumscript/__init__.py`, destroying the record of the previous version on every release. Also tightened `[0-9]*` to `[0-9]\+` so it cannot match an empty version string
* CLI stem flags (`--drumless`, `--all-stems`, `--mute`) now work on the happy path. `separate_audio()` was only ever called from inside the `except` handler in `drumscript/main.py`, so `drumscript song.mp3 --drumless` ran the transcription pipeline, succeeded, and exited without producing a backing track — silently, with no error. Stem handling moved into the primary `try` block: full separation for stem flags, the cheaper `extract_drum_stem()` for `--full-song` alone, and both combined when transcription follows separation. The Python API (`ds.extract_stems()`) was never affected
* Removed the unreachable second `except Exception` clause in `drumscript/main.py`. The handler above it already caught `Exception`, so it could never run; the duplicated pipeline that lived inside the first handler also propagated exceptions uncaught, since a sibling `except` cannot catch them. Both blocks commented out rather than deleted, per project convention
* `build_score()` now creates the output directory before exporting. `midi_exporter` and `xml_exporter` each created it themselves, but the JSON write and `pdf_exporter` did not — so running the CLI from any directory without an `outputs/` folder (e.g. a pip-installed user working outside the repo root) silently produced a MIDI file and nothing else, with only warning prints and no failure exit code. Creating it centrally in `build_score()` fixes every caller, CLI and Python API alike. Caught by the new integration tests, which run in a clean temporary directory
* amended `ds.AudioLoader` references in `docs/guide/usage.md` and fixed to reflect correct version `ds.load_audio`
* `git-lfs` install instructions added to the `README.md` System Dependencies section — previously undocumented, which left first-time contributors with confusing Git LFS pointer files instead of the example audio. (#272)
* Confirmed `onset_detector.py` standalone mode takes a user-supplied audio path (`python -m drumscript.audio_processor.onset_detector <audio_file>`) rather than hardcoded test paths, and documented it in `cli_reference.md`. (#102)
>
> ### *Tests*
>
* Did full audit of all `drumscript` code to ensure `full-flag` / `full_flag` consistency throughout, following v0.1.6 release fix replacing `full=True` with `verbose=True` (`DeprecationShim`)
* Fixed Sphinx build errors for documentation
* Amended structure of index in [README.md](README.md) and added missing H2 headers
* Investigated `main.py` `.wav` comment and input/output format behaviour: confirmed `load_audio()` supports any format librosa can decode (wav, mp3, flac, ogg); ffmpeg only required for MP3 input decoding and MP3 stem output
* Added 4 tests to `tests/unit/test_transcribe.py` (16 → 20) covering written-path reporting: failed export omits its path, all-success reports all three, `None` return falls back to computed paths, verbose dict reflects the same
* Added `tests/integration/test_transcribe_real.py` (15 tests) with real end-to-end coverage, nothing mocked. Fast tier (12 tests, drum-only audio, no Demucs) verifies `transcribe()` writes PDF/JSON/MIDI to disk, the JSON parses, the `_TranscribeResult` deprecation shim and `__fspath__` work, and `build_score()` reports only files that exist — marked `integration` but not `slow`, so it runs in CI under `pytest -m "not slow"`. Slow tier (3 tests, requires Demucs) covers the CLI stem flags including `--drumless` producing a backing track without a score

>
### **[0.1.6] - June 2026**
>
> **`v0.1.6` is the final v0.1.*x* release.** 
> After this, the next release jumps to v0.2.0 to signal the deprecation shim for the `full` → `verbose` removal.
>
#### *Additions*
- Deprecation shim for `full` parameter on the Python API:
  - New `verbose` parameter added to `transcribe()`, `extract_stems()`, and `detect_tempo()` as the canonical replacement for `full`
  - Passing `full=True` (or `full=False`) continues to work but emits a `DeprecationWarning` directing users to `verbose`
  - Warning explicitly names the v1.0.0 (beta) removal target so users have a clear migration timeline
  - Passing both `full` and `verbose` together raises `TypeError` (ambiguous, almost certainly a bug)
  - Internal helper `_resolve_verbose_flag()` centralises the resolution logic so it cannot drift between wrappers
  - Docstrings updated to mark `verbose` as primary and `full` as deprecated
- **PR #273 by [@nanaoto](https://github.com/nanaoto)** — IDMT-SMT-Drums V2 benchmark runner with `mir_eval` scaffolding:
  - `benchmarks/run.py` entrypoint with dataset adapter dispatch, evaluation loop, CSV/JSON archive with git commit tracking
  - `drumscript/datasets/` package: `BenchmarkItem` dataclass and IDMT adapter (XML/SVL annotation parsing)
  - `benchmarks/README.md` documenting conventions, dataset setup, and planned dataset coverage
  - Unit tests for benchmark runner (`test_benchmarks_run.py`) and IDMT dataset adapter (`test_idmt_dataset.py`)
  - `mir_eval` added as a dev dependency
- New unit test file `tests/unit/test_deprecation_warnings.py` (13 tests)
- New unit test file `tests/unit/test_cli_args.py` (4 tests)
>
#### *Fixes*
- Commented-out dead code removed from `drumscript/__init__.py` and `drumscript/main.py`
- Flag inconsistency between `drumscript/main.py` and `drumscript/__init__.py` resolved: `argparse` in main block updated so the CLI flag is now `--full-song` (hyphenated, consistent with `--all-stems`). Auto-converts to `args.full_song` matching the Python API parameter name.
>
### **[0.1.5] - 25 May 2026**
>
#### *Fixes*
- Emergency fix: transcription outputs
- Updated docstrings to clarify expected input for transcription functions
>
### **[0.1.4] - 20 May 2026**
>
> **First PyPI publication**
>
**First release**
#### *Initial public alpha release to PyPI*
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
>
<!--### Notes

- Alpha period: 01 June – 31 August 2026
- Beta target: v1.0.0
- TISMIR Educational Articles paper planned for beta release-->
>
---


<!--END-->