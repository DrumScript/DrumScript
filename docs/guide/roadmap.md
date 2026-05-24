# Roadmap for `DrumScript`

<!--date_created: thurs-21-may-2026-->
<!--date_updated: sun-24-may-2026-->

> DrumScript follows [Semantic Versioning](https://semver.org/).
> The current phase is **Alpha** (`0.1.5`) — the classification model and score generation/ API is out for testing. 
> From **01 June 2026 to 31 August** alpha testing is under way.

* **[Release plan](#release-phases)**
    - **[Alpha priorities](#alpha-priorities-v030--v090)**
    - **[Beta](#beta-priorities-09x--099)**
    - **[Stable version (v1.0.0) and beyond](#stable-version-100-and-beyond)**
* **[How to get involved](#how-to-get-involved)**

---

## Release Plan

| Phase | Versions | Target Window | What to Expect |
|-------|----------|---------------|----------------|
| **Pre-Alpha** | `0.1.0` – `0.9.0` | June 2025 - May 2026 | Core pipeline works end-to-end. API may change between releases. Built in isolation |
| **Alpha** (current) | `0.1.0` – `0.9.0` | **June – August 2026** | Core pipeline works end-to-end. API may change between releases. Feedback sought. Cross off some of the **[Issues](https://github.com/DrumScript/DrumScript/issues)** added in pre-Alpha |
| **Beta** | `0.9.x` – `0.9.9` | September 2026 onwards | API locked for each minor version. Focus on accuracy, edge cases, and evaluation against standard ADT datasets.  Release **free-to-use** `WebGPU/WASM/ONNX` UI for non-coders|
| **Stable** | `1.0.0` | *tbc* | Public API frozen. Breaking changes only in major versions. Community-owned tool. Publication of paper in journal to announce release |


**What works today:**

- End-to-end transcription pipeline: audio → onsets → classification → PDF / MIDI / MusicXML
- Tempo detection via spectral onset envelope
- Stem separation using Demucs (`htdemucs` 4-stem model)
- Drumless backing track generation
- CLI and Python API
- Colab demo notebook

---

### Alpha Priorities (v0.3.0 – v0.9.0)

**What we're focused on during the alpha:**

- Expanding test coverage across **genres**, **kit types**, and **recording conditions**
- Fixing **deterministic classification** edge cases (deep snares vs clicky kicks, splash cymbals vs open hats)
- Improving onset detection sensitivity for ghost notes and fast passages
- Improve transcription notations, known bugs: ie note tails that dont mark up with note head, review cosmetic looks
- Fix time signatures and ensure the transcription timing is correct to semi-quaver
- Improving **Demucs** stem-separation quality outputs
- Community feedback from fellow drummers, audio, engineers and the TISMIR/MIR community

### Beta Priorities `0.9.x` – `0.9.9`

**Immediately prior to release of DrumScript v1.0.0 some goals will be small fixes to ensure robustness, testing the UI, integrating the UI with current CI/CD pipelines**

### Stable Version `1.0.0` and Beyond 

1. **Smarter classification across genres and kits**

* The current frequency thresholds were derived from a small sample set and are essentially absolute values — they work well for a typical rock/pop kit but can struggle with jazz kits, piccolo snares, deep floor toms, and non-standard tunings.

* The plan is to introduce a **per-track calibration step**: before the deterministic classifier runs, DrumScript would first characterise the kit as a whole (identify the frequency clusters present in a given track) and then classify hits relative to those clusters, rather than relying on fixed Hz bands. 

The working theory is that all drum kits have relative frequency relationships regardless of absolute tuning — making the system far more genre-agnostic.

2. **Richer organological modelling**

Building out the classification taxonomy along the `membranophone` (snares, toms, etc) and `idiophone` (cymbals, hats, etc) classification ontology:

* Better separation of tom voices (floor, mid, rack)
* Recognition of cymbal subtypes (splash, china, bell hits vs edge hits)
* Hi-hat gradations beyond open/closed (half-open, foot splash, pedal chick)

3. **Dynamics and advanced technique**

The alpha treats every hit as equal. Future versions should handle:

* Accents and ghost notes
* Different beater styles (stick tip vs shoulder, brush sweeps, mallet rolls)
* Expressive techniques critical for accur  FIX 1: Restored minimal noise gate (2% of global max) in classify_events.
         Dead silence was passing through and generating phantom events.
  FIX 2: Aligned ride/crash centroid threshold from 2500 → 5500 in classify_events,
         matching classify_idiophone standalone function. 2500 was causing massive
         crash over-detection (859 crashes in TGOO transcription).
  FIX 3: Added minimal de-bounce lockout (50ms) in classify_events for full-song mode.
         Duplicate timestamps were appearing because consecutive onsets on the same
         transient were both being classified.ate transcription and meaningful notatio

4.  Broader stem separation uses

The Demucs integration currently targets drummers, but the same pipeline can produce vocal-only, bass-only, or instrument-only extractions. These will be exposed as first-class features so the tool is useful to vocalists, bassists, and producers — not just drummers.

5. Browser-based zero-code UI

A major goal: a browser deployment using WebGPU, WebAssembly, Pyodide, and ONNX Runtime so that DrumScript can run entirely client-side — no installation, no server, no account, no data leaves the user's machine. The aim is a free, local-input/local-output tool that non-technical musicians can use without touching a terminal.

6. Formal evaluation and paper

Benchmarking against standard ADT datasets using `mir_eval` metrics, with a write-up targeting the [TISMIR](https://transactions.ismir.net/) Educational Articles track covering the pipeline architecture, evaluation results, and design decisions.

---

## How to Get Involved

- **Report bugs or edge cases:** [GitHub Issues](https://github.com/DrumScript/DrumScript/issues)
- **Suggest features:** [Feature Request template](https://github.com/DrumScript/DrumScript/issues/new?template=feature_request.md)
- **Contribute code:** See [Contributing](../development/contributor_guidance.md)
- **Share feedback:** [hello.drumscript@gmail.com](mailto:hello.drumscript@gmail.com)
- **Start a public discussion:** [Discussions](https://github.com/DrumScript/DrumScript/discussions)


## Similar Projects

No affiliation as yet, however. 

* **[librosa](https://librosa.org/)** — The spectral analysis library that powers DrumScript's onset detection and feature extraction.
* **[Demucs](https://github.com/adefossez/demucs)** — The stem separation model we use for isolating drums from full mixes.
* **[tepreece/drumscript (Golang)](https://github.com/tepreece/drumscript)** — A `(Go)lang` MIDI drum pattern scripting language by Tom Preece. Different use case (composing drum patterns via script), different technology (MIDI output rather than audio transcription). If you're looking to *write* drum patterns programmatically, check it out. Maintained by [@tepreece](https://github.com/tepreece)
* **[basic-pitch][**https://github.com/spotify/basic-pitch]** - A lightweight yet powerful audio-to-MIDI converter with pitch bend detection (better for non-percussive audio)
* **[mir_eval](https://github.com/mir-evaluation/mir_eval)** — Standard evaluation metrics for music information retrieval tasks.
* **[onset_db](https://github.com/CPJKU/onset_db)** - Provides a dataset of annotated musical onsets for tuning and evaluating audio detection algorithms. Maintained by JKU Linz.

---