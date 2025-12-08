
## `DrumScript` Python Package Structure

<!--date_created: weds-25-oct-2025?-->
<!--date_edited: mon-08-dec-2025 -->


> **PLEASE NOTE (Oct-2025 Update):** This repository structure has been updated to reflect the project's pivot to a non-ML, classification-based approach. Legacy machine learning modules have been archived.

```markdown
DrumScript/                          # The main Python package that converts drum audio into sheet music.
├── .git/                            # Git version control directory.
├── .gitignore                       # Specifies intentionally untracked files to ignore.
├── README.md                        # Project overview and main documentation.
├── pyproject.toml                   # Project metadata and dependencies (managed by `uv`).
├── uv.lock                          # Pinned versions of all dependencies.
├── __init__.py                      # Makes 'DrumScript' a Python package.
├── repository_structure.md          # This file.
│
├── drumscript/                      # <--- Main Source Package Directory
│   ├── __init__.py                  # Makes 'drumscript' a Python package.
├── main.py                          # Main entry point for the application's full pipeline.
│   ├── audio_processor/                # PYTHON SUPBPACKAGE/MODULE:  Handles audio loading, onset detection, and feature extraction.
│   │   ├── __init__.py
│   │   ├── audio_loader.py              # Loads and normalises audio files.
│   │   ├── feature_extractor.py         # Extracts DSP features for classification.
│   │   ├── onset_detector.py            # Detects drum hit onsets.
│   │   ├── stem_splitter.py            # Splits audio into 4-stems, uses Demucs
│   │   ├── tempo_detector.py            # Detects tempo from audio data.
│   │   └── tempogram.py                 # Visualisation tool for analysing tempo.
│   │   
│   │── drum_classifier/               # *[FORTHCOMING]* PYTHON SUPBPACKAGE/MODULE:  Classifies drum sounds using a rule-based DSP approach.
│   │    ├── __init__.py
│   │    └── classify.py              # *[FORTHCOMING]* Forthcoming deterministic classification model for drum audio
│   │
│   ├── notation_generator/              # PYTHON SUPBPACKAGE/MODULE:  Generates musical notation (.xml) and sheet music (.pdf).
│   │   ├── __init__.py
│   │   ├── constants.py                 # Defines constants for score generation (e.g., staff positions).
│   │   ├── pdf_exporter.py              # [MIGHT REMOVE] Converts the generated score into a PDF file.
│   │   ├── score_exporter.py            # Converts the generated score into an XML/MIDI file.
│   │   └── score_builder.py             # Builds a musical score from the list of classified events.

│   │ 
│   └── utils/                           # PYTHON SUPBPACKAGE/MODULE: Utility functions and configuration.
│   │   ├── __init__.py
│   │   ├── config.py                    # Stores configuration parameters.
│   │   ├── measure_frequency.py         # Uses Librosa to measure frequency of drum part (kick drum used as example)
│       └── ffmpeg_installer.py          # Utility script for installing ffmpeg.

│
├── developer_docs/                  # Documentation for contributors and developers.
│   └── static/                      # Stores the documentation GitHub Pages site assets
│      ├── custom.css                # Style sheet for DrumScript documentation site
│      ├── conf.py
│      ├── index.md
│      ├── api.rst
│      └── ...                       # Other `.md` files related to documentation
│
├── local_tests/                     # A place for local tests
│   └── ...                          
├── machine-learning/                # [ARCHIVED] Legacy modules from the previous ML-based approach.
│   ├── data_labeller/               # [LEGACY] Module for building custom drum training datasets.
│   ├── models/                      # [LEGACY] Saved outputs from the trained CNN model.
│   └── training_data/               # [LEGACY] Folder for training datasets.
├── outputs/                         # Default directory for generated `.MP3/.WAV`, `.XML`, `MIDI`, and `.PDF` files. Not version-controlled.
├── test_audio/                      # Directory for sample audio files used for testing.
├── theory/                          # Reference material on music theory and audio signal processing.
└── training_data/                   # Archived data related to ML model training. Not version-controlled.

```

---

### **Modular Descriptions**

#### `audio_processor/`

This module handles all the raw audio manipulation. It is responsible for loading an audio file, detecting the precise timestamps of drum hits (onsets), and extracting a set of descriptive acoustic features (like spectral centroid, zero-crossing rate, etc.) for each hit. Its output is the foundational data used for classification.

#### `drum_classifier/`

This is the logic engine of the package. It takes the features extracted by the `audio_processor/` and applies a **rule-based classification system** to determine which drum was hit (e.g., "if the sound has a very low spectral centroid, classify it as a kick drum"). This approach replaces the previous deep learning model. The `predict.py` script contains this core logic, and its output is a structured list of classified drum events.

#### `machine-learning/`

This directory contains archived modules from the project's previous iteration, which was focused on transcription via a trained Machine Learning model. These are kept for reference but are not used in the current classification-based pipeline.

#### `notation_generator/`

This module converts the list of classified drum events from `drum_classifier/` into a visual score. The `score_builder.py` script maps each event to its correct notehead and position on a drum staff, and the `pdf_exporter.py` script renders this information into the final `.pdf` and `.xml` sheet music files.

#### `main.py` (*The Orchestrator*)

This script serves as the main entry point to run the entire transcription pipeline with a single command. It orchestrates the process:

1.  Loads audio (`audio_processor`).
2.  Detects onsets and extracts features (`audio_processor`).
3.  Classifies each drum hit using the rule-based engine (`drum_classifier`).
4.  Generates the final sheet music from the classified hits (`notation_generator`).