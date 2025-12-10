## **`DrumScript Lite`**

<!--date_created: sun-15-june-2025-->
<!--date_updated: weds-10-dec-2025-->


DrumScript is an open-source `Python` library and suite of tools intended to make music more accessible for everyone. The Python package beta is released alongside a free-to-use engine for members of the musical and sound analysis community to use in a zero-code way.

> #### **[hello.drumscript@gmail.com](hello.drumscript@gmail.com)**

> **Python>=3.9**


**Acknowledgements**

* **Demucs**: The stem splitting functionality in DrumScript is built upon the incredible work of the Demucs project by [@adefozzez](https://github.com/adefossez) while at Facebook/Meta. Since he is no longer at Meta, we referenced the forked repo.

* **Librosa**: For the foundational audio processing tools.
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

### **Project Structure**

The `DrumScript` (Lite) project is organised into the following main directories. See the **full [`repository_structure.md`](repository_structure.md)**.

```
DrumScript/
├── drumscript/             # Main source package directory
│   ├── __init__.py
│   ├── audio_processor/    # Audio loading, onset detection, feature extraction, tempo detection, stem-splitter and tempo-detection
│   ├── notation_generator/ # Constants
│   └── utils/              # Utility functions
├── developer_docs/         # Documentation for developers and contributors
├── theory/                 # Reference documents (music theory, DSP, etc.)
├── pyproject.toml          # Project metadata, dependencies, build config
├── README.md               # Main project overview (this file)
└── ...                     # Other config files (.gitignore, etc.)
```

---
#### Features

* **Audio Input:** Supports common audio formats like `.wav` and `.mp3`.
* **Advanced Tempo Detection:** Estimates the tempo (BPM) of an audio file. A deterministic algorithm for tempo estimation. Analyses the entire audio file (not just local beats) to generate a "Tempogram." Conducts a "tempo election" to find the most consistent BPM, effectively handling complex syncopation and ghost notes where standard metronomes fail.
* **Drum Hit Detection:** Identifies the precise timing of drum strikes using onset event detection algorithms.
* **Audio Extractor:** We utilise the state-of-the-art [Demucs](https://github.com/adefossez/demucs) source separation model to provide high-quality drum extraction so users can separate audio files into their drum, guitar, base guitar and vocal stems. 
* **UI Integration:** Connect the package to a free-to-use public web interface.



---
### Installation

```bash
pip install drumscript
# or
uv pip install drumscript
```
**Dependencies**

A full list of project- and optional dependencies can be found in the **[`pyproject.toml`](#pyproject.toml)**.

`DrumScript` does not use a [`requirements.txt`](#requirements.txt), or a [`requirements.in`](#requirements.in) file. **All dependencies** are declared in the **[`pyproject.toml`](#pyproject.toml)**.



---

### Usage
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
  * #### What normalization is applied to loaded audio?
    The `audio_loader.py` script applies **peak normalization** after loading an audio file. It first converts the audio to mono and then normalizes it using `librosa.util.normalize()`.
  * #### What is `peak normalization`? 
    Peak normalization adjusts an audio file's volume so that its loudest point (the "peak") is set to a maximum level (1.0) without distortion. This standardizes the volume across different recordings, ensuring the classification engine receives a consistent signal. This allows the classification rules to work reliably across different recordings, focusing on the sonic **character** of each drum, not just its loudness.
  * #### Does `normalization` remove audio detail?
    No. Peak normalization is a **linear process**—it multiplies every audio sample by the same constant value, like turning a volume knob. The "shape" of the sound wave, which contains all the sonic details and rhythmic information, is perfectly preserved.
  * #### What is `hop_length`?
    When analysing audio, `librosa` slides a small window across the audio file. The **`hop_length`** is the number of audio samples the window "hops" forward for each step. A smaller `hop_length` results in more analysis windows and a more detailed, time-accurate analysis, which is crucial for capturing fast musical passages. For example, with a sample rate of 44100 Hz and a `hop_length` of 256 samples, the analysis resolution is:
    $$
    $$$$\\frac{256 \\text{ samples}}{44100 \\text{ samples per second}} \\approx 0.0058 \\text{ seconds (or 5.8 milliseconds)}
    $$

---

<!--END -->
