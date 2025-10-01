# **`DrumScript`: How it works**


<!--date_created: tues-24-june-2025-->
<!--date_updated: weds-01-oct-2025-->
**Description:** This document serves dual purpose:

1) It outlines the purpose of **specific modules** in `DrumScript`, object-wise.
2) It outlines key definitions to **clarify the methodology used**.

---
## `DrumScript`: How it works
### `audio_processor/`

**Module overview**

 - Find where the **drum hits actually occur** (i.e., `onset_events`)
 - Extract **numerical features** from these *events*

---

### `drum_classifier/`

**Module overview**

This module is the core logic engine of the package. It no longer involves training a model. Instead, it:

- Takes the numerical features for each drum hit from the `audio_processor/` module.
- Applies a pre-defined set of rules and thresholds (a classification system) to determine which drum was played.
- Outputs a structured list of all the classified drum events.

### `predict.py`

This script is the **Rule Engine**. It contains the core logic for the classification. Its main job is to take the acoustic features of a drum hit and make a decision. Specifically, `predict.py`:

- Loads the features extracted for every onset in an audio file.
- Runs these features through a series of conditional checks (e.g., "if the spectral centroid is below X and the energy is high, classify as a kick drum").
- Generates the final list of classified events (e.g., `prediction_output.json`), detailing what drum was hit and when.

### `generate_score.py`

This is a **Utility and Testing Script**. It's designed to quickly visualize the output of the classifier without running the entire application pipeline. Specifically, `generate_score.py`:

- Reads the list of classified events produced by `predict.py`.
- Uses the `notation_generator/` module to convert that list directly into a sheet music file (`.pdf` or `.xml`).
- Allows for rapid testing and debugging of the classification rules by providing immediate visual feedback on the transcription quality.


---
<!--END---> 