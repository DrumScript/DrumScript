# Contributing to `DrumScript`

<!--date_added:sun-10-may-2026->
<!--date_updated:weds-25-aug-2026-->

> This is a **summarised version** 
> **Full contributor guide:** [docs/development/contributor_guidance.md](docs/development/contributor_guidance.md)

---

We welcome contributions! DrumScript is intended to be a community-owned project. You can also refer to detailed contributor guidance **[here](./docs/development/contributor_guidance.md)**

All bug reports and feature requests must be filed as GitHub Issues. All code changes must be submitted as [Pull Requests](https://github.com/DrumScript/DrumScript/pulls). Keeping discussion public helps everyone.


- **[Open an Issue](https://github.com/DrumScript/DrumScript/issues/new)** for bugs or feature requests.
Please use the links below to submit your input:

  - **[Report a Bug](https://github.com/DrumScript/DrumScript/issues/new?template=bug_report.yml)**: Tell us if something is broken or behaving unexpectedly.
  - **[Request a Feature](https://github.com/DrumScript/DrumScript/issues/new?template=feature_request.yml)**: Suggest a new capability or improvement.
  - **[Submit Results](https://github.com/DrumScript/DrumScript/issues/new?template=submit_results.yml)**: Share a DrumScript output file to help improve the model or score generation.

- **[Submit a Pull Request](https://github.com/DrumScript/DrumScript/pulls)** for code changes.



- **[Discussions](https://github.com/orgs/DrumScript/discussions)** for discussions

---


<!--Thanks for your interest in contributing!-->

**Quick start:**

```bash
git clone https://github.com/DrumScript/DrumScript.git
cd DrumScript
uv venv && source .venv/bin/activate && uv sync --extra dev
pytest -m "not slow"
```

Please see Issues tab for full list of development opportunities; or feel free to add your own.


## Similar Projects

No affiliation as yet, however. 
w
**[librosa](https://librosa.org/)** - The spectral analysis library that powers DrumScript's onset detection and feature extraction.
**[Demucs](https://github.com/adefossez/demucs)** - The stem separation model we use for isolating drums from full mixes.
**[tepreece/drumscript (Golang)](https://github.com/tepreece/drumscript)** - A `(Go)lang` MIDI drum pattern scripting language by Tom Preece. Different use case (composing drum patterns via script), different technology (MIDI output rather than audio transcription). If you're looking to *write* drum patterns programmatically, check it out. Maintained by [@tepreece](https://github.com/tepreece)
**[basic-pitch](https://github.com/spotify/basic-pitch)** - A lightweight yet powerful audio-to-MIDI converter with pitch bend detection (better for non-percussive audio). Maintained by Spotify.
**[mir_eval](https://github.com/mir-evaluation/mir_eval)** - Standard evaluation metrics for music information retrieval tasks.
**[onset_db](https://github.com/CPJKU/onset_db)** - Provides a dataset of annotated musical onsets for tuning and evaluating audio detection algorithms. Maintained by JKU Linz.

## Releases

Releases are handled by maintainers. The tag format is `vX.Y.Z` (e.g. `v0.2.0`). The version is defined in `drumscript/__init__.py` and propagates automatically to `pyproject.toml`, documentation, and PyPI.

**We are currently looking to add new maintainers!** If you are interested in becoming a maintainer, please contact admins at hello.drumscript@gmail.com! 

---

<!--END-->