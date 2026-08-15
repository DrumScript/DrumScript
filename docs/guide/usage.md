# Usage Guide

<!--date_updated:sat-17-january-2026-->
<!--date_updated:sat-15-august-2026-->

## Quick Start

<!--`DrumScript` accepts the default format of `.wav` if the `--mp3` flag is not specified.-->

### 1. **Audio Loading**
 
Load and normalise audio files for analysis. The `load_audio` handles mono conversion and peak normalisation automatically.

```python
import drumscript as ds
load_audio = ds.load_audio("audio_path.wav") # 1. Load your audio into an .env
```

<!--#### **Audio Loading**

Load and normalise audio files for analysis. The `load_audio` handles mono conversion and peak normalisation automatically.

```python
import drumscript as ds
from drumscript.audio_processor.audio_loader import load_audio
# Load audio (returns audio time series and sample rate)
y, sr = ds.load_audio("audio_path.wav") 
```-->

### 2. **Extract Drums From Any Song**

Want to isolate the drums in your favourite song?

```python
import drumscript as ds
extract_drums = ds.extract_drum_stem("audio_path.wav", output_dir="path_to_output_dir/") # 2. Extract drums from a song and save to local path that you can specify
```

> `DrumScript` will save the output to an `outputs/` folder in your current working directory if `output_dir` is not specified.

### 3. **Create Drumless Backing Track (`--drumless`)**

Want to jam along? Remove the drums from your favourite song:

```zsh
python -m ds.main "audio_path.wav" --drumless 
```

```python
import drumscript as ds
backing_track = ds.main("audio_path.wav", "--drumless")
```
> `DrumScript` will save the output to `outputs/` folder in your current working directory if `output_dir` is not specified.


### 4. Extracting Stems (`--all-stems`)

Split a song into its constituent parts (`Drums`, `Bass`, `Vocals`, `Other`):

```zsh
python -m drumscript.main "audio_path.mp3" --all-stems --format mp3
```

> **PLEASE NOTE:** These stems are defined by `Demucs`

### 5. Custom Time Signatures (`--ts`)

By default, `DrumScript` assumes `4_4` time. You can override this for waltzes or complex meters:

```zsh
# Transcribe a waltz
python -m drumscript.main "audio_path.wav" --ts 3_4

# Transcribe 6_8 time
python -m drumscript.main "audio_path.wav" --ts 6_8

> 
```
<!--You can also use DrumScript directly from your terminal:-->

### 6. Full Audio to PDF Transcription (`--full-song`)

**CLI:**

```zsh
python -m drumscript.main audio_path.mp3 --full-song
```

**Python API:**

```python
import drumscript as ds

# Transcribe an isolated drum stem → PDF + JSON + MIDI
result = ds.transcribe("drum_audio.wav")
print(result["pdf_path"])   # PDF sheet music
print(result["json_path"])  # raw transcription data (JSON)
print(result["midi_path"])  # MIDI file for DAW import

# Transcribe a full song (separates drums automatically)
result = ds.transcribe("full_song.mp3", full_song=True)
print(result["pdf_path"])

# Get all intermediate results (tempo, onsets, events, etc.)
result = ds.transcribe("drum_audio.wav", verbose=True)
print(f"Tempo: {result['tempo']:.1f} BPM")
print(f"Events: {len(result['events'])}")
print(f"PDF: {result['pdf_path']}")
print(f"MIDI: {result['midi_path']}")
```

> **Note (v0.2.0):** `transcribe()` now returns a dict with `pdf_path`, `json_path`, and `midi_path` keys. Using the return value as a plain string (e.g. `pdf = ds.transcribe(...)`) still works but is deprecated and will be removed in v1.0.0. Use `result["pdf_path"]` instead.

> **Full commands**

#### **Audio Transcription**

To run the full transcription pipeline on an audio file, use the main entry point. This will load the audio, separate the drums (if needed), classify hits, and generate a PDF score.

```python
from drumscript.main import main

# Run the full pipeline
main()
# Follow the interactive prompts to provide the input file path.
```

#### **Stem Splitting**

Isolate the drum track from a full music mix using the `StemSplitter` class. This is useful if you want to process the drum audio separately.

```python
from drumscript.audio_processor.stem_splitter import StemSplitter

# Initialise the splitter
splitter = StemSplitter()

# Split the audio file; returns the path to the isolated drum track
drum_track_path = splitter.split_drums(
    input_file="audio_path.mp3",
    output_dir="output/"
)

print(f"Drum stem saved at: {drum_track_path}")
```

#### **Audio Loading**

Load and normalise audio files for analysis. The `load_audio` handles mono conversion and peak normalisation automatically.

```python
import drumscript as ds
from drumscript.audio_processor.audio_loader import load_audio
# Load audio (returns audio time series and sample rate)
y, sr = ds.load_audio("audio_path.wav") 
```

#### Extract Backing Track
<!--TO DO: Add content-->
#### Extract Drum-Only Audio
<!--TO DO: Add content-->
