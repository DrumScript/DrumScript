# **Creating your own training dataset**
## `DrumScript/data_labeller/data_labeller.py`
>
The following documentation outlines how you can use the `data_labeller/` module to **import your own drum audio** and **create a labelled dataset** Use cases for this might be:
>
* **Testing** `DrumScript` **core functionality**
* Submitting a **pull request** to `DrumScript` moderators
* **Testing a known issue** with the `DrumScript` package
* **Submitting a feature request** to `DrumScript` `base_model`
* Create a **bespoke** **`DrumScript` model**, for your **own personal use**.
  
<!-- date_created: mon-07-jul-2025-->

<!-- date_updated: mon-07-jul-2025-->

---

### How it works

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
      * **Frequency (in Hz):** Represented by the `spectral_centroid_mean_hz`, which gives you the average "center of mass" of the frequencies in the sound, providing a good indicator of its brightness or pitch.
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
> 3. **Include the path to this saved audio segment** in both the `JSON` and `CSV` output files under the field `"saved_audio_segment_path"`. 
> 
> **NOTE:** The filename will be descriptive, including the **original audio name**, **event number**, and **onset time** (e.g., `groove_1_event_3_onset_2.15s.wav`).
>
> These amendments allow for more **structured review** and **playback** on an **event-basis** post-script.


<!---
---
### Setup and Running Instructions

1.  **Create the Module Directory:**

      * Navigate to your `DrumScript/` project root.
      * Create a new folder: `mkdir DrumScript/data_labeller`
      * Create an empty `__init__.py` file inside it: `touch DrumScript/data_labeller/__init__.py`
      * Place the code above into `DrumScript/data_labeller/data_labeller.py`.

2.  **Verify Imports:**

      * In the provided `data_labeller.py` code, ensure the import statements for `audio_loader`, `onset_detector`, and `feature_extractor` correctly reflect their location within your `DrumScript` package. I've used relative imports assuming they are correctly structured under `audio_processor`. If they are directly under `DrumScript`, adjust accordingly (e.g., `from .audio_loader import ...`). Based on your `repository_structure.md`, they should be `from DrumScript.audio_processor import ...`.

3.  **Install `sounddevice`:**

      * This library is crucial for playing the audio segments interactively.
      * Open your terminal in the `DrumScript` project root and run:
        ```bash
        uv pip install sounddevice
        ```
      * **Important for Audio Playback:** `sounddevice` relies on a system-level  library called **PortAudio**. You might need to install this separately:
          * **macOS:** `brew install portaudio` (if you have Homebrew)
          * **Ubuntu/Debian:** `sudo apt-get install libportaudio2`
          * **Windows:** PortAudio usually comes bundled with `sounddevice` wheels, or you might need to find specific installation instructions for your Python distribution.

4.  **Prepare Your Audio Files:**

      * Gather the MP3 or WAV files of your drum recordings that you want to label.
      * Update the `input_audio_paths` list in the `if __name__ == "__main__":` block of `data_labeller.py` with the actual paths to your files.

5.  **Run the Labeller:**

      * Open your terminal.
      * Navigate to your `DrumScript` project's root directory (the one containing `.venv`, `pyproject.toml`, etc.).
      * Execute the script using `uv run`:
        ```bash
        uv run python3 DrumScript/data_labeller/data_labeller.py
        ```

The script will then guide you through each drum event detected. Listen to the played segment carefully, and type in the appropriate label(s) (e.g., "kick", "snare+ride", "fast\_kick\_1", "fast\_kick\_2") and press Enter. Once finished, your `labelled_drum_dataset.json` and `labelled_drum_dataset.csv` files will be in the `labelled_datasets` folder.
-->

---
### Setup and running instructions
For each detected drum event, the module will now:

1.  **Extract the audio segment**.
2.  **Save this segment** as a `.wav` file in a new `audio_segments` sub-folder within your chosen output directory (e.g., `labelled_datasets/audio_segments/`). The filename will be descriptive, including the original audio name, event number, and onset time (e.g., `groove_1_event_3_onset_2.15s.wav`).
3.  **Include the path** to this saved audio segment in both the `JSON` and `CSV` output files under the field `"saved_audio_segment_path"`. This allows for easy post-review and playback.

To get this new functionality working, please follow these steps carefully, paying special attention to the library installations:


1.  **Install essential libraries:**

      * You need `librosa`, `soundfile`, and `sounddevice` for the module to function correctly.
      * Open your terminal in the `DrumScript` project root and run these commands:
        ```bash
        uv pip install librosa
        uv pip install soundfile
        uv pip install sounddevice
        ```
        
    > **Important  note for audio playback using [`sounddevice`](https://python-sounddevice.readthedocs.io/en/0.5.1/)**
        >
        > `sounddevice` relies on a **system-level library** called **[PortAudio](https://www.portaudio.com/). You might need to install this separately**:
        >
        > * **macOS:** `brew install portaudio` (if you have Homebrew)
        > * **Ubuntu/Debian:** `sudo apt-get install libportaudio2`
        > * **Windows:** `PortAudio` usually comes bundled with `sounddevice` wheels, but you might need to find specific installation instructions for your Python distribution.
        > 
        > **[`PortAudio` source code](https://github.com/PortAudio/portaudio)**
>
2.  **Prepare your audio files:**

      * Gather the MP3 or WAV files of your drum recordings that you want to label.
      * Update the `input_audio_paths` list in the `if __name__ == "__main__":` block of `data_labeller.py` with the actual paths to your files.

        Open` DrumScript/data_labeller/data_labeller.py` in a text editor. 
    
        In the if `__name__ == __main__:` block at the bottom, update the `input_audio_paths` list with the actual file paths to the drum recordings you want to label.

        ```Python

        if __name__ == "__main__":
            input_audio_paths = [
                "test_audio/reference_audio/test.mp3", # Example from your repo
                "path/to/your/groove_1.wav", # <--- Add your paths here
                "path/to/your/double_bass_run.mp3", # <--- Like this
                # Add as many audio files as you want to label
            ]
            output_dataset_dir = "labelled_datasets"
            generate_labelled_dataset(input_audio_paths, output_dataset_dir)
        ```
> 
3.  **Run the Labeller:**
      * Open your terminal.
      * Navigate to your `DrumScript` project's root directory (the one containing `.venv`, `pyproject.toml`, etc.).
      * Execute the script using `uv run`:
        ```bash
        uv run python3 DrumScript/data_labeller/data_labeller.py
        ```
>
The script will then guide you through each drum event detected. Listen to the played segment carefully, and type in the appropriate label(s) (e.g., "kick", "snare+ride", "fast\_kick\_1", "fast\_kick\_2") and press Enter. 
>
Once finished, your `labelled_drum_dataset.json` and `labelled_drum_dataset.csv` files will be in the `labelled_datasets` folder, and a new `labelled_datasets/audio_segments` folder will contain all the individual audio clips.

---

<!--END-->