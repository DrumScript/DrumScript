# About DrumScript

## The Origin Story
**DrumScript was born from a simple frustration: sheet music for drums is inaccessible.**

For piano or guitar, converting MIDI to notation is a solved problem. But for drummers, the landscape is different. Most "transcription" tools are black boxes that cost money, require cloud uploads, or output messy MIDI files that look nothing like standard drum notation.

As a drummer, I wanted a tool that could listen to a track and hand me a chart I could actually read on the stand. I didn't want a "piano roll" — I wanted a **score**.

When I couldn't find a free, open-source tool that prioritised *readability* over raw MIDI data, I decided to build one.

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
DrumScript is currently in **Alpha (v0.1.2)**. We are looking for contributors who are passionate about audio, music, or Python.

* Check out the [GitHub Repository](https://github.com/DrumScript/DrumScript)
* Read the [Contribution Guide](development/contributor_guidance)