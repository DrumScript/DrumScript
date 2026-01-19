# **DrumScript CLI Reference**

This document provides a comprehensive guide to the command-line interface for **DrumScript**. The primary entry point for the full pipeline is `main.py`, while individual modules can be run standalone for development and testing purposes.

## **Primary Orchestrator (`main.py`)**

The `main.py` script orchestrates the end-to-end running of DrumScript, including stem separation, analysis, and score generation.

### **Usage**

```bash
python drumscript/main.py <audio_path> [options]
```

### **Positional Arguments**

* **`audio_path`**: The file path to the audio file (e.g., `.mp3`, `.wav`) you wish to process.

### **Transcription Options**

* **`--full`**: Instructs the pipeline to isolate the drum stem using Demucs before proceeding with transcription.

### **Stem Separation Options**

* **`--drumless`**: Extracts a drumless backing track from the source audio.
* **`--mute <stem>`**: Mutes specific stems (e.g., `bass`, `vocals`, `other`). This flag can be used multiple times in a single command.
* **`--all-stems`**: Exports all individual raw stems to the output directory.
* **`--format {wav,mp3}`**: Sets the output format for the stems. Defaults to `wav`.

### **Notation Options**

* **`--ts <signature>`**: Defines the time signature for the generated drum score. Defaults to `4/4`.

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
python -m drumscript.audio_processor.onset_detector
```

*Note: This standalone command currently uses hardcoded test paths for internal verification.*

---

## **Examples**

**1. Transcribe a full song into sheet music (isolating drums first):**

```bash
python drumscript/main.py "audio_path.mp3" --full
```

**2. Generate a drumless backing track in MP3 format:**

```bash
python drumscript/main.py "audio_path.wav" --drumless --format mp3
```

**3. Transcribe a drum solo with a custom time signature:**

```bash
python drumscript/main.py "audio_path.wav" --ts "7/8"
```