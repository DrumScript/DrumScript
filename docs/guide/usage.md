# Usage Guide

<!--date_updated:sat-17-january-2026-->
<!--date_updated:sun-16-august-2026-->

## Quick Start

### 1. **Audio Loading**
 
Load and normalise audio files for analysis. The `load_audio` handles mono conversion and peak normalisation automatically.

```python
import drumscript as ds
y, sr = ds.load_audio("audio_path.wav")   # y = audio samples, sr = sample rate
```

### 2. **Extract Drums From Any Song**

Want to isolate the drums in your favourite song?

```python
import drumscript as ds
extract_drums = ds.extract_drum_stem("audio_path.wav", output_dir="path_to_output_dir/")
```

> `extract_drum_stem()` writes to your **current working directory** if `output_dir` is not specified.

### 3. **Create Drumless Backing Track (`--drumless`)**

Want to jam along? Remove the drums from your favourite song:

```zsh
drumscript "audio_path.wav" --drumless
```

### 5. Custom Time Signatures (`--ts`)

By default, `DrumScript` assumes `4/4` time. You can override this for waltzes or complex meters:

```zsh
# Transcribe a waltz
drumscript "audio_path.wav" --ts 3/4

# Transcribe 6/8 time
drumscript "audio_path.wav" --ts 6/8
```

> Use a forward slash. Any other form — including underscores like `3_4` or a typo like `44` — falls back to 4/4 and prints a warning.
