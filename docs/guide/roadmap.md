# Roadmap for `DrumScript`

<!--date_created: 2026-05-21-->

> DrumScript follows [Semantic Versioning](https://semver.org/).
> The current phase is **Alpha** (`0.x.y`) — the API is stabilising and breaking changes between minor versions are expected.

---

## Release Phases

| Phase | Versions | Target Window | What to Expect |
|-------|----------|---------------|----------------|
| **Alpha** (current) | `0.1.x` – `0.2.x` | June – August 2026 | Core pipeline works end-to-end. API may change between releases. Feedback actively sought. |
| **Beta** | `0.3.x` – `0.9.x` | September 2026 onwards | API locked for each minor version. Focus on accuracy, edge cases, and evaluation against standard ADT datasets. |
| **Stable** | `1.0.0` | TBD | Public API frozen. Breaking changes only in major versions. Formal write-up targeting TISMIR. |

---

## Alpha Priorities (v0.1 – v0.2)

**What works today:**

- End-to-end transcription pipeline: audio → onsets → classification → PDF / MIDI / MusicXML
- Tempo detection via spectral onset envelope
- Stem separation using Demucs (`htdemucs` 4-stem model)
- Drumless backing track generation
- CLI and Python API
- Colab demo notebook

**What we're focused on during the alpha:**

- Expanding test coverage across genres, kit types, and recording conditions
- Fixing classification edge cases (deep snares vs clicky kicks, splash cymbals vs open hats)
- Improving onset detection sensitivity for ghost notes and fast passages
- Stabilising the public API ahead of the beta freeze
- Community feedback collection

---

## Planned — Beta and Beyond

### Smarter classification across genres and kits

The current frequency thresholds were derived from a small sample set and are essentially absolute values — they work well for a typical rock/pop kit but can struggle with jazz kits, piccolo snares, deep floor toms, and non-standard tunings.

The plan is to introduce a **per-track calibration step**: before the deterministic classifier runs, DrumScript would first characterise the kit as a whole (identify the frequency clusters present in a given track) and then classify hits relative to those clusters, rather than relying on fixed Hz bands. The working theory is that all drum kits have relative frequency relationships regardless of absolute tuning — making the system far more genre-agnostic.

### Richer organological modelling

Building out the classification taxonomy along the membranophone/idiophone divide:

- Better separation of tom voices (floor, mid, rack)
- Recognition of cymbal subtypes (splash, china, bell hits vs edge hits)
- Hi-hat gradations beyond open/closed (half-open, foot splash, pedal chick)

### Dynamics and advanced technique

The alpha treats every hit as equal. Future versions should handle:

- Accents and ghost notes
- Different beater styles (stick tip vs shoulder, brush sweeps, mallet rolls)
- Expressive techniques critical for accurate transcription and meaningful notation

### Broader stem separation uses

The Demucs integration currently targets drummers, but the same pipeline can produce vocal-only, bass-only, or instrument-only extractions. These will be exposed as first-class features so the tool is useful to vocalists, bassists, and producers — not just drummers.

### Browser-based zero-code UI

A major goal: a browser deployment using WebGPU, WebAssembly, Pyodide, and ONNX Runtime so that DrumScript can run entirely client-side — no installation, no server, no account, no data leaves the user's machine. The aim is a free, local-input/local-output tool that non-technical musicians can use without touching a terminal.

### Formal evaluation and paper

Benchmarking against standard ADT datasets using `mir_eval` metrics, with a write-up targeting the [TISMIR](https://transactions.ismir.net/) Educational Articles track covering the pipeline architecture, evaluation results, and design decisions.

---

## How to Get Involved

- **Report bugs or edge cases:** [GitHub Issues](https://github.com/DrumScript/DrumScript/issues)
- **Suggest features:** [Feature Request template](https://github.com/DrumScript/DrumScript/issues/new?template=feature_request.md)
- **Contribute code:** See [Contributing](../development/contributor_guidance.md)
- **Share feedback:** [hello.drumscript@gmail.com](mailto:hello.drumscript@gmail.com)
