# `DrumScript` Bug Report Template
---
name: Bug report
about: Something is broken or behaving unexpectedly
title: "[BUG] "
labels: bug
assignees: ''

---

## Describe the bug

A clear description of what is broken and what you expected to happen instead.

## Steps to reproduce

```python
# Minimal code that reproduces the problem
import drumscript as ds

ds.transcribe("my_file.wav")
```

1. Step one
2. Step two
3. See error

## Expected behaviour

What you expected to happen.

## Actual behaviour

What actually happened. Include the full error message and stack trace if there is one.

<details>
<summary>Full traceback</summary>

```
Paste the full traceback here


```

</details>

## Environment

Run `uv pip list | grep -E "drumscript|torch|librosa|demucs|numpy|soundfile"` and paste the output:

```
# paste here


```
| Item | Value |
|------|-------|
| DrumScript version | e.g. 0.1.2 |
| Python version | e.g. 3.11.4 |
| OS | e.g. macOS 14.4, Ubuntu 24.04, Windows 11 |
| ffmpeg on PATH? | yes / no / not sure |

## Audio file details (if relevant)

| Item | Value |
|------|-------|
| Format | e.g. WAV, MP3 |
| Sample rate | e.g. 44100 Hz |
| Duration | e.g. 3 min 24 sec |
| Input type | Full mix / isolated drum stem |

## Additional context

Any other information that might help — screenshots, links, related issues.
