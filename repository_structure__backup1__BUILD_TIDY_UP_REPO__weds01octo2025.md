## `DrumScript`  Python Package Structure


##  **Repository Structure**

This document outlines the directory and file structure of the `DrumScript` project.

> **PLEASE NOTE (Aug-25 update):** This **repository structure/tree diagram etc** needs to be updated. 

```markdown
# Repository Structure



This document outlines the directory and file structure of the `DrumScript` project.


**DrumScript/                        # The main Python package, a package that takes drum audio and converts it into drum sheet music**
├── __init__.py                    # Makes 'DrumScript' a Python package
├── main.py                        # Main entry point for the application
├── .venv/                         # Python virtual environment (created by `uv venv`)
├── .gitignore                     # Specifies intentionally untracked files to ignore
├── .python-version                # Specifies which version of Python to use (`3.12.10`)
├── pyproject.toml                 # Project metadata and dependencies (managed by `uv`)
├── README.md                      # Project overview and main documentation
├── requirements.txt               # Direct dependencies (generated/used by `uv pip install -r`)
├── LICENSE                        # Project licensing information (e.g., MIT License)
├── repository_structure.md  
├── developer_docs/                # Documentation on how DrumScript works, as well as contributing, testing etc.
│   ├── code_of_conduct.md
│   ├── contributor_guidance.md
│   ├── glossary.md
│   ├── how_it_works.md
│   ├── testing_guidance.md
├── audio_processor/               # PYTHON MODULE: Handles audio loading, normalisation, onset detection, and feature extraction
│   │   ├── __init__.py
│   │   ├── audio_loader.py        # Loads and normalises audio files
│   │   ├── feature_extractor.py   # Extracts features for classification
│   │   ├── onset_detector.py      # Detects drum hit onsets
│   │   ├── tempo_detector.py      # Automatic tempo detection from audio data.
│   │   └── tempogram.py           # Visualising tempo using librosa's `tempogram` function
├── data_labeller/                 # [LEGACY] PYTHON MODULE: For building custom drum training data and datasets for ML-purposes
│   │   ├── __init__.py
│   │   ├── data_labeller.py        # Loads and normalises audio files
│   │   ├── data_labeler.md         # Detects drum hit onsets
│   │   ├── docs/                   # Associated documentation for `data_labeller/` module
├── drum_classifier/                # [SEPT-25 UPDATE: CLASSIFICATION APPROACH WITHOUT ML TO BE TRIED FIRST] PYTHON MODULE: Machine learning module for drum sound/audio classification (uses Deep Learning)
│   │   ├── __init__.py
│   │   ├── data_preparer.py       # [SEPT-25 UPDATE: CLASSIFICATION APPROACH WITHOUT ML TO BE TRIED FIRST] Prepares audio features into a dataset for training
│   │   ├── drum_model.py          # [SEPT-25 UPDATE: CLASSIFICATION APPROACH WITHOUT ML TO BE TRIED FIRST] Defines the drum classification model architecture (e.g., Convolutional Neural Network (CNN) using Tensorflow)
│   │   ├── generate_score.py      # Script for interpreting outputs (`prediction_output.json`) to see what resultant `.PDF` or `.XML` looks like, such as when the model is changed/updated/improved
│   │   └── model_trainer.py       # [SEPT-25 UPDATE: CLASSIFICATION APPROACH WITHOUT ML TO BE TRIED FIRST] Script for training, evaluating, and saving the drum classification model
│   │   └── predict.py             # [SEPT-25 UPDATE: CLASSIFICATION APPROACH WITHOUT ML TO BE TRIED FIRST] Script for testing the model outputs on single existing audio file
│   │   └── prediction_output.json # [SEPT-25 UPDATE: CLASSIFICATION APPROACH WITHOUT ML TO BE TRIED FIRST] Output of the `predict.py` script, `.json` file that **lists all events detected** and specifies, for each event:   `drum_type`, `onset_time_seconds`,`midi_pitch`,`note_head_type`: `x`,`staff_position`, `display_name`
│   │   ├── docs/                  # Associated documentation for `drum_classifier/` module
├── midi_percussion_map.csv        # A 'master' map that provides `midi_note`, `key/note`, `instrument_name`, `articulation`,`notation_style`,`staff_position`, `instrument_family`,`common_genre`
├── models/                        # [SEPT-25 UPDATE: CLASSIFICATION APPROACH WITHOUT ML TO BE TRIED FIRST] Outputs from CNN model learning used to generate/predict events in new audio
│   │   ├── multi_label_drum_classifier_model.h5     
│   │   ├── multi_label_label_map.json           
│   │   └── multi_label_scaler.joblib
│   │   └── docs/                  # Associated documentation for `model/` module
├── notation_generator/            # Generates musical notation and pdf sheet music
│   │   ├── __init__.py
│   │   ├── constants.py           # PYTHON MODULE: Defines the constants used to transcribe events to drum score, ie `staff_position` relative to base
│   │   ├── helpers.py            
│   │   └── pdf_exporter.py        # Script for converting drum mappings to pdf output
│   │   ├── score_builder.py       # Builds a score based on extracted features and predictive power of CNN machine learning model in `drum_classifier/`
├── outputs/                       # XML, Midi and PDF outputs, stored relative to the module origin
│   │   ├──drum_classifier/        # The subdirectories of `.outputs/drum_classifier/` are generated when the code is run.
│   │   ├──notation_generator/
├── training_data/                 # Folder for training data sets
│   │   ├──ENST/                   # The primary dataset used to train the model
│   │   ├──ENST_processed/         # A processed version of the ENST dataset. 
│   │   ├──process_ENST_dataset.py # A script that takes ENST/ data and processes it ready for use in ML
├── utils/                         # Utility functions (e.g., for file handling, configuration)
│   │   ├──__init__.py
│   │   ├──config.py               # Defines things like `QUANTIZATION_SUBDIVISION` and `PDF_PAGE_SIZE`
│   │   ├──ffmpeg_installer.py     # Utility script for installing `ffmpeg`                        
├── theory/                        # Some helpful theory on drums, percussion, and advanced audio signal processing.

```

