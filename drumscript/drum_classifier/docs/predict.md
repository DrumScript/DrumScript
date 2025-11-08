### **Using `predict.py` to test the model**

The following documentation outlines how to use the `predict.py` script in the `.drum_classifier/` module to test the outputs of a trained model

<!--date_created:mon-14-jul-2025-->
<!--date_updated: mon-04-aug-2025-->

---
#### Using `predict.py` for model validation

This document outlines the purpose and usage of two key scripts in the `DrumScript` project: `predict.py` and `generate_score.py`.

#####  **`predict.py`**

* **Why/When to use it**: This script serves as your primary tool for **inference and model validation**. You use it after training a new model to test its performance on unseen audio data. It's the first step in the transcription pipeline for generating a structured output that can be used for further processing.
* **Where is the output stored?**: The script stores its output in a file named `prediction_output.json`. This file is located in the same directory as the script itself: `DrumScript/drum_classifier/`.
* **What event data is captured?**: The `prediction_output.json` file contains a detailed list of dictionaries, one for each detected drum event. Each dictionary captures the following information:
    * `drum_type` (e.g., "kick", "snare")
    * `onset_time_seconds` (time of the drum hit in the audio)
    * `midi_pitch` (MIDI note number for the drum)
    * `note_head_type` (e.g., "x" for cymbals, "normal" for drums)
    * `staff_position` (e.g., "F#3")
    * `display_name` (e.g., "Snare Drum")

#####  **`generate_score.py`**

* **Why/When to use it**: This script is used to **convert the data from `prediction_output.json` into musical notation files**. It's the next logical step after `predict.py` has successfully generated its output. You use this script to create the raw MIDI and MusicXML files that can then be used to generate a final PDF score.
* **Where are the outputs stored?**: This script creates a new, organized directory structure for its output. The generated `.mid` and `.xml` files are stored in: `DrumScript/outputs/drum_classifier/midi/`.
* **How to check if the `prediction_output.json` matches the audio?**: This is a qualitative process. You can't just run an automated check. To validate the model's performance:
    * **Listen to the MIDI**: Open the generated `.mid` file in a media player or a Digital Audio Workstation (DAW) to hear the transcribed drum pattern. Compare it to the original audio to see if the timing and drum types sound correct.
    * **View the Notation**: Open the generated `.xml` file in a music notation software like **MuseScore**. This will show you the visual sheet music. You can then compare the written score to the original audio to check for accuracy in note placement, drum types, and rhythm.

> To run `generate_score.py` navigate to `DrumScript.drum_classifier` directory:

```zsh
cd drum_classifier

```

> Then run


```zsh

python3 generate_score.py
```

**Outputs**

```zsh

Reading drum events from: ~DrumScript/drum_classifier/prediction_output.json
Successfully loaded 443 drum events.

Generating MIDI and MusicXML files...
✅ Successfully generated MIDI file: ~DrumScript/outputs/drum_classifier/midi/prediction_output.mid
✅ Successfully generated MusicXML file: ~DrumScript/outputs/drum_classifier/xml/prediction_output.xml
```

> The resultant `.xml` and `.MIDI` files will be stored in `DrumScript/outputs/drum_classifier/midi` and `DrumScript/outputs/drum_classifier/XML`

> **NOTE:** Please **do not** push these files to the repo. 
> **NOTE:** If these directories do not exist **they will be created when `generate_score.py` is run**




---

<!--END-->
