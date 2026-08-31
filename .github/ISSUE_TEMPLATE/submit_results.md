

# `DrumScript` Transcription Results Template

<!--date_added:mon-31-august-2026-->
<!--date_updated:mon-31-august-2026-->

**Description:** Share DrumScript results (such as incorrect transcriptions or classifications) to help improve accuracy

---
name: Submit transcription results
about: Share a transcription DrumScript produced, so it can be reviewed and used to improve accuracy
title: "[RESULTS] "
labels: transcription-results
assignees: ''

---

## Summary

One sentence: what did you transcribe, and how did it go overall?

## Overall rating

Tick one:

- [ ] Usable as-is
- [ ] Usable after minor manual editing
- [ ] Recognisable, but needs substantial editing
- [ ] Not usable

## Source audio

| Item | Value |
|------|-------|
| Artist / track (or "own recording") | e.g. Megadeth, Peace Sells |
| Genre | e.g. thrash metal, funk, jazz |
| Real tempo (BPM), if you know it | e.g. 156 |
| Real time signature, if you know it | e.g. 4/4, 7/8 |
| Duration | e.g. 1 min 01 sec |
| Format / sample rate | e.g. WAV, 44100 Hz |
| Input type | Full mix / isolated drum stem |
| Kit type | Acoustic / electronic / sampled / programmed |
| Production | Studio / live / rehearsal room / phone recording |

> Please do not upload copyrighted audio. Link to it, or supply a short clip you
> own the rights to.

## How you ran it

```bash
# Paste the exact CLI command, or the Python you called
drumscript transcribe test.wav
```

## Environment

Run `uv pip list | grep -E "drumscript|torch|librosa|demucs|numpy|soundfile"` and paste the output:

```
# paste here


```

| Item | Value |
|------|-------|
| DrumScript version | e.g. 0.2.1 |
| Python version | e.g. 3.12.4 |
| OS | e.g. macOS 14.4, Ubuntu 24.04, Windows 11 |
| ffmpeg on PATH? | yes / no / not sure |

## Detection summary

Fill in what DrumScript reported. The tempo and onset count are printed in the
log; the instrument counts can be counted from the JSON.

| Item | DrumScript reported | Your estimate of the truth |
|------|---------------------|----------------------------|
| Tempo (BPM) | e.g. 64.60 | e.g. 156 |
| Time signature | e.g. 4/4 | e.g. 4/4 |
| Total onsets detected | e.g. 158 | e.g. 160 |
| Bars in the score | e.g. 16 | e.g. 32 |

## Per-instrument accuracy

Rate each instrument you can judge. Leave rows blank if the instrument is not in
the track.

Key: **Good** / **Over-detected** (heard too often) / **Under-detected** (missed)
/ **Confused** (labelled as something else).

| Instrument | Rating | Notes |
|------------|--------|-------|
| Kick | | |
| Snare | | |
| Hi-hat (closed) | | |
| Hi-hat (open) | | |
| Ride | | |
| Crash | | |
| Toms | | |
| Other (specify) | | |

If an instrument was **confused**, please say what it was confused *with*
(e.g. "open hi-hats came out as crashes").

## Score and PDF readability

Tick anything that applies to the generated PDF:

- [ ] Notation is readable and correctly spaced
- [ ] Bar lengths look wrong
- [ ] Notes are quantised to the wrong subdivision
- [ ] Too many notes crammed into a bar
- [ ] Stems, beams or rests are malformed
- [ ] Instrument is on the wrong line or space of the stave
- [ ] Page or system breaks are in awkward places
- [ ] Other (describe below)

Comments on readability:

```
# your notes here


```

## Files

Please attach as many as you can. GitHub does not accept `.mid`, `.json` or
`.musicxml` directly, so **zip them together** and attach the zip.

- [ ] `*_transcription.json` (required if possible, this is the most useful file)
- [ ] `*_transcription.pdf`
- [ ] `*_transcription.mid`
- [ ] `*_transcription.musicxml`
- [ ] `onset_detection.log` or console output
- [ ] Screenshot of the score
- [ ] Short audio clip (only if you own the rights)

<details>
<summary>Console output</summary>

```
Paste the console output here


```

</details>

## Ground truth (optional)

If you have a reference to compare against, this is extremely valuable for
benchmarking.

- [ ] I have a reference MIDI file
- [ ] I have a published or hand-written drum chart
- [ ] I played the part myself and know what I played
- [ ] No ground truth available

## Permission to reuse

- [ ] You may use this transcription output (JSON / MIDI / PDF) as a test case in the DrumScript repository.
- [ ] You may quote my comments in issues, docs or a paper.
- [ ] Please credit me as: `your name or handle here`
- [ ] Please keep this private to the maintainers (do not reuse).

## Additional context

Anything else worth knowing. Related issues, links, or a specific timestamp in
the audio where things went wrong.