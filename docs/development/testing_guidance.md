# **Testing Documentation**

<!--date_created: sat-21-june-2025-->
<!--date_updated: fri-12-dec-2025-->

`DrumScript` is a `Python package` that **converts drum audio recordings into sheet music (drum notation) in PDF format**. 

It leverages **advanced audio signal processing** and **machine learning** to detect individual drum hits (kick, snare, hi-hat, etc.) and translate them into a musical score.

**[Package Structure](repository_structure.md)** **[README.md](README.md)**

---
## Modules

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

---
<!--END-->