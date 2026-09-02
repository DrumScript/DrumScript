# `DrumScript` Submit Results Template

<!--date_added:mon-31-august-2026-->
<!--date_updated:tues-01-september-2026-->

**Usage:**  Use this template to submit results from DrumScript, ie inaccurate transcription, poor score generation, or give feedback. Please try to include **as much information** as possible to help us understand what you were trying to achieve. Please **do not share personal information** when using this template.  DrumScript is a **public repository** which means that **anyone** can view its code, including **[Issues](https://github.com/DrumScript/DrumScript/issues)**. GitHub usernames are fine. Please do not upload copyrighted audio, nor your own. Link to it, or supply a short clip you own the rights to. If you are unsure email the developers at hello.drumscript@gmail.com. 

**Release Plan**
Before we can publish a **confident v1.0.0 of `DrumScript` we need to:**
1. perfect the **DrumScript deterministic engine**: ie, the classification model and the score/PDF generation
2. build an in-browser, zero storage for input or output audio and **free-to-use** UI for non-coders

> 
<!--**about:** Share a transcription DrumScript produced (or some other output), so it can be reviewed and used to improve accuracy of the **deterministic classification engine**, **pdf rendering** and/or the **score generation**
title: "[RESULTS] "
labels: transcription-results
assignees: ''-->

---

## Summary

One sentence: what were you trying to do, and how did it go overall?
Tick one:

- [ ] Transcribe drum-only audio into pdf drum sheet music
- [ ] Transcribe drum-only from polyphonic* audio into pdf drum sheet music
- [ ] Detect tempo of drum-only audio
- [ ] Extract drums from polyphonic* audio
- [ ] Create a backing track from polyphonic* audio

> ****polyphonic audio*** *refers to a sound or musical texture made up of two or more independent melodic lines or multiple notes played at the exact same time. you might call this a **song***

## Overall rating

**Tick one:**

- [ ] Usable as-is
- [ ] Usable after minor manual editing
- [ ] Recognisable, but needs substantial editing
- [ ] Not usable

## Source audio

| **Item** | *Value* |
|------|-------|
| **Artist / track (or "own recording")** | *e.g. Megadeth, Peace Sell*s* |
| **Genre** | *e.g. thrash metal, funk, jazz* |
| **Real tempo (BPM)** (if you know it) | *e.g. 156* |
| **Real time signature** (if you know it) | *e.g. 4/4, 7/8* |
| **Duration** | *e.g. 1 min 01 sec* |
| **Format / sample rate** | *e.g. WAV, 44100 Hz* |
| **Input type** (if you know it)| *Full mix / isolated drum stem* |
| **Kit type** (if you know it)| *Acoustic / electronic / sampled / programmed* |
| **Production** (if you know it)| *Studio / live / rehearsal room / phone recording* |


## How you ran it

```bash
# Paste the exact CLI command, or the Python you called
drumscript transcribe test.wav
```
```
# paste here


```

## Environment

Run `uv pip list | grep -E "drumscript|torch|librosa|demucs|numpy|soundfile"` and paste the output:

```
# paste here


```

| Item | *Value* |
|------|-------|
| **DrumScript version** | *e.g. 0.2.1* |
| **Python version** | *e.g. 3.12.4* |
| **OS** | *e.g. macOS 14.4, Ubuntu 24.04, Windows 11* |
| **ffmpeg on PATH?** | *yes / no / not sure* |

## Detection summary

Fill in what **DrumScript** reported. The tempo and onset count are printed in the log; the instrument counts can be counted from the JSON.

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

<details>
<summary>Additional notes</summary>

```
Paste here


```

</details>

---

<!--FOR OUR PURPOSES-->
<!--date_received:tues01sept2026-->
<!--date_assigned:tues01sept2026-->
<!--date_closed:tues01sept2026-->
<!--user_conf_sent:tues01sept2026-->
<!--zero_ephemeral_data:yes/no-->