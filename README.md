# **`DrumScript`**

<!--date_created: sun-15-june-2025-->
<!--date_edited: fri-31-july-2026--->


**DrumScript** is an open-source Python library and CLI tool for drum audio analysis and transcription. Give it a recording — a full mix or an isolated drum stem — and it will generate PDF sheet music, MIDI files, and MusicXML output. The `DrumScript` model is a **deterministic classifier**, and doesn't use AI/machine learning. Built for drummers and by drummers, it is - and always will be - an open-source community tool.

> **Python >=3.9**

**Workflow Status**
> 
[![Run Tests](https://github.com/DrumScript/DrumScript/actions/workflows/tests.yml/badge.svg?branch=main)](https://github.com/DrumScript/DrumScript/actions/workflows/tests.yml)
>
**[Documentation](https://drumscript.github.io/DrumScript/)**
>
> **[Try DrumScript In Colab](https://colab.research.google.com/drive/15yBGu6WURPyiH-sEQ82g_2T2wKqiIPsq)**
>
> <a href="https://colab.research.google.com/drive/15yBGu6WURPyiH-sEQ82g_2T2wKqiIPsq" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>


- **[Overview](#overview)**
- **[Features](#features)**
- **[Installation](#installation)**
- **[Quick Start](#quick-start)**
- **[CLI Usage](#cli-usage)**
- **[Contributing](#contributing)**
- **[Traffic](#traffic)**
- **[FAQs](#faqs)**
- **[Similar projects](#similar-projects)**


---

## Overview
*[back](#drumscript)*

**Public Alpha (v0.1.4+) — June to August 2026**

 - We're looking for early adopters and feedback
 - [Feedback on the classification model](https://github.com/DrumScript/DrumScript/issues), and help shape v1.0.0.
 - In particular we are interested in hearing from everyone:: drummers (coding not required!), sound engineers and academics in Music Information Retrieval with an interest in deterministic drum/percussion classifications. 
 - For beta release, we are planning to (amongst other things) improve the classification model, fix any user-suggested bugs, implement user-suggested feature requests and **most importantly** build a **WebGPU/ONNX/WASM UI** that will be free to use for all.

> See the **[Roadmap](https://drumscript.github.io/DrumScript/guide/roadmap.html)** for what's planned.

**What it looks like**

<!-- TODO: Replace with a GIF showing terminal output-->
<!-- For now, this shows the PDF transcription output -->

*Input: audio recording → Output: drum notation (PDF).

**Example 1: Simple groove**

![DrumScript transcription output](./docs/_static/test_wav.png)

**Example 2: A well-known Sabbath song**

![DrumScript transcription output](./docs/_static/iron_man_1.png)
![DrumScript transcription output](./docs/_static/iron_man_2.png)
![DrumScript transcription output](./docs/_static/iron_man_3.png)

---

## Features
*[back](#drumscript)*

- **Automatic Drum Transcription:** Detects kicks, snares, hi-hats, toms, and cymbals using a deterministic, rule-based classification engine — no machine learning required.
- **Tempo Detection:** Automatically estimates BPM using a voting-system algorithm tuned for percussive audio.
- **Onset Detection:** Onset detection method tuned to the physics of percussion audio rather than polyphonic instruments (piano, guitar, etc.).
- **Stem Separation:** Uses the state-of-the-art [Demucs](https://github.com/adefossez/demucs) source separation model to isolate drums, bass, vocals, and other instruments from a full mix.
- **Backing Track Generator:** Automatically remove the drums from any `.mp3` or `.wav` to create a drumless play-along track. Bass-only and vocal-only extraction also supported.
- **Multiple Output Formats:** Export transcriptions to PDF sheet music, MIDI (`.mid`), and MusicXML (`.xml`) for import into DAWs and notation software (Logic Pro, Cubase, Ableton, MuseScore, Sibelius, etc.).
- **Deterministic Classification:** DrumScript's core classification engine uses physics-based rules derived from acoustic analysis of real drum samples, not probabilistic AI/ML models.

> **Note:** Some dependencies used by DrumScript (e.g. [Demucs](https://github.com/adefossez/demucs), [librosa](https://librosa.org/)) may internally use probabilistic methods. DrumScript's own classification engine is fully deterministic.

---

## Project Structure

See [`repository_structure.md`](repository_structure.md) for the full project layout.

```
DrumScript/
├── drumscript/                 # Main source package
│   ├── __init__.py             # Public API (transcribe, load_audio, etc.)
│   ├── main.py                 # CLI entry point
│   ├── audio_processor/        # Audio loading, DSP, stem splitting
│   ├── drum_classifier/        # Rule-based classification engine
│   ├── notation_generator/     # Score building, PDF/MIDI/XML export
│   ├── datasets/               # Benchmark dataset adapters (IDMT, etc.)
│   └── utils/                  # Helpers (ffmpeg installer, research scripts)
├── benchmarks/                 # Evaluation runners (see benchmarks/README.md)
├── docs/                       # Sphinx documentation
├── tests/                      # pytest test suite (131 unit + 8 integration)
├── .github/workflows/          # CI/CD (tests, build, publish, docs)
├── pyproject.toml              # Package metadata and dependencies
└── uv.lock                     # Pinned dependency versions
```


## Installation
*[back](#drumscript)*

**For users:**

```zsh
pip install drumscript
```

**For developers:**

```zsh
git clone https://github.com/DrumScript/DrumScript.git
cd DrumScript
uv sync # this will create a .venv
source .venv/bin/activate && uv sync --extra dev
pytest -m "not slow"
```

DrumScript manages all dependencies via [`pyproject.toml`](pyproject.toml) using [`uv`](https://docs.astral.sh/uv/). There is no `requirements.txt`.

### System dependencies

- **ffmpeg** is required for MP3 input/output. WAV-only workflows do not need it.
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt-get install ffmpeg libsndfile1`
  - Windows: [Download from ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.
  - Or use the built-in helper: `import drumscript as ds; ds.install_ffmpeg()`

- **PortAudio** is required by `sounddevice` for audio playback.
  - macOS: `brew install portaudio`
  - Ubuntu/Debian: `sudo apt-get install libportaudio2`
  - Windows: Usually bundled with the `sounddevice` wheel.

- **git-lfs** is **only** required if you want to run the documentation notebooks locally or rebuild the docs site. Some example audio files in `docs/guide/interactive/audio/` are tracked via Git LFS to keep the main repo lightweight. `pip install drumscript` and ordinary use of the package do **not** need it. If you skip this step, `git clone` will still succeed — you'll just get small LFS pointer files in place of the example audio.
  - macOS: `brew install git-lfs`
  - Ubuntu/Debian: `sudo apt-get install git-lfs`
  - Windows: [Download from git-lfs.com](https://git-lfs.com/) or install via `winget install GitHub.GitLFS`.
  - After installing, run `git lfs install` once, then `git lfs pull` inside the cloned repo to fetch the audio.

---

## Quick Start
*[back](#drumscript)*

> Please note: DrumScript assumes you are providing **drum audio-only inputs by default** 

> If you are using transcription with full song use the `full_song=True` flag, ie 

### End-to-end transcription

```python
import drumscript as ds

# Transcribe an isolated drum stem → PDF
pdf_path = ds.transcribe("drum_audio.wav")

# Transcribe a full song (separates drums automatically)
pdf_path = ds.transcribe("full_song.mp3") # drum only audio
pdf_path = ds.transcribe("full_song.mp3", full_song=True) # full song, tells DrumScript to extract the drums first and then transcribe

# Get all intermediate results
result = ds.transcribe("drum_audio.wav", verbose=True)
print(f"Tempo: {result['tempo']:.1f} BPM")
print(f"Events: {len(result['events'])}")
```

### Load and explore audio

```python
import drumscript as ds

# Load at native sample rate (for notebooks / exploration)
audio_file = ds.load_audio("drum_audio.wav")
print(f"Sample rate: {sr} Hz, Duration: {len(audio)/sr:.1f}s")

# Detect tempo
bpm = ds.detect_tempo("drum_audio.wav")
print(f"Tempo: {bpm:.1f} BPM")
```

### Extract stems

```python
import drumscript as ds

# Extract just the drum stem from full polyphonic audio (let's call it "full_song.wav")
# Not to be confused with "full_song" flag used in transcribe(), which is for when you want to extract stems before transcribing
stem_split = ds.extract_stems("full_song.wav")

```

### Create drumless backing track to your favourite songs

```python
import drumscript as ds

# Remember to use mp3 flag if using mp3 audio
# default input format is .wav

remove_drums = ds.extract_stems("full_song.wav",
    drumless=True,
    verbose=True,
)
print(f"Backing track: {results['mix']}")
```

---

## Benchmarking

DrumScript includes a benchmarking framework for evaluating the classifier against standard ADT datasets using [`mir_eval`](https://github.com/mir-evaluation/mir_eval). Currently supports IDMT-SMT-Drums V2.

```zsh
# Install dev dependencies (includes mir_eval)
uv sync --extra dev

# Run the IDMT benchmark
uv run --extra dev python benchmarks/run.py idmt \
  --root /path/to/IDMT-SMT-DRUMS-V2

# Run on a single subset with a limit
uv run --extra dev python benchmarks/run.py idmt \
  --root /path/to/IDMT-SMT-DRUMS-V2 \
  --subset RealDrum --limit 5
```

Results are archived to `outputs/benchmarks/idmt/` with per-file metrics, summary statistics, and git commit tracking for reproducibility. See [`benchmarks/README.md`](benchmarks/README.md) for dataset setup and full usage.


---

## CLI Usage
*[back](#drumscript)*

DrumScript also provides a command-line interface.

### Basic transcription (isolated drum stem)

```zsh
drumscript drum_audio.wav
```

### Full song transcription (auto-separates drums)

```zsh
drumscript full_song.mp3 --full-song
```

### Extract a drumless backing track

```zsh
drumscript full_song.mp3 --drumless
```

### All options

```zsh
drumscript <audio_file> [OPTIONS]

Options:
  --full-song     Transcribe a full song (isolates drums first via Demucs)
  --drumless      Extract a drumless backing track
  --mute STEM     Mute a specific stem (e.g. --mute bass). Repeatable.
  --all-stems     Export all individual stems (drums, bass, vocals, other)
  --format FORMAT Output format for stems: wav (default) or mp3 (requires ffmpeg to be installed)
  --rudiment      Optimise classification for isolated single beats
  --ts SIG        Time signature (default: 4/4)
```

### Examples

```zsh
# Transcribe with 6/8 time signature
drumscript drum_audio.wav --ts 6/8

# Extract all stems as MP3
drumscript full_song.mp3 --all-stems --format mp3

# Classify rudiments
drumscript snare_hit.wav --rudiment
```
---

## Contributing
*[back](#drumscript)*

We welcome contributions! DrumScript is intended to be a community-owned project. You can also refer to detailed contributor guidance **[here](./docs/development/contributor_guidance.md)**

- **[Open an Issue](https://github.com/DrumScript/DrumScript/issues/new)** for bugs or feature requests.
- **[Submit a Pull Request](https://github.com/DrumScript/DrumScript/pulls)** for code changes.
- See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the full contributor guide.

> All bug reports and feature requests must be filed as GitHub Issues. All code changes must be submitted as Pull Requests. Keeping discussion public helps everyone.

**[hello.drumscript@gmail.com](mailto:hello.drumscript@gmail.com)**

## Alpha Priorities (v0.0.4 < v1.0.0) 
The alpha phase runs between 01 June and 31 August 2026

**What works today:**

- End-to-end transcription pipeline: audio → onsets → classification → PDF / MIDI / MusicXML
- Tempo detection via spectral onset envelope
- Stem separation using Demucs (`htdemucs` 4-stem model)
- Drumless backing track generation
- CLI and Python API

**What we're focused on during the alpha:**

- Expanding test coverage across genres, kit types, and recording conditions
- Fixing classification edge cases (deep snares vs clicky kicks, splash cymbals vs open hats)
- Improving onset detection sensitivity for ghost notes and fast passages
- Stabilising the public API ahead of the beta freeze
- Community feedback collection

---

## Publishing a new release

We use an automated pipeline to publish new versions to PyPI. All releases must use a specific tag format: `vX.Y.Z` (for example, `v0.2.0`).

**To publish a release via GitHub Actions (Recommended):**
1. Go to the **Actions** tab in this repository.
2. Click on **Create Release** on the left menu.
3. Click **Run workflow** on the right.
4. Type in your new version number (e.g., `0.2.0`) and click **Run workflow**. GitHub will handle the rest!

---

## Testing 

For detailed instructions on testing and publishing via the command line, please see our [Testing Guidance](tests/README.md).

---

## Traffic
*[back](#drumscript)*

We collate usage over time for performance-monitoring. Live repository statistics — updated daily:

- [**View Report (PDF)**](https://github.com/DrumScript/DrumScript/blob/github-repo-stats/DrumScript/DrumScript/latest-report/report.pdf)
<!--- [**View Report (HTML)**](https://github.com/DrumScript/DrumScript/blob/github-repo-stats/DrumScript/DrumScript/latest-report/report.html)

> Views, clones, stars, forks, top referrers and popular paths. Data collected automatically via [github-repo-stats](https://github.com/jgehrcke/github-repo-stats). Defaults to last 14 days in outputs. Raw data available on **[github-repo-stats](https://github.com/DrumScript/DrumScript/tree/github-repo-stats/DrumScript/DrumScript/ghrs-data**) branch-->

---

## FAQs
*[back](#drumscript)*

### Why doesn't DrumScript include `ffmpeg` as a dependency?

ffmpeg is a system-level program, not a Python library, so it cannot be declared in `pyproject.toml`. It must be installed on the operating system. DrumScript provides an `install_ffmpeg()` helper to make this easier. 

### What normalisation is applied to loaded audio?

`load_audio()` applies **peak normalisation** after loading. It converts the audio to mono and scales it so the loudest sample is at 1.0. This is a linear operation — no audio detail is lost.

### What is `hop_length`?

When analysing audio, librosa slides a small analysis window across the signal. The `hop_length` is how many samples the window advances per step. DrumScript uses `HOP_LENGTH = 128`, which at 44100 Hz gives a time resolution of ~2.9 milliseconds — fast enough to capture individual drum hits.

### Does DrumScript use AI/machine learning?

DrumScript's own classification engine is **fully deterministic** — it uses physics-based rules, not neural networks. However, the optional stem separation feature uses [Demucs](https://github.com/adefossez/demucs), which is a deep learning model by Meta/Facebook.

---

## Acknowledgements

1. **[Demucs](https://github.com/adefossez/demucs)** — The stem splitting functionality is built upon the work of [@adefossez](https://github.com/adefossez).
2. **[librosa](https://librosa.org/)** — For foundational audio processing tools.
3. **[@nanaoto](https://github.com/nanaoto)** — For building the `mir_eval` benchmarking infrastructure and IDMT-SMT-Drums V2 adapter (PR [#273](https://github.com/DrumScript/DrumScript/pull/273)).

---

## License

[Apache License 2.0](LICENSE)

---
## Similar Projects

*[back](#drumscript)*

DrumScript has no affiliation with any of the projects below. They are listed for context and reference.

* **[librosa](https://librosa.org/)** — The spectral analysis library that powers DrumScript's onset detection and feature extraction.
* **[Demucs](https://github.com/adefossez/demucs)** — The stem separation model we use for isolating drums from full mixes.
* **[tepreece/drumscript (Golang)](https://github.com/tepreece/drumscript)** — A `(Go)lang` MIDI drum pattern scripting language by Tom Preece. Different use case (composing drum patterns via script), different technology (MIDI output rather than audio transcription). If you're looking to *write* drum patterns programmatically, check it out. Maintained by [@tepreece](https://github.com/tepreece)
* **[basic-pitch](https://github.com/spotify/basic-pitch)** — A lightweight yet powerful audio-to-MIDI converter with pitch bend detection (better for non-percussive audio). Maintained by Spotify.
* **[mir_eval](https://github.com/mir-evaluation/mir_eval)** — Standard evaluation metrics for music information retrieval tasks.
* **[onset_db](https://github.com/CPJKU/onset_db)** - Provides a dataset of annotated musical onsets for tuning and evaluating audio detection algorithms. Maintained by JKU Linz.

---

<!--END-->