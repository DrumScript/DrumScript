## `DrumScript` Python Package Structure

<!--date_created: weds-25-oct-2025-->
<!--date_edited: wwds-12-august-2026--->

```markdown
DrumScript/                          # Project root
├── .github/                         # GitActions files
│   ├── workflows/
│   │   ├── build_test.yml           # Tests whether the package is ready to be rebuilt and pushed to PyPi
│   │   ├── docs.yml                 # Handles publishing of `DrumScript` documentation to GitHub Pages
│   │   ├── publish.yml              # Handles publishing of the package to PyPi automatically
│   │   ├── release.yml              # Manual dispatch from GitHub Actions UI (Actions → "Create Release" → Run workflow). Enter the version number, release type (Alpha/Beta/Stable), and an optional summary.
│   │   ├── repo-stats.yml           # Daily (23:00 UTC) collection of repository traffic stats via [`jgehrcke/github-repo-stats`]|(https://github.com/jgehrcke/github-repo-stats). Data persisted to `DrumScript/github-repo-stats` branch. Not connected with source code to prevent bloat.
│   │   └── tests.yml                # Handles tests on development branch and main to ensure they dont break when PR is merged
│   ├── CODEOWNERS
│   ├── ISSUE_TEMPLATE
│   │   ├── bug_report.md
│   │   └── feature_request.md
│   └── PULL_REQUEST_TEMPLATE.md
│
├── benchmarks/                      # Evaluation runners for scoring DrumScript against ADT datasets (added v0.1.6, PR #273 by @nanaoto)
│   ├── README.md                    # Dataset setup, conventions, and usage docs
│   └── run.py                       # CLI entrypoint: dispatches to dataset adapters, runs mir_eval scoring, archives results
│
├── drumscript/                      # <--- Main Source Package Directory
│   ├── __init__.py                  # Exposes the package. Public API wrappers (transcribe, extract_stems, detect_tempo)
│   ├── main.py                      # Main entry point for the application's full pipeline.
│   ├── audio_processor/             # Handles audio loading, Digital Signal Processing (DSP), and stem-splitting (ie audio extraction).
│   │   ├── __init__.py
│   │   ├── audio_loader.py          # Loads and normalises audio files.
│   │   ├── feature_extractor.py     # Extracts Digital Signal Processing (DSP) features (spectral centroid, etc.).
│   │   ├── onset_detector.py        # Detects drum hit timestamps.
│   │   ├── stem_splitter.py         # Splits audio into 4 stems using Demucs.
│   │   ├── tempo_detector.py        # "Voting System" algorithm for tempo estimation.
│   │   └── tempogram.py             # Visualization tool for analysing tempo.
│   │
│   ├── datasets/                    # Benchmark dataset adapters (added v0.1.6, PR #273 by @nanaoto)
│   │   ├── __init__.py              # BenchmarkItem dataclass
│   │   ├── base.py                  # Shared base for dataset adapters
│   │   └── idmt.py                  # IDMT-SMT-Drums V2 adapter: file discovery, XML/SVL annotation parsing
│   │
│   ├── drum_classifier/             # Rule-based DSP classification engine.
│   │    ├── __init__.py
│   │    └── classify.py             # The core rule engine for deterministically classifying drum audio using `constants.py`
│   │
│   ├── notation_generator/          # Generates musical notation (`.json`), (`.midi`) and sheet music (`.pdf`) from audio provided.
│   │   ├── __init__.py
│   │   ├── constants.py             # Single-source of truth for constants such as `SAMPLE_RATE`, `N_FFT` used globally through `DrumScript`
│   │   ├── score_builder.py
│   │   ├── pdf_exporter.py
│   │   ├── midi_exporter.py
│   │   └── xml_exporter.py
│   └── utils
│       ├── __init__.py
│       ├── config.py
│       ├── ffmpeg_installer.py
│       └── research                 # A set of utility scripts very useful for testing the deterministic parameters on richer drum sample data. Excluded from binaries
│           ├── __init__.py
│           ├── analyze_closed_hat_physics.py
│           ├── analyze_crash_physics.py
│           ├── analyze_high_tom_physics.py
│           ├── analyze_kick_physics.py
│           ├── analyze_low_tom_physics.py
│           ├── analyze_mid_tom_physics.py
│           ├── analyze_open_hat_physics.py
│           ├── analyze_ride_physics.py
│           ├── analyze_snare_physics.py
│           ├── analyze_tom_physics.py
│           ├── get_event_frequencies.py
│           ├── measure_hat_frequency.py
│           ├── measure_kick_frequency.py
│           └── measure_snare_frequency.py
├── docs/                            # Documentation for developers and contributors, as well as the `_build` artifacts for the `DrumScript` 
└── tests/
    ├── __init__.py
    ├── README.md                    # Testing README.md
    ├── conftest.py                  # Shared fixtures (auto-discovered)
    ├── fixtures/
    ├── unit/                        # Unit tests for `DrumScript`
    └── integration/                 # E2E integration tests for `DrumScript`
├── .gitignore                       # Specifies intentionally untracked files.
├── LICENSE                          # Apache 2.0
├── MANIFEST.in                      
├── README.md                        # Project overview and main documentation.
├── CHANGELOG.md                    
├── CODE_OF_CONDUCT.md
├── CONTRIBUTING.md
├── LICENSE
├── MANIFEST.in
├── README.md
├── SECURITY.md
├── repository_structure.md          
├── tree.txt                         # Tree diagram (generated using `homebrew tree`)
├── pyproject.toml                   # Project metadata and dependencies (managed by `uv`). Also sets `pytest.ini` config
└── uv.lock                          # Pinned versions of all dependencies.
```

--- 
<!--END-->