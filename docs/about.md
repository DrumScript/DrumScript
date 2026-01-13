# About

<!--date_created:Fri-25-Oct-2025-->
<!--date_updated:Tues-30-Dec-2025-->


---

`DrumScript` is a Python **classification engine** and **transcription tool**.

It takes audio inputs in various formats (`.wav`, `.mp3`)—ranging from raw drum recordings to full musical mixes. By utilizing advanced **stem splitting** technology, it isolates the drum track before passing it to the classification engine.

The core function is to **transcribe this audio** into `.pdf` drum sheet music, making drum notation accessible to everyone.

---


Video Explanation of `stem splitting` using Demucs (for your reference): [Music Source Separation with Demucs](https://www.google.com/search?q=https://www.youtube.com/watch%3Fv%3D4C4Xr6T3_fI)

This video provides a visual and technical explanation of how the underlying technology (Demucs) separates instruments from a mix, which is the core of the`StemSplitter` class, ie how `DrumScript Lite` extracts audio from polyphonic tracks.

---

<!--END-->