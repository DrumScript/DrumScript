# Usage Guide

## Quick Start
Transcribe a drum beat in three lines of code:

```python
import drumscript as ds

# 1. Load your audio
audio = ds.load("beat.wav")

# 2. Transcribe to sheet music
score = ds.transcribe(audio)

# 3. Save as PDF
score.export("output.pdf")
```

### Command Line Interface

You can also use DrumScript directly from your terminal:

```bash
python -m drumscript.main input_song.mp3 --output my_score.pdf
```

> **Simple**

```python
import drumscript as ds

# 1. Load Audio
y, sr = ds.load_audio("test.wav")

# 2. Detect Tempo
bpm = ds.detect_tempo(y, sr)

# 3. Separate Stems
stems = ds.separate_stems("test.wav", output_dir="./my_stems")
```

> **Full commands**

#### **Basic Transcription**

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
    input_file="path_to_your_song.mp3",
    output_dir="output_stems/"
)

print(f"Drum stem saved at: {drum_track_path}")
```

#### **Audio Loading**

Load and normalise audio files for analysis. The `AudioLoader` handles mono conversion and peak normalisation automatically.

```python
from drumscript.audio_processor.audio_loader import AudioLoader

# Initialise loader
loader = AudioLoader()

# Load audio (returns audio time series and sample rate)
y, sr = loader.load_audio("path/to/drum_stem.wav") 
```