> **NOTE:** 
> 1. Some elements of the script `.utils/config.py` could be moved to the `notation_generator/constants.py` file.
> 2. The `.training_data/ENST` and `.training_data/ENST_processed` folders can tend to get very large and so, these are **not** published on the repo. 


---
### **Modular Descriptions** (Requires update per Sept-25)

#### `audio_processor/`

This module handles all the raw audio manipulation and initial feature extraction.

<!--|Name|Purpose|
|-|-|
|**`audio_loader.py`**|Load audio files (`.wav`, `.mp3`, etc.).|
|**`onset_detector.py`**||
 **`feature_extractor.py`**||-->

* **`audio_loader.py`**:
    * **Purpose:** Load audio files (`.wav`, `.mp3`, etc.).
    * **Scientific Principle:** Digital audio files are sampled representations of analog sound waves. Loading involves reading these samples into a numerical array (e.g., NumPy array).
    * **Functions:**
        * `load_audio(file_path, sr=None)`: Loads audio, optionally resamples to a target sample rate (`sr`).
        * `normalise_audio(audio_data)`: Normalizes amplitude to a standard range (-1.0 to 1.0).
  * **`tempo_detector.py`**:
      * **Purpose:** Estimates the tempo of an audio file in beats per minute (BPM).
      * **Scientific Principle:** This is achieved by analyzing the **tempogram**, a representation of rhythmic patterns over time. The model identifies the most prominent rhythmic pulse in the audio.
      * **Functions:**
          * `estimate_tempo(audio_data, sr)`: Takes audio data and its sample rate to return a tempo value.
> 
  * **`tempogram.py`**:
      * **Purpose:** Generates a visual representation of the tempogram, which can be useful for debugging and analysis.
      * **Scientific Principle:** The script visualizes the rhythmic energy of the audio across different tempos, with higher intensity indicating a more prominent tempo at that point in time. It overlays the estimated tempo from `tempo_detector.py` on the graph.
      * **Functions:**
          * `visualise_tempogram(audio_data, sr)`: Creates a plot and saves it as an image file.
>
* **`onset_detector.py`**:
    * **Purpose:** Identify the precise time points where drum hits occur.
    * **Scientific Principle:** Onsets are characterized by rapid changes in spectral energy or amplitude over time (high spectral flux).
    * **Functions:**
        * `detect_onsets(audio_data, sr)`: Uses algorithms like `librosa.onset.onset_detect` (which might use spectral flux, peak picking, etc.) to return a list of onset times in seconds.
    * **Considerations:** Thresholding is critical. Too low, many false positives; too high, miss subtle hits (ghost notes).
