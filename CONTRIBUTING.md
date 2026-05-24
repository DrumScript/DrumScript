# Contributing to `DrumScript`

<!--date_added:2026-05-10-->
<!--date_updated:2026-05-23-->

> This is a **summarised version** 
> **Full contributor guide:** [docs/development/contributor_guidance.md](docs/development/contributor_guidance.md)

---

Thanks for your interest in contributing!

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

**[librosa](https://librosa.org/)** — The spectral analysis library that powers DrumScript's onset detection and feature extraction.
**[Demucs](https://github.com/adefossez/demucs)** — The stem separation model we use for isolating drums from full mixes.
**[tepreece/drumscript (Golang)](https://github.com/tepreece/drumscript)** — A `(Go)lang` MIDI drum pattern scripting language by Tom Preece. Different use case (composing drum patterns via script), different technology (MIDI output rather than audio transcription). If you're looking to *write* drum patterns programmatically, check it out. Maintained by [@tepreece](https://github.com/tepreece)
**[basic-pitch][**https://github.com/spotify/basic-pitch]** - A lightweight yet powerful audio-to-MIDI converter with pitch bend detection (better for non-percussive audio)
**[mir_eval](https://github.com/mir-evaluation/mir_eval)** — Standard evaluation metrics for music information retrieval tasks.
**[onset_db](https://github.com/CPJKU/onset_db)** - Provides a dataset of annotated musical onsets for tuning and evaluating audio detection algorithms. Maintained by JKU Linz.

---

<!--END-->