# CLI Reference

This page details all available arguments and flags for the `drumscript` command-line tool.

## Main Command
**Usage:**
```bash
python -m drumscript.main [INPUT_AUDIO] [OPTIONS]

```

## Arguments

### Positional Arguments

* **`input_audio_path`**
Path to the input audio file (`.wav` or `.mp3`).

### Options

* **`--full`**
Transcribe the full song. Automatically separates drums from the mix before transcription.
* **`--drumless`**
Generate a drumless backing track (removes drums from the mix).
* **`--ts <SIGNATURE>`**
Set the time signature (default: `4/4`).
* *Example:* `--ts 3/4`


* **`--all-stems`**
Export all individual stems (Drums, Bass, Vocals, Other).
* **`--mute <STEM>`**
Mute a specific stem. Can be used multiple times.
* *Example:* `--mute bass --mute vocals`