>
* **`feature_extractor.py`**:
    * **Purpose:** Extract relevant features from audio segments around detected onsets that characterize drum sounds.
    * **Scientific Principle:** Timbre differences are encoded in the frequency content (spectrum) and the temporal evolution of the sound.
    * **Functions:**
        * `extract_features(audio_segment, sr)`: Takes a small audio segment (e.g., 200-500ms around an onset) and extracts features.
        * **Common Features (using `librosa`):**
            * **MFCCs (Mel-Frequency Cepstral Coefficients):** Excellent for timbre.
            * **Spectral Centroid:** Average frequency.
            * **Spectral Rolloff:** Skewness of the spectrum.
            * **Zero-Crossing Rate:** Roughness/noisiness.
            * **RMS Energy:** Loudness.
            * **Spectral Bandwidth:** Spread of frequencies.
            * **Pitch (for pitched elements like toms, or to *disregard* for unpitched ones):** While drums are unpitched, low-frequency content can indicate bass drum.
            * **Attack/Decay Characteristics:** Shape of the amplitude envelope.
>
#### `data_labeller/`
The `data_labeller/` module facilitates an **interactive labelling process**, which is the most effective way to accurately tag complex drum events like simultaneous hits or extremely fast patterns, like the `double-bass`.

**Here's a breakdown of the steps involved to this module:**

1.  **Import audio files:** It takes a list of your drum audio recordings (MP3, WAV, etc.) as input. 
>
2.  **Slice files:** It uses DrumScript's existing `onset_detector` to identify individual drum hit events. For very fast passages, I've adjusted parameters to allow for more sensitive detection.
>
3.  **Interactive playback & Labelling:** For *each* detected drum hit:
      * It plays a small audio segment of that specific event for you.
      * It prompts you to manually enter a label (e.g., `kick`, `snare`, `hi-hat`, `kick+snare`, `double_kick_right`, `double_kick_left`, etc.). This human input is vital for correctly identifying simultaneous drum hits or distinct, rapid events.
>
1.  **Feature extraction:** For each labelled event, it extracts relevant audio features:
      * **Frequency (in Hz):** Represented by the `spectral_centroid_mean_hz`, which gives you the average `center of mass` of the frequencies in the sound, providing a good indicator of its brightness or pitch.
      * MFCCs (Mel-frequency Cepstral Coefficients): Standard features for distinguishing different sounds.
      * RMS (Root Mean Square) energy: A measure of loudness.
>
4.  **Labelled output:** Once you've labelled all events in your files, the module saves the complete dataset in **two formats**:
    >
    * **JSON file (`labelled_drum_dataset.json`):** Contains all event details, including raw and processed features.
    >
    * **CSV file (`labelled_drum_dataset.csv`):** A flattened version of the data, suitable for direct use in machine learning model training.

> **Updated functionality:**
> 
> For each detected drum event, the `data_labeller` module will now:
>
> 1. **Extract the audio segment.**
>
> 2. **Save this segment** as a `.wav` file in a new `audio_segments/` sub-folder within your chosen output directory (e.g., `labelled_datasets/audio_segments/`). 
> 3. **Include the path to this saved audio segment** in both the `JSON` and `CSV` output files under the field ``saved_audio_segment_path``. 
> 
> **NOTE:** The filename will be descriptive, including the **original audio name**, **event number**, and **onset time** (e.g., `groove_1_event_3_onset_2.15s.wav`).
>
> These amendments allow for more **structured review** and **playback** on an **event-basis** post-script.

#### `drum_classifier/`

This is the *brain* of the package, identifying **which drum was hit**.

* **`data_preparer.py`**:
    * **Purpose:** Prepare a dataset for training the drum classifier.
    * **Functions:**
        * `build_dataset(audio_files, annotations_files)`: Takes raw drum audio (ideally isolated hits or labeled full tracks) and corresponding labels (e.g., *kick,* *snare,* *hi-hat*). Extracts features for each labeled hit and stores them.
        * `split_data(features, labels)`: Splits data into training, validation, and test sets.
    * **Challenge:** Creating a robust, labeled dataset is the hardest part.  might need to manually label some initial drum samples or use existing datasets (e.g., Open Drum Kit, ENST-Drums).
>
* **`drum_model.py`**:
    * **Purpose:** Define the machine learning model architecture.
    * **Scientific Principle:** Machine learning models learn complex patterns and relationships between input features (spectral data) and output classes (drum type).
    * **Classes/Functions:**
        * `DrumClassifierModel()`: A class to encapsulate the ML model.
            * **Deep Learning (TensorFlow/PyTorch):**
                * **CNN (Convolutional Neural Network):** Excellent for processing spectral images (spectrograms generated from features). Can learn hierarchical features directly from frequency-time representations.
                * **RNN/LSTM:** If  want to consider sequential context (e.g., hi-hat patterns).
                * **Transformer:** Emerging as powerful for sequential data like audio.
