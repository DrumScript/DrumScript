## **`DrumScript`**

<!--date_created: sun-15-june-2025-->
<!--date_updated: tues-13-jan-2026-->

DrumScript is an open-source `Python` library and suite of tools intended to make music more accessible for everyone. The Python package alpha is released alongside a free-to-use engine for members of the musical and sound analysis/engineering community to use in a zero-code way.

> #### **[hello.drumscript@gmail.com](hello.drumscript@gmail.com)**

> **Python>=3.9**

---
  - **[Project Structure](#project-structure)**
  - **[Features](#features)**
  - **[Documentation](#documentation)**
  - **[Installation](#install)**
  - **[Usage](#usage)**
      - **[Arguments](#arguments)**
      - **[Options](#options)**
      - **[Example](#example)**
  - **[Contributing](#contributing)**
  - **[Contact](#contact)**
  - **[FAQs](#faqs)**

### **Project Structure**

The `DrumScript` project is organised into the following main directories. For completeness, we include folders such as `notation_generator` because they contain functionality used in `DrumScript (Lite)`; however, the alpha release **does not** contain sheet music generation functionality. This is the goal of a forthcoming release of the full `DrumScript` package (targeted for the beginning of Q2 2026). See the **full [`repository_structure.md`](repository_structure.md)**.

```
DrumScript/
├── drumscript/             # Main source package directory
│   ├── __init__.py
│   ├── audio_processor/    # Audio loading, onset detection, feature extraction, tempo detection, stem-splitter and tempo-detection
│   ├── notation_generator/ # Constants
│   └── utils/              # Utility functions
├── docs/                   # Documentation for developers and contributors, as well as the `_build` artifacts for the `DrumScript` documentation website.
├── theory/                 # Reference documents (music theory, DSP, etc.). Sources provided
├── pyproject.toml          # Project metadata and dependencies (managed by `uv`).
├── README.md               # Main project overview (this file)
├── repository_structure.md # Full repository_structure.md
├── .github/                # GitActions files
│   ├── workflows/
│   │   ├── build_test.yml  # Tests whether the package is ready to be rebuilt and pushed to PyPi
│   │   ├── docs.yml        # Handles publishing of `DrumScript` documentation to GitHub Pages
│   │   ├── publish.yml     # Handles publishing of the package to PyPi automatically
│   │   └── tests.yml       # Handles tests on development branch and main to ensure they dont break when PR is merged
└── ...                     # Other config files (.gitignore, etc.)
```

---
### Features

* **Audio Input:** Supports common audio formats like `.wav` and `.mp3`.
* **Advanced Tempo Detection:** Estimates the tempo (BPM) of an audio file. A deterministic algorithm for tempo estimation. Analyses the entire audio file (not just local beats) to generate a "Tempogram." Conducts a "tempo election" to find the most consistent BPM, effectively handling complex syncopation and ghost notes where standard metronomes fail.
* **Drum Hit Detection:** Identifies the precise timing of drum strikes using onset event detection algorithms.
* **Audio Extractor:** We utilise the state-of-the-art [Demucs](https://github.com/adefossez/demucs) source separation model to provide high-quality drum extraction so users can separate audio files into their drum, guitar, base guitar and vocal stems. 
* **UI Integration:** Connect the package to a free-to-use public web interface.
* **Stem Splitting**: Automatically isolate drum tracks from full audio mixes using the `demucs` hybrid transformer model.
* **Onset Detection**: Precise identification of drum hits using spectral analysis.
<!--* **Classification**: Rule-based engine to classify hits (Snare, Kick, Hi-Hat) based on acoustic features.-->
<!--* **Score Generation**: Export transcribed drums to `.pdf` sheet music and `.xml` formats.-->


---
### Documentation

```{toctree}
:maxdepth: 1
:caption: Getting Started

how_it_works

```
```{toctree}
:maxdepth: 1
:caption: User Guide

tempo_estimation
advanced_sound_analysis101.md
glossary

```

```{toctree}
:maxdepth: 1
:caption: API Reference

api

```

```{toctree}
:maxdepth: 1
:caption: Development

contributor_guidance
testing_guidance
code_of_conduct
glossary

```

```{toctree}
:maxdepth: 1
:caption: About

about
```

---
### Installation

> `DrumScript` manages dependencies using `uv` and `pyproject.toml`.

```bash
pip install drumscript
# or
uv pip install drumscript
```

```bash
# Install dependencies
uv sync

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
### LilyPond Installation

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

`music21` will attempt to find LilyPond automatically. If you encounter errors, you may need to configure the path manually (see `DrumScript/notation_generator/pdf_exporter.py`).

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
