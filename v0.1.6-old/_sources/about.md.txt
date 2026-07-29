# About DrumScript

<!--date_updated:tues-30-dec-2025-->
<!--date_updated:fri-22-may-2026-->

---

## The Origin Story
**DrumScript was born from a simple frustration: sheet music for drums is inaccessible.**

For piano or guitar, converting MIDI to notation is a solved problem. But for drummers, the landscape is different. Most "transcription" tools are black boxes that cost money, require cloud uploads, or output messy MIDI files that look nothing like standard drum notation. As a drummer, I wanted a tool that could listen to a track and hand me a chart I could actually read on the stand. I didn't want a "piano roll" — I wanted a **score**.

When I couldn't find a free, open-source tool that prioritised *readability* over raw MIDI data, I decided to build one. Over time I became really interested in **Digital Signal Processing (DSP)**, **Sound Engineering** and **Automatic Transcription** in both theory and practise.  I discovered the field of **Music Information Retrieval**, communities like **[International Society for Music Information Retrieval (ISMIR)](https://ismir.net/)**, and so have a working interest in the theory of these fields.

Above all I built this tool to fix a problem I had never found a free and easily-accessible solution to as a fellow drummer.

## The Mission
DrumScript is built on three core philosophies:

1.  **Accessibility First:** Music education shouldn't be paywalled. The core engine of DrumScript will always be free and open-source.
2.  **Notation Over Data:** We don't just output data; we output *music*. We care about the difference between a "Ghost Note" and a standard hit.
3.  **Local & Private:** You shouldn't have to upload your creative stems to a third-party server to get a transcription. DrumScript runs locally on your machine.

## How It Works
DrumScript bridges the gap between **Signal Processing (DSP)** and **Music Theory**.

* It uses **Demucs** (Meta's state-of-the-art source separation model) to isolate drums from mixed audio.
* It uses **Librosa** for onset detection (finding *when* a drum was hit).
* It uses a custom **Rule-Based Classification Engine** to determine *what* was hit (Kick vs. Snare vs. Hi-Hat) based on frequency analysis.

## Join the Project
DrumScript is currently in **Alpha**. We are looking for contributors who are passionate about audio, music, or Python.

Check out the [GitHub Repository](https://github.com/DrumScript/DrumScript) or the [Contributor Guide](./development/contributor_guidance.md)

`DrumScript` could be potentially useful (and developed by):

* Drummers who want to transcribe their playing automatically
* Music tech / audio-ML developers
* Python open-source community
* Music educators
* Beat-makers / producers who want stems
* Drummers! :drum:

**hello.drumscript@gmail.com**

Please also get involved at: **[Discussions](https://github.com/orgs/DrumScript/discussions)**