>
* **`model_trainer.py`**:
    * **Purpose:** Train and evaluate the drum classification model.
    * **Functions:**
        * `train_model(model, train_data, val_data, epochs, batch_size)`: Trains the `DrumClassifierModel`.
        * `evaluate_model(model, test_data)`: Evaluates performance (accuracy, precision, recall, F1-score per class).
        * `save_model(model, path)` / `load_model(path)`: For persistence.

#### `notation_generator/`

This module handles converting the identified drum events into a visual score.

* **`score_builder.py`**:
    * **Purpose:** Map detected and classified drum events to musical notation data.
    * **Scientific Principle:** Musical quantization (aligning events to a beat grid) and standard drum notation rules.
    * **Functions:**
        * `quantize_events(onset_times, tempo=120, subdivision=16)`: Takes raw onset times and snaps them to the nearest musical subdivision (e.g., 16th note). This is critical for readable sheet music. Requires tempo detection (or user input).
        * `map_to_drum_parts(classified_events)`: Converts classified drum hits (*kick*, *snare*) into standard drum notation elements (e.g., MIDI note numbers for notation software, or custom symbols).
        * `create_score_data(quantized_events)`: Assembles the raw data for the score (e.g., a list of `(time, drum_part, velocity)` tuples).
    * **Notation Mapping (Example):**
        * Kick: Lowest space/line
        * Snare: Middle space (often C or E)
        * Hi-Hat (closed): Top space (X-head)
        * Hi-Hat (open): Top space (X-head with circle)
        * Crash: Above top staff line
        * Ride: Top space (X-head)
        * Toms: Various spaces/lines
>
* **`pdf_exporter.py`**:
    * **Purpose:** Render the musical score data into a PDF.
    * **Libraries:**
        * `music21`: A powerful Python library for computer-aided musicology. Can represent musical objects and export to MusicXML, which can then be converted to PDF.
        * `LilyPond` (external): A powerful music engraving program. `music21` can often interface with it.
        * `PyPDF2` (for direct PDF manipulation if rendering manually, less common for complex scores).
        * `reportlab` (for drawing shapes, if  ant to draw the staff and notes manually, more complex).
    * **Functions:**
        * `generate_pdf(score_data, output_path)`: Takes the structured score data and generates a PDF. This will be the most visually challenging part.
    * **Considerations:** Staff lines, note heads, stems, flags, rests, clefs, time signatures, tempo markings, dynamic markings. `music21` simplifies this greatly.
>
#### `utils/`

> Helper and configuration functions

* **`config.py`**: Stores configuration parameters (e.g., default sample rate, model paths, feature extraction parameters).
* **`helpers.py`**: Small utility functions (e.g., `milliseconds_to_seconds`).
* **`constants.py`**: Defines constant values (e.g., drum instrument mappings to MIDI notes or custom IDs).

---

#### `main.py` (*`The Orchestrator`*)

<!--This script brings all the modules together.-->

 `main.py`serves as the **main entry point** or **orchestration script** for the entire `DrumScript` application. Specifically,  `main.py` is used for:

1.  **Orchestrating the full pipeline:** 
It brings together all the individual components of  `DrumScript`:

    - **Audio loading:** It loads the input drum audio file.
    - **Onset detection:** It detects when drum hits occur in the audio.
    - **Drum classification:** It loads previously trained drum classification model (from `drum_classifier.drum_model` and `model_trainer`), extracts features from the detected drum hits, and then classifies each hit (e.g., as a kick, snare, hi-hat).
    - **Notation generation:** It takes the classified drum events, quantizes them (ie. aligns them to a musical grid), and structures them into data suitable for sheet music.
    - **PDF generation:** Finally, it generates a PDF file of the drum sheet music.
    - **User Interface via Command Line:** It uses `argparse` to allow users **to specify the input audio file**, **the desired output PDF file path**, and (optionally) **the tempo**, directly from the **command line**.
>
In short, `main.py` **makes it easy** for someone to **run the entire conversion process** with a **single command**.

> `main.py` is the script  would run when you **want to convert a complete drum audio recording** into a drum **sheet music PD**F, utilising all the preceding steps (like data preparation and model training). It's the final piece that connects everything together for the end-user functionality.

> However, as the comments in `main.py` script point out, for `main.py` to work correctly,  **must first have a trained drum classification model** saved (using `model_trainer.py`)

---
<!--END--->