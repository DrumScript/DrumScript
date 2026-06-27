# Stem-Splitter

<!--date_createdthurs-07-may-2026-->
<!--date_updated:sat-27-june-2026-->

---

## How does the stem-splitter module (`audio_processor/stem_splitter.py`) work?

In simple terms, the **stem-splitter** takes a full polyphonic song and pulls it apart into its individual instrumental layers — drums, bass, vocals, and "other" — using the **Demucs** source separation model. From there, those isolated layers can be saved individually, recombined into custom mixes (e.g. a drumless backing track), or fed into the rest of the DrumScript transcription pipeline.

Here's a more detailed breakdown of what it does and why it's designed this way.

### What the Module Does

1.  **Receives a full audio mix** — any `.wav` or `.mp3` file containing a complete song.

2.  **Runs Demucs in a subprocess**, using the high-quality 4-stem `htdemucs` model. Calling Demucs via its CLI (rather than importing it as a Python library) keeps Demucs's heavy dependencies (PyTorch, torchaudio, torchcodec) outside the core DrumScript Python process.

3.  **Demucs writes four raw WAV stems to a temporary directory:** `drums.wav`, `bass.wav`, `vocals.wav`, and `other.wav`.

4.  **Reads each stem back in as a NumPy array** using `soundfile`. This step is deliberately ffmpeg-free for WAV — only the MP3 export path further down ever needs ffmpeg.

5.  **Decides what to do with the stems**, based on which flags were passed:
    - `drumless=True` → mix every stem **except** drums into a backing track, and save the drums stem on its own.
    - `mute=["bass"]` (or any other stem) → mix everything except the muted stem(s); save the muted stem(s) separately.
    - `all_stems=True` → export every individual stem as its own file.
    - **No flags** → default behaviour: just save the isolated drum stem (this is what the transcription pipeline uses internally when `full_song=True`).

6.  **Mixes stems where needed** by summing the NumPy arrays sample-by-sample (via the internal `mix_stems` helper) and clipping the result to the valid `[-1, 1]` range to prevent overflow.

7.  **Writes outputs in the requested format.** WAV writes go through `soundfile` (no ffmpeg). MP3 writes go through `pydub`, which shells out to ffmpeg's LAME encoder.

8.  **Cleans up the temporary Demucs directory** and returns a dictionary of paths to every generated file.

### Why This Approach

DrumScript uses Demucs as a **pre-processor**, not as part of its own classification engine. This separation of concerns is deliberate:

- **Source separation and drum classification are different problems.** Isolating a drum track from a polyphonic mix requires learning what "drums" sound like across many recording conditions, kits, and genres — a problem deep learning solves well. Drum *classification* (kick vs snare vs hi-hat etc.), by contrast, is a problem DrumScript solves with deterministic, physics-based rules.

- **Demucs is treated as a black box that produces a WAV file.** From DrumScript's perspective, the output of the stem-splitter is just another audio file. Everything downstream — onset detection, feature extraction, classification, score-building — runs on that file deterministically.

#### Key design choices

- **Demucs is invoked via subprocess CLI, not imported as a Python module.** Demucs's heavy ML dependencies (PyTorch, torchaudio, torchcodec) don't have to be loaded into the Python process for every DrumScript call. This keeps DrumScript light to install and quick to import.

- **WAV output is ffmpeg-free.** Demucs writes WAV by default; `soundfile` reads and writes WAV natively. A user on a WAV-only workflow never needs ffmpeg on their system.

- **MP3 output is opt-in.** MP3 routes through `pydub` (which shells out to ffmpeg), so ffmpeg only becomes a requirement if the user explicitly asks for MP3 output.

#### A note on Demucs's long-term maintenance

The original Demucs project is no longer actively maintained by its original owners (Meta). Alexandre Défossez maintains an occasional [fork](https://github.com/adefossez/demucs). To insulate DrumScript against potential dependency drift, the project may eventually replace Demucs with its own lightweight stem-splitter — but for now, Demucs remains the simplest, highest-quality option available.

---

<!--END-->
