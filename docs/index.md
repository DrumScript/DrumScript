# `DrumScript` Documentation

<!--**`DrumScript`** is a Python suite that converts drum audio into sheet music, as well as provides a range of tools to assist in sound audio manipulation. It leverages audio signal processing and a rule-based classification engine to detect individual drum hits, transcribe them into a **musical score**, and export them as `.pdf` files. -->

`DrumScript` is an open-source Python library that converts drum audio (in `.mp3`, or `.wav`) to `.pdf` sheet music. It contains functions for you to **automatically measure tempo of drum-only audio using Tempogram-first principles**. `DrumScript` is unique to any other library because **we do not use machine learning or AI**. Our classification approach is a **deterministic** one. 

`DrumScript` also **extracts** drum audio from **any** `.mp3` or `.wav` audio file for you. Give it your favourite track, and it will do the job of extracting **just the drum audio** and then transcribe into handy `.pdf` sheet music. There **stem-splitter** functionality also extracts, optionally, the **non-drum-parts** of an audio track and provides it as a **backing track** for all you aspiring drummers and percussionists to play along to.

> We are currently working on academic papers related to the deterministic method(s) used and will publish here in future
> There is also the plan to integrate the **backing track extraction**, **drum only extraction**, **tempo detection** and **classification** functions to a free-to-use UI that does not require login or store any of your uploads, nor their resultant outputs. More information will be provided soon! 
> In the meantime, if you would like to be involved, get in touch! 🥁🚀 

`DrumScript` was built for drummers, by drummers. It is - and always will be - a community-owned tool. 


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

guide/configuration
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
guide/glossary
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
development/testing_guidance

```

## About

```{toctree}
:maxdepth: 1
:caption: Project Info

about
