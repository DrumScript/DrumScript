
## `DrumScript` Python Package Structure

<!--date_created: weds-25-oct-2025?-->
<!--date_edited: mon-08-dec-2025 -->


> **PLEASE NOTE (Oct-2025 Update):** This repository structure has been updated to reflect the project's pivot to a non-ML, classification-based approach. Legacy machine learning modules have been archived.

```text
DrumScript/                          # Project root
├── .gitignore                       # Specifies intentionally untracked files.
├── LICENSE                          # MIT License.
├── README.md                        # Project overview and main documentation.
├── pyproject.toml                   # Project metadata and dependencies (managed by `uv`).
├── uv.lock                          # Pinned versions of all dependencies.
├── repository_structure.md          # This file.
│
├── drumscript/                      # <--- Main Source Package Directory
│   ├── __init__.py                  # Exposes the package.
│   ├── main.py                      # Main entry point for the application's full pipeline.
│   │
│   ├── audio_processor/             # Handles audio loading, Digital Signal Processing (DSP), and stem splitting.
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
│   │    ├── predict.py              # The core rule engine for classifying drum hits.
│   │    └── ...
│   │
│   ├── notation_generator/          # *[FORTHCOMING]* Generates musical notation (.json) and sheet music (.pdf).
│   │   ├── __init__.py
│   │   ├── constants.py             # Defines musical constants (MIDI mapping, frequencies).
│   │
│   └── utils/                       # Utility functions.
│       ├── config.py                # Global configuration.
│       └── ffmpeg_installer.py      # Helper to ensure ffmpeg is present.

│
├── developer_docs/                  # Documentation for contributors.
├── local_tests/                     # Local test scripts (e.g., interface testing).
├── outputs/                         # Default directory for generated files (Ignored by Git).
├── test_audio/                      # Audio files used for testing.
└── theory/                          # Reference material on music theory and DSP.## `DrumScript` Python Package Structure

> **PLEASE NOTE:** This repository structure reflects the project's pivot to a non-ML, classification-based approach. Legacy machine learning modules are archived.

---

### **Modular Descriptions**

#### `audio_processor/`

This module handles all the raw audio manipulation. It is responsible for loading an audio file, detecting the precise timestamps of drum hits (onsets), and extracting a set of descriptive acoustic features (like spectral centroid, zero-crossing rate, etc.) for each hit. Its output is the foundational data used for classification.

#### `notation_generator/`

This module converts the list of classified drum events from `drum_classifier/` into a visual score. The `score_builder.py` script maps each event to its correct notehead and position on a drum staff, and the `pdf_exporter.py` script renders this information into the final `.pdf` and `.xml` sheet music files.

#### `main.py` (*The Orchestrator*)

This script serves as the main entry point to run the entire transcription pipeline with a single command. It orchestrates the process:

1.  Loads audio (`audio_processor`).
2.  Detects onsets and extracts features (`audio_processor`).
3.  Classifies each drum hit using the rule-based engine (`drum_classifier`).
4.  Generates the final sheet music from the classified hits (`notation_generator`).


--- 
<!--END-->