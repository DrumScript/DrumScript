# About

<!--date_created: Fri-25-Oct-2025-->
<!--date_updated: Weds-14-Jan-2026-->

DrumScript is an open-source `Python` library and suite of tools intended to make music more accessible for everyone. The Python package alpha is released alongside a free-to-use engine for members of the musical and sound analysis/engineering community to use in a zero-code way.

> #### **[hello.drumscript@gmail.com](hello.drumscript@gmail.com)**

---
## Features

* **Audio Input:** Supports common audio formats like `.wav` and `.mp3`.
* **Advanced Tempo Detection:** Estimates the tempo (BPM) of an audio file. A deterministic algorithm for tempo estimation. Analyses the entire audio file (not just local beats) to generate a "Tempogram." Conducts a "tempo election" to find the most consistent BPM, effectively handling complex syncopation and ghost notes where standard metronomes fail.
* **Drum Hit Detection:** Identifies the precise timing of drum strikes using onset event detection algorithms.
* **Audio Extractor:** We utilise the state-of-the-art [Demucs](https://github.com/adefossez/demucs) source separation model to provide high-quality drum extraction so users can separate audio files into their drum, guitar, base guitar and vocal stems. 
* **UI Integration:** Connect the package to a free-to-use public web interface.
* **Stem Splitting**: Automatically isolate drum tracks from full audio mixes using the `demucs` hybrid transformer model.
* **Onset Detection**: Precise identification of drum hits using spectral analysis.
<!--* **Classification**: Rule-based engine to classify hits (Snare, Kick, Hi-Hat) based on acoustic features.-->
<!--* **Score Generation**: Export transcribed drums to `.pdf` sheet music and `.xml` formats.-->



---

<!--END-->