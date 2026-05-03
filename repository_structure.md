
## `DrumScript` Python Package Structure

<!--date_created: weds-25-oct-2025-->
<!--date_edited: sun-03-apr-2026-->

```markdown
DrumScript/                          # Project root
├── drumscript/                      # <--- Main Source Package Directory
│   ├── __init__.py                  # Exposes the package.
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
│   ├── drum_classifier/             # Rule-based DSP classification engine.
│   │    ├── __init__.py
│   │    └── classify.py             # The core rule engine for deterministically classifying drum audio using `constants.py`
│   │
│   ├── notation_generator/          # Generates musical notation (`.json`), (`.midi`) and sheet music (`.pdf`) from audio provided.
│   │   ├── __init__.py
│   │   ├── score_builder.py
│   │   ├── pdf_exporter.py
│   │   ├── midi_exporter.py
│   │   ├── xml_exporter.py
│   │   └── constants.py             # Single-source of truth for constants such as `SAMPLE_RATE`, `N_FFT` used globally through `DrumScript`
│   └── utils/                       # Utility functions.
├── docs/                            # Documentation for developers and contributors, as well as the `_build` artifacts for the `DrumScript` 
│    ├── theory/                     # Reference documents (music theory, DSP, etc.). Sources provided
└── tests/
    ├── __init__.py
    ├── README.md                    # Testing README.md
    ├── conftest.py                  # Shared fixtures (auto-discovered)
    ├── fixtures/
    ├── unit/                        # Unit tests for `DrumScript`
    └── integration/                 # E2E integration tests for `DrumScript`
├── .gitignore                       # Specifies intentionally untracked files.
├── .github/                         # GitActions files
│   ├── workflows/
│   │   ├── build_test.yml           # Tests whether the package is ready to be rebuilt and pushed to PyPi
│   │   ├── docs.yml                 # Handles publishing of `DrumScript` documentation to GitHub Pages
│   │   ├── publish.yml              # Handles publishing of the package to PyPi automatically
│   │   └── tests.yml                # Handles tests on development branch and main to ensure they dont break when PR is merged
├── LICENSE                          # Apache
├── README.md                        # Project overview and main documentation.
├── repository_structure.md          # This file.
├── tree.txt                         # Tree diagram (generated using `homebrew tree`)
├── pyproject.toml                   # Project metadata and dependencies (managed by `uv`). Also sets pytest.ini config
└── uv.lock                          # Pinned versions of all dependencies.
```
> **PLEASE NOTE (Oct-2025 Update):** This repository structure has been updated to reflect the project's pivot to a non-ML, classification-based approach. Legacy machine learning modules have been archived.

---

<!--### **Modular Descriptions**

#### `audio_processor/`

This module handles all the raw audio manipulation. It is responsible for loading an audio file, detecting the precise timestamps of drum hits (onsets), and extracting a set of descriptive acoustic features (like spectral centroid, zero-crossing rate, etc.) for each hit. Its output is the foundational data used for classification.

#### `notation_generator/`

This module converts the list of classified drum events from `drum_classifier/` into a visual score. The `score_builder.py` script maps each event to its correct notehead and position on a drum staff, and the `pdf_exporter.py` script renders this information into the final `.pdf` and `.xml` sheet music files.

#### `main.py` (*The Orchestrator*)

This script serves as the main entry point to run the entire transcription pipeline with a single command. It orchestrates the process:

1.  Loads audio (`audio_processor`).
2.  Detects onsets and extracts features (`audio_processor`)
3.  Classifies each drum hit using the rule-based engine (`drum_classifier`).
4.  Generates the final sheet music from the classified hits (`notation_generator`).-->


--- 
<!--END-->