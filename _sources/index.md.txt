# `DrumScript` Documentation
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1eDVXc3d6ezmorxINOjzldRPSC3emTl2I)

**DrumScript** is an open-source Python library and CLI tool designed for drummers and audio engineers.  DrumScript's classification engine is **deterministic**. While its core mission is **Automatic Drum Transcription (ADT)** (converting drum recordings into sheet music), it also functions as a powerful **Audio Toolbox** for extracting drums from polyphonic tracks, creating backing tracks, and analysing rhythm.

| # | Feature | What it does |
|---|---------|-------------|
| 1 | **Tempo Detection** | `DrumScript` stimates BPM from drum audio file based on tempogram-anaysis |
| 2 | **Stem Separation** | Extracts drums from `.wav` and `.mp3`^ songs. Also supports extraction of bass, vocals, and other instruments |
| 3 | **Backing Tracks** | Give `DrumScript` a song and it will mute the drums to create a backing track for you|
| 4 | **Transcription** | `DrumScript` converts drum audio → PDF sheet music . The --full flag also means you can give it a full song and it will extract the drums **and** transcribe|

^ `.mp3` requires `.ffmpeg` (`brew install ffmpeg`)
Unlike most ADT systems, DrumScript's classification engine is **deterministic**. `DrumScript` combines physics-derived spectral analysis: fundamental frequency, spectral centroid, energy ratios, and decay characteristics, applied through a rule-based pipeline built on `librosa` and `Demucs`. It also functions as a general-purpose audio toolbox: stem separation, drumless/bassless backing track generation, and tempo detection. 

The project was born from one working drummer's desire to make playing drums more fun and in an accessible way - it's taken almost a year to build. `v0.1.5` is the **Alpha release**. Between **01 June and 31 August 2026** Im reaching out to communities, both musicians and academics alike, to find people to test  - and hopefully improve - the deterministic classification model. For more info on where this is headed see **[roadmap](guide/roadmap.md)** or **https://github.com/orgs/DrumScript/discussions**

## What can DrumScript do?

### 1. Audio-to-Sheet Music (Transcription)
Give DrumScript a recording of a drum beat, and it will generate a **PDF Score**.
* **Smart Detection:** Uses signal processing to detect Kicks, Snares, and Hi-Hats.
* **Tempo Aware:** Automatically calculates BPM.
* **Customizable:** Supports custom time signatures (e.g., `3/4`, `6/8`).

### 2. Stem Splitting (The "De-Mixer")
Powered by **Demucs** (Hybrid Transformer Source Separation), DrumScript can un-mix a full song.
* **Isolate Drums:** Extract *just* the drum track from a full mix to study the groove.
* **Isolate Bass:** Extract *just* the bass line to practice locking in.
* **Separate Everything:** Explode a song into 4 stems: `Drums`, `Bass`, `Vocals`, `Other`.

### 3. Backing Track Generator
Want to play along to your favorite song but the drums are in the way?
* **Drumless Tracks:** Automatically remove the drums from any `.mp3` or `.wav` to create a play-along track.
* **Bassless Tracks:** Mute the bass to practice your low-end theory.

`DrumScript` is an open-source Python library that converts drum audio (in `.mp3`, or `.wav`) to `.pdf` sheet music. It contains functions for you to **automatically measure tempo of drum-only audio using Tempogram-first principles**. `DrumScript` is unique to any other library because **we do not use machine learning or AI**. Our classification approach is a **deterministic** one. 

`DrumScript` also **extracts** drum audio from **any** `.mp3` or `.wav` audio file for you. Give it your favourite track, and it will do the job of extracting **just the drum audio** and then transcribe into handy `.pdf` sheet music. There **stem-splitter** functionality also extracts, optionally, the **non-drum-parts** of an audio track and provides it as a **backing track** for all you aspiring drummers and percussionists to play along to. 

> We are currently working on academic papers related to the deterministic method(s) used and will publish here in future
> There is also the plan to integrate the **backing track extraction**, **drum only extraction**, **tempo detection** and **classification** functions to a free-to-use UI that does not require login or store any of your uploads, nor their resultant outputs. More information will be provided soon! 
> In the meantime, if you would like to be involved, get in touch! 🥁🚀 

`DrumScript` was built for drummers, by drummers. It is - and always will be - a community-owned tool. 


**Example output**

![alt text](_static/transcription.png)

---

## Getting Started

```{toctree}
:maxdepth: 1
:caption: Getting Started

guide/installation
```

## User Guide

```{toctree}
:maxdepth: 1
:caption: User Guide

guide/cli_reference
guide/configuration
guide/usage
guide/glossary
guide/roadmap
guide/security
guide/usage
```

## Theory

```{toctree}
:maxdepth: 1
:caption: Theory

theory/drum_notation_guide
theory/digital_signal_processing
theory/tempo_estimation
theory/stem_splitting
theory/how_it_works
theory/percussion_frequencies
theory/bibliography
theory/sources
```

## API Reference

```{toctree}
:maxdepth: 1
:caption: API Reference

api
```

## Development

```{toctree}
:maxdepth: 1
:caption: Development

development/code_of_conduct
development/contributor_guidance
development/documentation
development/testing_guidance
```


## Runbooks

```{toctree}
:maxdepth: 2
:caption: Runbooks

guide/interactive/index
```
## About

```{toctree}
:maxdepth: 1
:caption: Project Info
about
```
## Release Notes


```{toctree}
:maxdepth: 1
:caption: Versions

release_notes/index

```