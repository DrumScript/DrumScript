
## `DrumScript` Python Package Structure

<!--date_edited: thurs-23-oct-2025-->

> **PLEASE NOTE (Oct-2025 Update):** This repository structure has been updated to reflect the project's pivot to a non-ML, classification-based approach. Legacy machine learning modules have been archived.

```markdown
DrumScript/                          # The main Python package that converts drum audio into sheet music.
├── .git/                            # Git version control directory.
├── .gitignore                       # Specifies intentionally untracked files to ignore.
├── .python-version                  # Specifies the Python version to use (e.g., 3.12.10).
├── README.md                        # Project overview and main documentation.
├── pyproject.toml                   # Project metadata and dependencies (managed by `uv`).
├── requirements.txt                 # Project dependencies.
├── uv.lock                          # Pinned versions of all dependencies.
├── __init__.py                      # Makes 'DrumScript' a Python package.
├── main.py                          # Main entry point for the application's full pipeline.
├── midi_percussion_map.csv          # Master map for MIDI note numbers, instrument names, and staff positions.
├── repository_structure.md          # This file.
│
├── audio_processor/                 # PYTHON MODULE: Handles audio loading, onset detection, and feature extraction.
│   ├── __init__.py
│   ├── audio_loader.py              # Loads and normalises audio files.
│   ├── feature_extractor.py         # Extracts DSP features for classification.
│   ├── onset_detector.py            # Detects drum hit onsets.
│   └── tempo_detector.py            # Detects tempo from audio data.
│
├── developer_docs/                  # Documentation for contributors and developers.
│   ├──
│   ├── onset_detector.py            # Detects drum hit onsets.
│   └── static/                      # Stores the documentation GitHub Pages site assets
│      ├── custom.css                # Style sheet for DrumScript documentation site
│      ├── ...
├── drum_classifier/                 # PYTHON MODULE: Classifies drum sounds using a rule-based DSP approach.
│   ├── __init__.py
│   ├── generate_score.py            # Script for interpreting classification outputs to generate a score.
│   ├── predict.py                   # Applies the classification rules to an audio file's features.
│   └── prediction_output.json       # Example output listing all detected and classified events.
│
├── machine-learning/                # [ARCHIVED] Legacy modules from the previous ML-based approach.
│   ├── data_labeller/               # [LEGACY] Module for building custom drum training datasets.
│   ├── models/                      # [LEGACY] Saved outputs from the trained CNN model.
│   └── training_data/               # [LEGACY] Folder for training datasets.
│
├── notation_generator/              # PYTHON MODULE: Generates musical notation (.xml) and sheet music (.pdf).
│   ├── __init__.py
│   ├── constants.py                 # Defines constants for score generation (e.g., staff positions).
│   ├── pdf_exporter.py              # Converts the generated score into a PDF file.
│   └── score_builder.py             # Builds a musical score from the list of classified events.
│
├── outputs/                         # Default directory for generated XML, MIDI, and PDF files.
├── test_audio/                      # Directory for sample audio files used for testing.
├── theory/                          # Reference material on music theory and audio signal processing.
└── utils/                           # Utility functions and configuration.
    ├── __init__.py
    ├── config.py                    # Stores configuration parameters.
    └── ffmpeg_installer.py          # Utility script for installing ffmpeg.
```

-----

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