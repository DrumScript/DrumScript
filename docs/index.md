## **DrumScript**

<!--date_created: sun-15-june-2025-->
<!--date_updated: tues-13-jan-2026-->

> **Python 3.12.10**

`DrumScript` is a `Python` package that converts **drum audio** into **sheet music** (drum notation). Born from a drummer's need for accessible sheet music, this project aims to be a free, open-source tool for the music community.

It leverages **audio signal processing** and a **rule-based classification engine** to detect individual drum hits, transcribe them into a **musical score**, and export them as `.pdf` or `.xml` files, which you can use directly or import into software like Guitar Pro or Logic Pro.

***[hello.drumscript@gmail.com](mailto: hello.drumscript@gmail.com)***

---

  - **[Features](#features)**
  - **[Roadmap](#roadmap)**
  - **[Installation](#installation)**
  - **[Usage](#usage)**
      - **[Arguments](#arguments)**
      - **[Options](#options)**
      - **[Example](#example)**
  - **[Contributing](#contributing)**
  - **[Contact](#contact)**
  - **[FAQs](#faqs)**

> **NOTE:** See **[`docs/how_it_works.md`](#docs/how_it_works.md)** if you are interested in the link between **music theory** and `DrumScript`'s structure.

> **NOTE:** For simplicity, `DrumScript` uses the generic spelling of the word ***quantize***, rather than the British English spelling ***quantise***.

---

### Features

  * **Audio Input:** Supports common audio formats like `.wav` and `.mp3`.
  * **Automatic Tempo Detection:** Estimates the tempo (BPM) of an audio file automatically.
  * **Drum Hit Detection:** Identifies the precise timing of drum strikes using onset detection algorithms.
  <!--* **Multi-Instrument Classification:** Differentiates between various drum kit elements (e.g., kick, snare, hi-hat) and can identify **concurrent hits** (e.g., a kick and crash cymbal played at the same time).-->
  <!--* **Musical Quantization:** Aligns detected drum hits to a musical grid for clean, accurate notation.-->
  <!--* **Sheet Music Output:** Generates clear and readable drum notation in both `.pdf` and MusicXML (`.xml`) formats.-->
  * **Stem Splitting**: Isolate drums from full songs using `Demucs` technology.
  <!--* **Automatic Transcription**: Converts raw audio into readable drum scores.-->
  <!--* **Multi-Format Export**: Generates `.pdf` for print and `.xml` for MusicXML compatible software (Guitar Pro, Logic Pro, etc.).-->
  <!--* **Deterministic Engine**: Uses physics-based rules rather than opaque "black box" machine learning for transparent classification.-->


### Roadmap

Here are some features planned for future releases:

  * **Advanced Notation:** Add support for accents, ghost notes, and more complex rhythmic figures.
  * **Expanded Instrument Range:** Increase the number of percussion instruments the system can detect, including those used in specific genres (e.g., double-bass for metal).
  * **UI Integration:** Connect the package to a free-to-use public web interface.

---

### Installation

`DrumScript` uses `uv` for efficient dependency management.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/victoria-mckinney/DrumScript.git
    cd DrumScript
    ```
2.  **Create a virtual environment and install dependencies:**
    ```bash
    uv venv
    source .venv/bin/activate  # On Windows, use: .venv\Scripts\activate
    uv pip install -r requirements.txt
    ```

> **NOTE:** Other `Python` package managers, like `pip` or `conda`, can be used interchangeably with the commands above.

#### LilyPond Installation

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

---

### Dependencies

A full list of dependencies can be found in **[`requirements.txt`](#requirements.txt)** and **[`pyproject.toml`](#pyproject.toml)**.

---

> **Important note for audio playback (`sounddevice`):**
>
> The `sounddevice` library relies on **[PortAudio](https://www.portaudio.com/)**. You might need to install this system-level library separately:
>
>   * **macOS:** `brew install portaudio`
>   * **Ubuntu/Debian:** `sudo apt-get install libportaudio2`
>   * **Windows:** PortAudio is usually bundled with `sounddevice` wheels, but check official documentation if you have issues.
>
> **[`PortAudio` source code](https://github.com/PortAudio/portaudio%5D\(https://github.com/PortAudio/portaudio\))**

---

> **Important note for `.mp3` users:**
>
> **See also [FAQs](#faqs)**
>
> To process `.mp3` files, you must first install **`FFmpeg`**, a command-line tool for handling audio and video.
>
> ##### Installing `FFmpeg`
>
> **How to install `FFmpeg` via `DrumScript`**
>
> The package includes a helper script for easy installation.
>
> ```python
> # In your main.py or another script
> import utils.ffmpeg_installer as ffmpeg_installer
> ```

> # This will prompt for a password on Linux/macOS for system-wide installation.
>
> ffmpeg_installer.install_ffmpeg()
>
> ```
> 
> **How to install `FFmpeg` manually**
> ```
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

> ```
> ```

---

### Usage

Run `DrumScript` from the command line using `main.py`.

```bash
python main.py <input_audio_file> <output_sheet_music_path> [OPTIONS]
```

#### Arguments

  * `<input_audio_file>`: Path to your drum audio recording (`.wav`, `.mp3`, etc.).
  * `<output_sheet_music_path>`: Desired path for the generated file (e.g., `drum_score.pdf` or `drum_score.xml`).

#### Options

  * `--tempo <BPM>`: (Optional) Manually specify the tempo in Beats Per Minute. If not provided, the script will attempt to detect the tempo automatically.

#### Example

```bash
python main.py my_drum_track.wav drum_score.pdf --tempo 120
```

---

### Contributing

We welcome contributions! `DrumScript` is intended to be a community-owned project. If you have ideas, bug fixes, or new features, please **[open an issue](https://github.com/victoria-mckinney/DrumScript/issues/new)** or submit a **[pull request](https://github.com/victoria-mckinney/DrumScript/pulls)**.

## Documentation

```{toctree}
:maxdepth: 2
:caption: Contents:

about.md
how_it_works.md
testing_guidance.md
contributor_guidance.md
code_of_conduct.md
tempo_estimation.md
glossary.md
api.rst
```

---

### Contact

For questions or support, please **[open an issue](https://github.com/victoria-mckinney/DrumScript/issues)** on the GitHub repository or email the maintainers:

***[hello.drumscript@gmail.com](#hello.drumscript%40gmail.com)***

---

### FAQs

  * #### Why don't you include `FFmpeg` as a dependency?
    `FFmpeg` is a system-level program, not a Python library, so it cannot be bundled directly into the package's dependencies via `requirements.txt` or `pyproject.toml`. It must be installed on the operating system itself.
  * #### Is it safe to use the `install_ffmpeg()` helper script?
    Yes. The script is a simple wrapper that runs standard, trusted installation commands for each OS. However, you are always welcome to follow the manual installation instructions instead.
  * #### What normalisation is applied to loaded audio?
    The `audio_loader.py` script applies **peak normalisation** after loading an audio file. It first converts the audio to mono and then normalises it using `librosa.util.normalize()`.
  * #### What is `peak normalisation`? 🔊
    Peak normalisation adjusts an audio file's volume so that its loudest point (the "peak") is set to a maximum level (1.0) without distortion. This standardises the volume across different recordings, ensuring the classification engine receives a consistent signal. This allows the classification rules to work reliably across different recordings, focusing on the sonic **character** of each drum, not just its loudness.
  * #### Does normalisation remove audio detail?
    No. Peak normalisation is a **linear process**—it multiplies every audio sample by the same constant value, like turning a volume knob. The "shape" of the sound wave, which contains all the sonic details and rhythmic information, is perfectly preserved.
  * #### What is `hop_length`?
    When analysing audio, `librosa` slides a small window across the audio file. The **`hop_length`** is the number of audio samples the window "hops" forward for each step. A smaller `hop_length` results in more analysis windows and a more detailed, time-accurate analysis, which is crucial for capturing fast musical passages. For example, with a sample rate of 44100 Hz and a `hop_length` of 256 samples, the analysis resolution is:
    $$
    $$$$\\frac{256 \\text{ samples}}{44100 \\text{ samples per second}} \\approx 0.0058 \\text{ seconds (or 5.8 milliseconds)}
    $$



---

<!--END -->
