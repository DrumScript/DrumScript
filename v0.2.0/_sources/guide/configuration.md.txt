# Configuration

<!--date_updated:sun-16-august-2026-->

DrumScript's DSP behaviour is controlled by module-level constants rather than
per-call parameters. This page documents what is actually configurable today.

> **Note:** Earlier versions of this page documented a `threshold` argument on
> `detect_onsets()` and a `format` argument for output. Neither exists. The
> real controls are described below.

## Onset Detection

`detect_onsets()` takes the audio and its sample rate, and nothing else:

```python
import drumscript as ds

y, sr = ds.load_audio("drum_audio.wav")
y = ds.normalise_audio(y)
onsets = ds.detect_onsets(y, sr)   # returns a list of times in seconds
```

Sensitivity is governed by two values set inside
`drumscript/audio_processor/onset_detector.py`:

| Setting | Value | Effect |
|---|---|---|
| `delta` | `0.05` | Detection threshold above the noise floor. Lower detects quieter hits (more false positives); higher misses ghost notes. |
| lockout | `0.05` s | Minimum gap between two detected hits. Stops cymbal vibration from double-triggering. |

Both are currently hardcoded. Exposing them as arguments is on the roadmap —
see [the issue tracker](https://github.com/DrumScript/DrumScript/issues).

## Sample Rate and Hop Length

Set in `drumscript/notation_generator/constants.py`:

| Constant | Value | Meaning |
|---|---|---|
| `SAMPLE_RATE` | `44100` | Rate the pipeline resamples to internally. |
| `HOP_LENGTH` | `128` | Analysis window advance, ~2.9 ms at 44.1 kHz. |

`load_audio()` defaults to the file's **native** rate. The pipeline passes
`sr=SAMPLE_RATE` explicitly when it needs a consistent rate:

```python
from drumscript.notation_generator.constants import SAMPLE_RATE

y, sr = ds.load_audio("drum_audio.wav")                 # native rate
y, sr = ds.load_audio("drum_audio.wav", sr=SAMPLE_RATE) # resampled to 44100
```

## Output Formats

Output format is not a parameter. `transcribe()` always writes three files and
reports where they went:

```python
result = ds.transcribe("drum_audio.wav")
result["pdf_path"]    # sheet music
result["json_path"]   # raw transcription data
result["midi_path"]   # MIDI for DAW import
```

MusicXML is not produced automatically. Export it separately with
`ds.export_xml()`.

> Per-format flags (`output_midi`, `output_json`, `output_xml`) are planned —
> see the [CHANGELOG](../changelog.md).

## Stem Output Format

The one place a format **is** selectable is stem export, via `--format` on the
CLI or `output_format=` in the Python API:

```zsh
drumscript "full_song.mp3" --all-stems --format mp3
```

```python
ds.extract_stems("full_song.mp3", all_stems=True, output_format="mp3")
```

Valid values are `wav` (default) and `mp3`. MP3 requires `ffmpeg`; WAV does not.

## Time Signature

```python
ds.transcribe("drum_audio.wav", time_signature="6/8")
```

```zsh
drumscript "drum_audio.wav" --ts 6/8
```

> Use a forward slash (`3/4`, `6/8`). Any other form — including underscores
> like `3_4` — silently falls back to 4/4 with no warning.
