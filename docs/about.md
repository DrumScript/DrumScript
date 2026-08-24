# About DrumScript

<!--date_updated:tues-30-dec-2025-->
<!--date_updated:mon-24-aug-2026-->

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

**DrumScript** is an open-source Python library and CLI tool for drum audio analysis and transcription. Give it a recording — a full mix or an isolated drum stem — and it will generate PDF sheet music, MIDI files, and MusicXML output. The `DrumScript` model is a **deterministic classifier**, and doesn't use AI/machine learning. Built for drummers and by drummers, it is - and always will be - an open-source community tool. The alpha has been running since **01 June 2026** and will be ongoing until we make the model and transcription process more accurate. 

**Disclaimer**
> * `DrumScript` is developed by part-timers who have full-time jobs and, like most modern software, it's built with the help of good tooling and occasional use of LLM for debugging and refining website content, but all the decisions are human-reviewed more than once at every step.
> * The deterministic classification model (classify.py) has been built from a relatively small dataset covering different genres, but with a notable focus on **fast-paced, technical death metal** songs and drumming
> * The prioritisation of speed versus accuracy means the score generation needs work. 
> * Moreover, as our [roadmap](./docs/guide/roadmap.md) points out, increasing DrumScript's accuracy for all genres and drumming styles, including better score generation is an important long-term goal
> * The core classification model does NOT use machine learning in classifying onset_events into drum parts. This is what makes the DrumScript package unique: it uses physics-only derived and measured inputs based on the individual features of each part of the drumkit. 
> * The PDF generation uses ReportLab to build a custom PDF; it does not use librosa or MuseScore
> * Accuracy of onset detection, sonic properties of deterministic model and score generation are the three main areas we need to improve. 
> * `GitActions[Bot]` is used in the automated daily workflow that gathers repository statistics: [**repo-stats**](https://github.com/DrumScript/DrumScript/blob/github-repo-stats/DrumScript/DrumScript/latest-report/report.pdf)
> * If you feel any part of this hasn't been made clear, then please raise it in the **[Discussions](https://github.com/orgs/DrumScript/discussions)**

> **Python >=3.9, < 3.13**