# **How it works**
<!--DrumScript-->

<!--date_created: tues-24-june-2025-->
<!--date_updated: thurs-11-dec-2025-->
**Description:** This document serves dual purpose:

1) It outlines the purpose of **specific modules** in `DrumScript`, object-wise.
2) It outlines key definitions to **clarify the methodology used**.

---
## `DrumScript`: How it works
### `audio_processor/`

**Module overview**

This module handles all raw audio manipulation. It is currently the most active part of the package, handling:

 - **Stem Splitting (`stem_splitter.py`):** Uses the **Demucs** source separation model (by [adefossez](https://github.com/adefossez/demucs)) to isolate drum frequencies from a full audio mix.
 - **Tempo Detection (`tempo_detector.py`):** Uses a deterministic "Voting System" to analyse the tempogram and determine the most likely BPM across the entire track.
 - **Onset Detection (`onset_detector.py`):** Finds where the **drum hits actually occur** (i.e., `onset_events`).
 - **Feature Extraction (`feature_extractor.py`):** Extracts **numerical features** (spectral centroid, bandwidth, zero-crossing rate) from these *events* for use in the classifier.

---

### `drum_classifier/`

**Module overview**

This module is the core logic engine of the package (currently in active R&D). It no longer involves training a model. Instead, it:

- Takes the numerical features for each drum hit from the `audio_processor/` module.
- Applies a pre-defined set of rules and thresholds (a deterministic classification system) to determine which drum was played.
- Outputs a structured list of all the classified drum events.

### `classify.py`

This script is the **Rule Engine**. It contains the core logic for the classification. Its main job is to take the acoustic features of a drum hit and make a decision. Specifically, `classify.py`:

- Loads the features extracted for every onset in an audio file.
- Runs these features through a series of conditional checks (e.g., "if the spectral centroid is below X and the energy is high, classify as a kick drum").
- Generates the final list of classified events (e.g., `prediction_output.json`), detailing what drum was hit and when.

### `generate_score.py`

This is a **Utility and Testing Script**. It's designed to quickly visualise the output of the classifier without running the entire application pipeline. Specifically, `generate_score.py`:

- Reads the list of classified events produced by `classify.py`.
- Uses the `notation_generator/` module to convert that list directly into a sheet music file (`.pdf`)
- Allows for rapid testing and debugging of the classification rules by providing immediate visual feedback on the transcription quality.


---
<!--END---> 