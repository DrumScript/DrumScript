## **`DrumScript`**

<!--date_created: sun-15-june-2025-->
<!--date_updated: sun-05-apr-2026-->

DrumScript is an open-source `Python` library and suite of tools intended to make music more accessible for everyone. The Python package alpha is released alongside a free-to-use engine for members of the musical and sound analysis/engineering community to use in a zero-code way.

> #### **[hello.drumscript@gmail.com](hello.drumscript@gmail.com)**

> **Python>=3.9**

---
  - **[Project Structure](#project-structure)**
  - **[Features](#features)**
  - **[Installation](#install)**
  - **[Usage](#usage)**
      - **[Arguments](#arguments)**
      - **[Options](#options)**
      - **[Example](#example)**
  - **[Contributing](#contributing)**
  - **[Contact](#contact)**
  - **[FAQs](#faqs)**

**Workflow Statuses**
>
> [![Run Tests](https://github.com/DrumScript/DrumScript/actions/workflows/tests.yml/badge.svg?branch=build%2Fclassification_model)](https://github.com/DrumScript/DrumScript/actions/workflows/tests.yml)

**Demo Notebooks**
>
> [![Try `DrumScript` in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1eDVXc3d6ezmorxINOjzldRPSC3emTl2I)


---
### **Project Structure**

The `DrumScript` project is organised into the following main directories. See **[`repository_structure.md`](repository_structure.md)** for the full repository structure. 

```
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
│   │   ├── pdf_generator.py
│   │   └── constants.py             # Single-source of truth for constants such as `SAMPLE_RATE`, `N_FFT` used globally through `DrumScript`
│   └── utils/                       # Utility functions.
├── docs/                            # Documentation for developers and contributors, as well as the `_build` artifacts for the `DrumScript` documentation website.
│    ├── theory/                          # Reference documents (music theory, DSP, etc.). Sources provided
├── local_tests/                     # Local test scripts (e.g., interface testing).
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
├── pyproject.toml                   # Project metadata and dependencies (managed by `uv`).
└── uv.lock                          # Pinned versions of all dependencies.
```

---
#### Overview of `DrumScript` Features

* **Audio Input:** Supports common audio formats like `.wav` and `.mp3`, both as inputs and outputs
<!--* **Drum Hit Detection:** Identifies the precise timing of drum strikes using onset event detection algorithms.-->
* **Onset Detection**: Onset detection method which has been tuned to the features of percussion audio physics rather than polyphnic audio physics (such as for piano, guitar etc).
* **Audio Extraction:** We utilise the state-of-the-art [Demucs](https://github.com/adefossez/demucs) source separation model to provide high-quality drum extraction so users can separate audio files into their drum, guitar, base guitar and vocal stems.
* **Stem-Manipulation:** We also utilise the state-of-the-art [Demucs](https://github.com/adefossez/demucs) source separation model to provide high-quality drum extraction from given audio path so users can produce **drumless backing tracks** to play along to. The method also allows users to extract bass guitar. In the future we hope to add more advanced stem extraction! [See **Contributing**](#contributing) section for more information.
* **Drum Classification**: Rule-based engine to classify hits (Snare, Kick, Hi-Hat) based on acoustic features tested and refined on a large dataset of isolated audio samples for each drum part, over almost a year.
* **Multiple Output Formats**: Export transcribed drums to `midi (.mid)` and `.musicXML` so you can add to your preferred DAW (ie Logic Pro, Cubase, Ableton etc)
* **PDF Score Generation**: Generate a PDF of extracted drums/ 
* **UI Integration:** Free-to-use public web interface for no-code users, with no persistent storage of uploaded or transformed files. 


> `DrumScript` functionality is based on **deterministic methods** rather than probabilistic (AI/ML).
> We cannot guarantee however that any non-native Python packages or libraries that form part of `DrumScript` build wheel will not contain probabilities methods (ie `Demucs`) or `Librosa`


---
### Installation

> `DrumScript` manages dependencies using `uv` and `pyproject.toml`.

```bash
uv pip install drumscript
```

```bash
# Install dependencies
uv pip install -e .
```

**Dependencies**

A full list of project- and optional dependencies can be found in the **[`pyproject.toml`](#pyproject.toml)**.

`DrumScript` does not use a [`requirements.txt`](#requirements.txt), or a [`requirements.in`](#requirements.in) file. **All dependencies** are declared in the **[`pyproject.toml`](#pyproject.toml)**.



---

### Usage

> **Simple**

```python
import drumscript as ds

# 1. Load Audio
y, sr = ds.load_audio("test.wav")

# 2. Detect Tempo
bpm = ds.detect_tempo(y, sr)

# 3. Separate Stems
stems = ds.separate_stems("test.wav", output_dir="./my_stems")
```

> **Full commands**

#### **Basic Transcription**

To run the full transcription pipeline on an audio file, use the main entry point. This will load the audio, separate the drums (if needed), classify hits, and generate a PDF score.

```python
from drumscript.main import main

# Run the full pipeline
main()
# Follow the interactive prompts to provide the input file path.

```

#### **Stem Splitting**

Isolate the drum track from a full music mix using the `StemSplitter` class. This is useful if you want to process the drum audio separately.

```python
from drumscript.audio_processor.stem_splitter import StemSplitter

# Initialise the splitter
splitter = StemSplitter()

# Split the audio file; returns the path to the isolated drum track
drum_track_path = splitter.split_drums(
    input_file="path/to/your/song.mp3",
    output_dir="output_stems/"
)

print(f"Drum stem saved at: {drum_track_path}")

```

#### **Audio Loading**

Load and normalise audio files for analysis. The `AudioLoader` handles mono conversion and peak normalisation automatically.

```python
from drumscript.audio_processor.audio_loader import AudioLoader

# Initialise loader
loader = AudioLoader()

# Load audio (returns audio time series and sample rate)
y, sr = loader.load_audio("path/to/drum_stem.wav")
```
---

### Contributing

We welcome contributions! `DrumScript` is intended to be a community-owned project. If you have ideas, bug fixes, or new features, please **[open an issue](https://github.com/DrumScript/DrumScript/issues/new)** or submit a **[pull request](https://github.com/DrumScript/DrumScript/pulls)**.

> **All bug reports and feature requests must be filed as [GitHub Issues](https://github.com/DrumScript/DrumScript/issues)**. All code changes must be submitted as [Pull Requests](https://github.com/DrumScript/DrumScript/pulls). Please do not email us directly about the project, as keeping all communication public helps everyone.

###  Roadmap

The ultimate goal of this project is to build a fully open-source classification engine that converts drum audio directly into .pdf sheet music.

It leverages **audio signal processing** and a **rule-based classification engine** to detect individual drum hits, transcribe them into a **musical score**, and export them as `.pdf` files, which you can use directly or import into software like Guitar Pro or Logic Pro.

---

### Contact

> All bug reports and feature requests must be filed as [GitHub Issues](https://github.com/DrumScript/DrumScript/issues). All code changes must be submitted as [Pull Requests](https://github.com/DrumScript/DrumScript/pulls). 


---
<!--### LilyPond Installation

To generate high-quality PDF sheet music, `DrumScript` uses `music21`, which relies on the music engraving program **LilyPond**. You must install LilyPond separately.

  * **Download & Install LilyPond:**
      * Visit the official LilyPond website: [https://lilypond.org/](https://lilypond.org/) and download the version for your OS.
      * **macOS Users:** You can install via [Homebrew](https://brew.sh/):
        ```bash
        brew install lilypond
        ```
  * **Verify Installation:**
    Check that LilyPond is installed correctly by running:
    ```bash
    lilypond --version
    ```

`music21` will attempt to find LilyPond automatically. If you encounter errors, you may need to configure the path manually (see `DrumScript/notation_generator/pdf_exporter.py`).-->

> **Important note for audio playback (`sounddevice`):**
>
> The `sounddevice` library relies on **[PortAudio](https://www.portaudio.com/)**. You might need to install this system-level library separately:
>
>   * **macOS:** `brew install portaudio`
>   * **Ubuntu/Debian:** `sudo apt-get install libportaudio2`
>   * **Windows:** PortAudio is usually bundled with `sounddevice` wheels, but check official documentation if you have issues.
>
> **[`PortAudio` source code](https://github.com/PortAudio/portaudio%5D\(https://github.com/PortAudio/portaudio\))**


> **Important note for `.mp3` users** (**see also [FAQs](#faqs)**)

To process `.mp3` files, you must first install **`FFmpeg`**, a command-line tool for handling audio and video.
>
### Installing `FFmpeg`

> **How to install `FFmpeg` via `DrumScript`**
>
> The package includes a helper script for easy ¢¢.
>
> ```python
> # In your main.py or another script
> import utils.ffmpeg_installer as ffmpeg_installer
> ```
> `ffmpeg_installer.install_fmpeg()`
> 
> This will prompt for a password on Linux/macOS for system-wide ¢¢.


>
**How to install `FFmpeg` manually**
>
>
>   * **macOS (using [Homebrew](https://brew.sh/))**:
>     ```bash
>     brew install ffmpeg
>     ```
>   * **Linux (using apt for Debian/Ubuntu)**:
>     ```bash
>     sudo apt update
>     sudo apt install ffmpeg
>     ```
>   * **Windows**:
>     Download the binaries from the **[official website](https://ffmpeg.org/download.html)**, extract the files, and add the `bin` directory to your system's `PATH` environment variable.
>
> <!-- end list -->

---

### FAQs

  * #### Why don't you include `FFmpeg` as a dependency?
    `FFmpeg` is a system-level program, not a Python library, so it cannot be bundled directly into the package's dependencies via `requirements.txt` or `pyproject.toml`. It must be installed on the operating system itself.
  * #### Is it safe to use the `install_ffmpeg()` helper script?
    Yes. The script is a simple wrapper that runs standard, trusted ¢¢ commands for each OS. However, you are always welcome to follow the manual ¢¢ instructions instead.
  * #### What normalisation is applied to loaded audio?
    The `audio_loader.py` script applies **peak normalisation** after loading an audio file. It first converts the audio to mono and then normalises it using `librosa.util.normalize()`.
  * #### What is `peak normalisation`? 
    Peak normalisation adjusts an audio file's volume so that its loudest point (the "peak") is set to a maximum level (1.0) without distortion. This standardises the volume across different recordings, ensuring the classification engine receives a consistent signal. This allows the classification rules to work reliably across different recordings, focusing on the sonic **character** of each drum, not just its loudness.
  * #### Does `normalisation` remove audio detail?
    No. Peak normalisation is a **linear process**—it multiplies every audio sample by the same constant value, like turning a volume knob. The "shape" of the sound wave, which contains all the sonic details and rhythmic information, is perfectly preserved.
  * #### What is `hop_length`?
    When analysing audio, `librosa` slides a small window across the audio file. The **`hop_length`** is the number of audio samples the window "hops" forward for each step. A smaller `hop_length` results in more analysis windows and a more detailed, time-accurate analysis, which is crucial for capturing fast musical passages. For example, with a sample rate of 44100 Hz and a `hop_length` of 256 samples, the analysis resolution is:
    $$
    $$$$\\frac{256 \\text{ samples}}{44100 \\text{ samples per second}} \\approx 0.0058 \\text{ seconds (or 5.8 milliseconds)}
    $$

---
### **Acknowledgements**

* **Demucs**: The stem splitting functionality in DrumScript is built upon the incredible work of the Demucs project by [@adefozzez](https://github.com/adefossez) while at Facebook/Meta. Since he is no longer at Meta, we referenced the forked repo.

* **Librosa**: For the foundational audio processing tools.

---

<!--END -->
