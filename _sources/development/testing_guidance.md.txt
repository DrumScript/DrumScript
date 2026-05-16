# Testing Guidance

<!--date_created: sat-21-june-2025-->
<!--date_updated: thurs-30-apr-2026-->

DrumScript ships with a [pytest](https://docs.pytest.org/) test suite organised
around a clear separation between **fast unit tests** and **slower integration
tests**. This page covers the *philosophy* and *contribution conventions* for
the suite. For a copy-pasteable command reference, see the
[tests README on GitHub](https://github.com/DrumScript/DrumScript/tree/main/tests#readme).

- **[The Test Pyramid](#the-test-pyramid)**
- **[Modules](#modules)**
- **[Suite layout](#suite-layout)**
- **[Markers](#markers)**
- **[Writing a new test](#writing-a-new-test)**
- **[Patterns you'll use often](#patterns-youll-use-often)**
- **[Coverage reports](#coverage-reports)**
- **[Common pitfalls](#common-pitfalls)**
- **[Continuous integration](#continuous-integration)**
- **[See also](#see-also)**


<!--- - **[]()**-->


---

## The Test Pyramid
[*back to top*](#testing-guidance)

DrumScript follows the classic [test pyramid](https://martinfowler.com/articles/practical-test-pyramid.html):

| Layer | Speed | Volume | What it covers |
|---|---|---|---|
| **Unit** | milliseconds | many (~75 tests) | Pure functions, helper logic, no I/O |
| **Integration** | seconds–minutes | few (~8 tests) | Real Demucs runs, real ffmpeg, real files |
| **End-to-end** | minutes | very few | Full pipeline: audio → MIDI/PDF/XML |

The dev loop (`pytest -m "not slow"`) runs only the unit layer, which finishes
in well under 5 seconds. Integration tests are opt-in, so they don't slow down
day-to-day development but can be triggered before a release with a plain
`pytest`.

```{admonition} Why this matters
:class: tip
Trying to test everything end-to-end is the most common testing mistake. It
gives you a suite that takes 20 minutes to run and tells you nothing useful
when something fails. Unit tests catch *most* bugs *much* faster.
```
---
## Suite Layout
[*back to top*](#testing-guidance)

```
tests/
├── conftest.py              ← shared fixtures (auto-discovered)
├── fixtures/audio/          ← real audio files (empty; synthesised in conftest)
├── unit/                    ← fast, no I/O, no subprocess
│   ├── test_audio_loader.py
│   ├── test_helpers.py
│   ├── test_stem_splitter_helpers.py
│   ├── test_tempo_detector.py
│   ├── test_onset_detector.py
│   └── test_classify.py
└── integration/             ← real Demucs / ffmpeg / files (slow)
    └── test_stem_splitter_real.py
```

Tests are auto-discovered by pytest — any file matching `test_*.py` under
`tests/` is picked up automatically. There is no central registry to update
when adding new files.

---

## Markers

Two custom markers are defined in `pytest.ini`:

`@pytest.mark.slow`
: Tests that take more than a second or two. Skipped by default during
  development.

`@pytest.mark.integration`
: Tests that require external dependencies — Demucs, ffmpeg, real audio
  files. Always combined with `slow`.

```zsh
# Fast loop (default)
pytest -m "not slow"

# Integration tests only
pytest -m integration

# Everything (e.g. before a release)
pytest
```

```{admonition} Strict markers
:class: note
`pytest.ini` enables `--strict-markers`, which means typos like
`@pytest.mark.slwo` will fail loudly instead of silently applying to nothing.
If you add a new marker category, register it in `pytest.ini` first.
```

---

## Writing a New Test

### 1. Pick the right layer

Ask yourself: *does my test need to touch the filesystem, run a subprocess, or
load audio that takes more than 100ms?*

- **No** → put it in `tests/unit/`. No marker needed.
- **Yes** → put it in `tests/integration/` and decorate with both
  `@pytest.mark.slow` and `@pytest.mark.integration`.

### 2. Follow the file conventions

- Filename: `test_*.py`
- Class names: `Test*`
- Function names: `test_*`
- Group related assertions inside a `Test*` class for readability — pytest
  treats each method as a separate test.

### 3. Use Arrange / Act / Assert

Every test should follow this shape:

```python
def test_normalises_to_unit_peak():
    # Arrange — set up inputs
    audio = np.array([0.0, 0.5, -0.25, 0.1], dtype=np.float32)

    # Act — do the thing
    result = normalise_audio(audio)

    # Assert — verify the outcome
    assert np.isclose(np.max(np.abs(result)), 1.0)
```

One test = one act = one (or a few related) asserts. If you find yourself
writing more than one *act* in a single test, split it into two.

### 4. Use `tmp_path` for file output

Pytest gives you a fresh temp directory per test, automatically cleaned up.
**Always use it** instead of writing to the working directory or hardcoded
paths.

```python
def test_writes_output_file(tmp_path):
    output = tmp_path / "out.wav"
    # ... do stuff that writes to output ...
    assert output.exists()
    assert output.stat().st_size > 0
```

### 5. Reuse fixtures from `conftest.py`

The shared fixtures already cover most needs:

| Fixture | What it gives you |
|---|---|
| `sine_wave` | 1-second 440 Hz sine, mono float32 |
| `silent_audio` | 5 seconds of silence |
| `click_track_120bpm` | Deterministic click track for tempo tests |
| `stereo_constant_audio` | 1 second of stereo audio with known amplitudes |
| `small_wav_file` | Sine wave written to disk in `tmp_path` |
| `stem_files` | Three distinct stems written to disk for mixing tests |

Add new fixtures to `conftest.py` only if more than one file will use them.
Single-use fixtures belong in the test file itself.

---
## Patterns You'll Use Often

### Parametrised tests

When the same logic needs to be checked against many inputs, use
`@pytest.mark.parametrize` rather than copying the test:

```python
@pytest.mark.parametrize("input_beats,subdivision,expected", [
    (0.24, 4, 0.25),
    (0.51, 4, 0.50),
    (0.0, 4, 0.0),
    (1.99, 4, 2.0),
])
def test_round_to_nearest_subdivision(input_beats, subdivision, expected):
    assert round_to_nearest_subdivision(input_beats, subdivision) == pytest.approx(expected)
```

Each tuple becomes a separate test in pytest's output, so you get clear
per-case pass/fail reporting.

### Approximate snapshot tests for DSP code

DSP algorithms (tempo detection, onset detection, etc.) produce *approximate*
results. Direct equality assertions are too brittle. Use tolerance bands
instead:

```python
def test_tempo_detection_on_120bpm_click(click_track_120bpm):
    audio, sr = click_track_120bpm
    bpm = estimate_tempo(audio, sr)
    # ±10% — accepts 108-132 BPM. Wide enough for librosa's variance,
    # narrow enough to catch real regressions.
    assert 108 <= bpm <= 132
```

### Mocking subprocess calls

The unit tests for `stem_splitter` don't actually run Demucs — that would be
too slow. Instead, they mock `subprocess.run` and verify the *command being
constructed*. The real Demucs run lives in
`tests/integration/test_stem_splitter_real.py`.

---

## Coverage Reports

Once `pytest-cov` is installed (it's part of the `dev` group), you can see
which lines of source code your tests are exercising:

```zsh
pytest --cov=drumscript --cov-report=term-missing
```

`term-missing` adds a column listing the line numbers that *aren't* covered.
That's the column to look at when deciding what to test next.

```{admonition} Aim for value, not 100%
:class: warning
Don't chase 100% coverage. The classification logic deserves rigorous tests;
the `__main__` blocks at the bottom of files don't. High-value coverage is
better than total coverage.
```

---

## Common Pitfalls

1. **Don't test third-party libraries.** Test how *your code uses them*. An
   assertion like `assert librosa.load("x.wav")` is testing librosa, not
   DrumScript.
2. **Don't test private implementation details.** Test public behaviour. If
   you rename `_read_stem_as_array` to `_load_stem`, your tests for
   `mix_stems` should still pass.
3. **Don't put real audio files larger than ~100KB in the repo.** Use small
   fixtures and synthesise the rest in `conftest.py`.
4. **Don't write the test only after the bug.** When you fix a bug, write the
   test that *would have caught it*. This is the single most valuable kind of
   test you can add.

---

## Continuous Integration

CI configuration is on the roadmap. The intended setup is:

- Run `pytest -m "not slow"` on every push and pull request
- Run the full suite (`pytest`) on tagged release commits
- Publish coverage reports as a build artifact

Until CI is in place, contributors are expected to run `pytest -m "not slow"`
locally before opening a pull request.

---

## See Also

- [Tests README](https://github.com/DrumScript/DrumScript/tree/main/tests#readme) — copy-pasteable command reference
- [Contributor Guidance](contributor_guidance.md)
- [Documentation Guide](documentation.md)
- [Pytest documentation](https://docs.pytest.org/) — official reference

---
<!-- LEGACY_CODE: KEEP FOR NOW
## Modules
[*back to top*](#testing-guidance)

### **`audio_processor/`**

#### `audio_loader.py`

```
python3 audio_processor/audio_loader.py <path_to_audio_file.mp3>
```

**expected output:**

```
Running audio_loader.py example with actual MP3/WAV...
Attempting to load: <path_to_audio_file.mp3>
Loaded audio: Shape=(324288,), Sample Rate=22050, Duration=14.71 seconds
Original max amplitude: 0.9660
Normalised max amplitude: 1.0000

Playing loaded (and normalised) audio...

# my_test_file.mp3 will play

Audio playback finished.
audio_loader.py example finished.
```

#### `feature_extractor.py`

```
python3 audio_processor/feature_extractor.py
```

**expected output:**

```
    Running feature_extractor.py example...
    Install 'soundfile' (pip install soundfile) to run this example fully.
    Skipping dummy file creation/deletion.
    feature_extractor.py example finished.
    DrumScript %
```

or, to run `feature_extractor.py` as a **module**

```
python -m audio_processor.feature_extractor
```

**expected output:**

```
DrumScript % python -m audio_processor.feature_extractor
Running feature_extractor.py example with test.mp3...
Attempting to load: DrumScript/tests/test.mp3
Loaded audio: Shape=(324288,), Sample Rate=22050, Duration=14.71 seconds

Detecting onsets...
Detected 68 onsets.

--- Features for Onset 1 (at 0.07s) ---
  mfccs: shape=(180,), mean=8.2517
  spectral_centroid: shape=(9,), mean=2826.1621
  spectral_rolloff: shape=(9,), mean=6810.4736
  zero_crossing_rate: shape=(9,), mean=0.1527
  rms: shape=(9,), mean=0.2310

--- Features for Onset 2 (at 0.28s) ---
  mfccs: shape=(180,), mean=7.4435
  spectral_centroid: shape=(9,), mean=2350.6134
  spectral_rolloff: shape=(9,), mean=6206.3477
  zero_crossing_rate: shape=(9,), mean=0.0832
  rms: shape=(9,), mean=0.2055

...

feature_extractor.py example finished.
DrumScript %
```

#### `onset_detector.py`

```
python3 audio_processor/onset_detector.py
```

**expected output:**

```
Running onset_detector.py example...
Created dummy audio file with hits: dummy_audio_with_hits.wav
Original hit times: [0.5, 1.2, 1.8, 2.5, 3.1, 3.8, 4.4]
Detected onsets (seconds): ['0.51', '1.21', '1.81', '2.51', '3.11', '3.81', '4.41']
Cleaned up dummy audio file: dummy_audio_with_hits.wav
onset_detector.py example finished.
```

or, to run `onset_detector.py` as a **module**

```
python3 -m audio_processor.onset_detector
```

**expected output:**

```zsh
DrumScript % python3 -m audio_processor.onset_detector
Running onset_detector.py example with test.mp3...
Attempting to load: ~/DrumScript/tests/test.mp3
Loaded audio: Shape=(324288,), Sample Rate=22050, Duration=14.71 seconds

Detecting onsets from test.mp3...
Detected 68 onsets.

First 10 detected onsets (seconds):
  Onset 1: 0.07s
  Onset 2: 0.28s
  Onset 3: 0.49s
  ...and 58 more onsets.

onset_detector.py example finished.
DrumScript %  -
```

#### `tempo_detector.py`

```
python3 audio_processor/tempo_detector.py <path_to_audio_file.mp3>
```

**expected output:**

```
Attempting to load: my_test_file.mp3
Loaded audio: Shape=(324288,), Sample Rate=44100, Duration=14.71 seconds
Estimated Tempo: 177 BPM
```

#### `tempogram.py`

```
python3 audio_processor/tempogram.py <path_to_audio_file.mp3>
```

**expected output:**

```
Attempting to load: my_test_file.mp3
Loaded audio: Shape=(324288,), Sample Rate=44100, Duration=14.71 seconds
Estimated Tempo: 177 BPM
Tempogram saved to: `DrumScript/visuals/tempogram.png`
```

#### **`drum_classifier/`**

**PLEASE NOTE:**[Testing instructions to be added for the new rule-based classifier scripts: `classify.py` and `generate_score.py`]

<!--TO DO: Add in (any) missing fcts and modules-->
-->

---
<!--END-->