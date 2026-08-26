# **DrumScript CLI Reference**

<!--date_added:sat-20-june-2026-->
<!--date_updated:weds-25-aug-2026-->

This document provides a comprehensive guide to the command-line interface for **DrumScript**. The primary entry point is the `drumscript` console command, while individual modules can be run standalone for development and testing purposes.

## **Primary Orchestrator**

Installing DrumScript provides a `drumscript` command that orchestrates the end-to-end run, including stem separation, analysis, and score generation.

### **Usage**

```bash
drumscript <audio_path> [options]
```

Equivalent forms, useful when working from a clone without installing:

```bash
python -m drumscript.main <audio_path> [options]
python drumscript/main.py <audio_path> [options]     # only from the repo root
```

### **Positional Arguments**

* **`audio_path`**: The file path to the audio file (e.g., `.mp3`, `.wav`) you wish to process.

### **Transcription Options**

* **`--full-song`**: Instructs the pipeline to isolate the drum stem using Demucs before proceeding with transcription.

### **Stem Separation Options**

* **`--drumless`**: Extracts a drumless backing track from the source audio.
* **`--mute <stem>`**: Mutes specific stems (e.g., `bass`, `vocals`, `other`). This flag can be used multiple times in a single command.
* **`--all-stems`**: Exports all individual raw stems to the output directory.
* **`--format {wav,mp3}`**: Sets the output format for the stems. Defaults to `wav`.

### **Classification Options**

* **`--rudiment`**: Optimises classification for isolated single beats, rudiments, or paradiddles by applying dynamic transient gating. Use this for single-hit samples and practice-pad recordings rather than full grooves.

### **Notation Options**

* **`--ts <signature>`**: Defines the time signature for the generated drum score. Defaults to `4/4`. Use a forward slash (`3/4`, `6/8`) - any other form, including underscores like `3_4`, silently falls back to 4/4.

---

## **Development & Module-Level Commands**

Developers can run specific modules directly to test isolated components of the signal processing chain.

### **Audio Loader**

Used to verify audio loading and peak normalization.

```bash
python -m drumscript.audio_processor.audio_loader <audio_file_path>
```

### **Tempo Detector**

Estimates the BPM of a specific audio file using the tempogram-first method.

```bash
python -m drumscript.audio_processor.tempo_detector <audio_file_path>
```

### **Stem Splitter (Standalone)**

Directly triggers the Demucs-based separation engine.

```bash
python -m drumscript.audio_processor.stem_splitter <file> [--drumless] [--mp3] [--all]

```

* **`--mp3`**: Sets the output format to MP3 (standalone version uses `--mp3` instead of `--format mp3`).
* **`--all`**: Exports all stems.

### **Onset Detector**

Primarily used for internal verification of the HPSS-based onset detection.

```bash
python -m drumscript.audio_processor.onset_detector <audio_file_path>
```

---

## **Examples**

**1. Transcribe a drum-only recording:**

```bash
drumscript "drum_loop.wav"
```

Writes `<name>_transcription.pdf`, `.json` and `.mid` to `outputs/`.

**2. Transcribe a full song into sheet music (isolating drums first):**

```bash
drumscript "audio_path.mp3" --full-song
```

**3. Generate a drumless backing track in MP3 format:**

```bash
drumscript "audio_path.wav" --drumless --format mp3
```

**4. Transcribe a drum solo with a custom time signature:**

```bash
drumscript "audio_path.wav" --ts "7/8"
```

**5. Classify a single rudiment or practice-pad sample:**

```bash
drumscript "paradiddle.wav" --rudiment
```

**6. Export all four stems:**

```bash
drumscript "audio_path.mp3" --all-stems --format mp3
```