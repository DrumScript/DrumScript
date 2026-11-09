## `DrumScript` Python Package Structure

<!--date_created: weds-25-oct-2025-->
<!--date_edited: tues-03-nov-2026-->

```markdown
DrumScript/                          # Project root
├── .github/                         # GitActions files
│   ├── workflows/
│   │   ├── docs.yml                 # Handles publishing of `DrumScript` documentation to GitHub Pages
│   │   ├── publish.yml              # Handles publishing of the package to PyPi automatically
│   │   ├── pull_requests.yml        # Runs ruff and the test suite on every pull request
│   │   ├── release.yml              # Manual dispatch from GitHub Actions UI (Actions → "Create Release" → Run workflow). Enter the version number, release type (Alpha/Beta/Stable), and an optional summary.
│   │   ├── repo-stats.yml           # Daily (23:00 UTC) collection of repository traffic stats via [`jgehrcke/github-repo-stats`]|(https://github.com/jgehrcke/github-repo-stats). Data persisted to `DrumScript/github-repo-stats` branch. Not connected with source code to prevent bloat.
│   │   ├── test_build.yml           # Tests whether the package is ready to be rebuilt and pushed to PyPi
│   │   └── tests.yml                # Handles tests on development branch and main to ensure they dont break when PR is merged
│   ├── CODEOWNERS
│   ├── ISSUE_TEMPLATE/              # Issue forms (`.yml`, not `.md`) so reports arrive structured
│   │   ├── bug_report.yml
│   │   ├── config.yml
│   │   ├── feature_request.yml
│   │   └── submit_results.yml       # For users submitting `.pdf`/`.mid` transcription outputs
│   └── PULL_REQUEST_TEMPLATE.md
│
├── benchmarks/                      # Evaluation runners for scoring DrumScript against ADT datasets (added v0.1.6, PR #273 by @nanaoto)
│   ├── README.md                    # Dataset setup, conventions, and usage docs
│   ├── run.py                       # CLI entrypoint: dispatches to dataset adapters, runs mir_eval scoring, archives results
│   └── tree_benchmarks.txt          # Tree diagram for the benchmarks folder
│
├── drumscript/                      # <--- Main Source Package Directory
│   ├── __init__.py                  # Exposes the package. Public API wrappers (transcribe, extract_stems, detect_tempo, export_midi)
│   ├── main.py                      # Main entry point for the application's full pipeline. Holds `build_parser()` and `cli()`
│   ├── audio_processor/             # Handles audio loading, Digital Signal Processing (DSP), and stem-splitting (ie audio extraction).
│   │   ├── __init__.py
│   │   ├── audio_loader.py          # Loads and normalises audio files.
│   │   ├── feature_extractor.py     # Extracts Digital Signal Processing (DSP) features (spectral centroid, etc.).
│   │   ├── onset_detector.py        # Detects drum hit timestamps.
│   │   ├── stem_splitter.py         # Splits audio into 4 stems using Demucs (invoked as a CLI subprocess, not imported).
│   │   ├── tempo_detector.py        # "Voting System" algorithm for tempo estimation.
│   │   └── tempogram.py             # Visualization tool for analysing tempo.
│   │
│   ├── datasets/                    # Benchmark dataset adapters (added v0.1.6, PR #273 by @nanaoto)
│   │   ├── __init__.py              # BenchmarkItem dataclass
│   │   ├── base.py                  # Shared base for dataset adapters
│   │   ├── enst.py                  # ENST-Drums full-kit adapter
│   │   ├── idmt.py                  # IDMT-SMT-Drums V2 adapter: file discovery, XML/SVL annotation parsing
│   │   └── mdb.py                   # MDB-Drums full-kit adapter
│   │
│   ├── drum_classifier/             # Rule-based DSP classification engine.
│   │    ├── __init__.py
│   │    └── classify.py             # The core rule engine for deterministically classifying drum audio using `constants.py`
│   │
│   ├── notation_generator/          # Generates musical notation (`.json`), (`.midi`) and sheet music (`.pdf`) from audio provided.
│   │   ├── __init__.py
│   │   ├── constants.py             # Single-source of truth for constants such as `SAMPLE_RATE`, `N_FFT` used globally through `DrumScript`
│   │   ├── helpers.py               # Shared notation helpers (quantisation, note grouping)
│   │   ├── score_builder.py         # Decides which outputs are written (`.json`, `.pdf`, `.mid`); honours `midi_only`
│   │   ├── pdf_exporter.py
│   │   ├── midi_exporter.py
│   │   └── xml_exporter.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── ffmpeg_installer.py
│       └── research/                # A set of utility scripts very useful for testing the deterministic parameters on richer drum sample data. Excluded from binaries
│           ├── __init__.py
│           ├── analyze_closed_hat_physics.py
│           ├── analyze_crash_physics.py
│           ├── analyze_enst_dataset.py      # ENST-Drums stage attribution, confusion reporting, feature distributions
│           ├── analyze_high_tom_physics.py
│           ├── analyze_idmt_dataset.py      # IDMT diagnostics: `--diagnose-kick`, `--sweep-csv`, `--top`
│           ├── analyze_kick_physics.py
│           ├── analyze_low_tom_physics.py
│           ├── analyze_mdb_dataset.py       # MDB-Drums full-kit diagnostics
│           ├── analyze_mid_tom_physics.py
│           ├── analyze_open_hat_physics.py
│           ├── analyze_ride_physics.py
│           ├── analyze_snare_physics.py
│           ├── analyze_tom_physics.py
│           ├── get_event_frequencies.py
│           ├── measure_hat_frequency.py
│           ├── measure_kick_frequency.py
│           └── measure_snare_frequency.py
│
├── docs/                            # Sphinx documentation for users, developers and contributors
│   ├── _static/                     # Images and assets served with the docs site
│   ├── _templates/
│   ├── development/                 # Contributor guidance, testing guidance, documentation guidance
│   ├── generated/                   # Autodoc API stubs (generated, not hand-edited)
│   ├── guide/                       # Usage, CLI reference, roadmap, interactive notebooks
│   ├── release_notes/               # One page per published version, plus `_template.md` and `index.md`
│   └── theory/                      # Drum notation theory and reference material
│
├── scripts/                         # Developer helper scripts (not shipped in the package)
│   ├── backup.sh                    # Archives `drumscript/` and the full-review bundle into `.archive/`
│   ├── collect_code.sh              # Regenerates `drumscript_full_review.txt`, a single-file view of the source
│   ├── pypi.sh                      # PyPi publishing helper (gitignored)
│   └── run_tests.sh                 # Runs the suite with per-file logging to `scripts/logs/tests/<timestamp>/`
│
├── tests/
│   ├── README.md                    # Testing README.md
│   ├── conftest.py                  # Shared fixtures (auto-discovered)
│   ├── tree_tests.txt               # Tree diagram for the tests folder
│   ├── unit/                        # Unit tests for `DrumScript`
│   ├── integration/                 # E2E integration tests for `DrumScript`
│   └── regression/                  # Before/after transcription comparison harness (added v0.3.0)
│       ├── README.md
│       ├── songs.example.json       # Committed template; the working `songs.json` is gitignored
│       └── test_regression.py       # Both a pytest module and a CLI with `run`, `compare`, `verify`
│
├── .gitignore                       # Specifies intentionally untracked files.
├── CHANGELOG.md
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE                          # Apache 2.0
├── MANIFEST.in                      # Prunes tests/docs/datasets from the source distribution
├── README.md                        # Project overview and main documentation.
├── SECURITY.md
├── repository_structure.md
├── tree.txt                         # Tree diagram (generated using `homebrew tree`)
├── pyproject.toml                   # Project metadata and dependencies (managed by `uv`). Also sets `pytest.ini` config
└── uv.lock                          # Pinned versions of all dependencies.
```

---
<!--END-->
