<!--date_created: weds-25-june-2025-->
<!--date_updated: weds-01-oct-2025-->

# **`DrumScript`: Glossary of Terms**

# **Python Libraries**
## [`Librosa`](#librosa)

> **Python library**

  - [`librosa`]((https://librosa.org/doc/latest/advanced.html)) is a popular open-source Python library for **audio and music analysis**. It is a **powerful toolkit** that helps you **process, analyse**, and understand **sound**.
  - `librosa` provides a wide **range of Python functions** for common tasks in **music information retrieval (MIR)** and **audio processing**, such as:
      - **Loading audio files:** Reading various audio formats (`.wav`, `.MP3`, etc.) into a format Python can easily work with.
      - **Feature extraction:** Converting raw audio into meaningful numerical descriptions (features) that **classification systems can use**, like **MFCCs (Mel-frequency cepstral coefficients)**, **spectral centroid**, **rhythm features**, etc.
      - **Time-frequency analysis**: Analysing how the **frequency content of sound** changes over time (e.g., creating **spectrograms**).
      - **Beat and tempo detection:** Identifying the pulse or speed of music.
      - **Pitch tracking:** Estimating the **fundamental frequency** of a **sound**.
      - **Onset detection:** Finding the **precise moments where sounds begin** (like a *snare hit*).

In `DrumScript`, `librosa` is crucial because it's the underlying library that `audio_loader.py`, `feature_extractor.py`, and `onset_detector.py` use to actually perform the **low-level audio processing** and extract the characteristics of your **drum sound** and **audio recordings**. `Librosa`'s beat and tempo detection functions are specifically used in the `tempo_detector.py` and `tempogram.py` scripts.

## [`MuseScore`](#musescore)

  - [`MuseScore`](https://musescore.org/%5D\(https://musescore.org/\)) [source code here](https://github.com/musescore/MuseScore) is a popular, free, and open-source **music notation software**. It provides a comprehensive environment for **creating, editing, printing**, and **playing back sheet music**.
  - `MuseScore` offers a wide range of features for **composing and arranging music**, such as:
      - **Intuitive score entry:** Easily add notes, rests, and other musical elements using a mouse, keyboard, or MIDI input.
      - **Extensive musical symbols:** Supports a vast library of notation symbols, including dynamics, articulations, slurs, tuplets, and complex rhythmic figures.
      - **Playback capabilities:** Hear your compositions with built-in sounds, allowing for immediate feedback on your arrangements.
      - **Layout and formatting:** Professional-quality typesetting and customizable layout options for print and digital distribution.
      - **Import/Export options:** Supports various file formats, including **MusicXML**, MIDI, PDF, and audio formats.

In `DrumScript`, `MuseScore` is crucial because `music21` can be configured to use it as an **external backend for converting the generated MusicXML score data into a high-quality PDF of drum sheet music**. When LilyPond encounters issues, `MuseScore` serves as a robust and visually capable alternative for rendering the final notation.

-----

# Definitions

## `Discrete Fourier Transform` (`DFT`)

> ***Mathematics***

  * **Meaning:** The **`Discrete Fourier Transform`** (or **`DFT`**) is a mathematical operation that **converts a sequence** of individual, distinct data points from their original *domain* (like time, or space) into a *frequency domain* representation. The `DFT` helps reveal the **underlying cycles** or periodic patterns present within that (discrete) data.   In short, the **`DFT`** breaks down the **complex temperature pattern** into its **repeating components**.

> 
  * **Example:**
> Imagine you have a discrete sequence of numbers, such daily temperature readings for a city over a year. **The DFT can analyse this data to tell you if there are dominant cycles**, such as a strong yearly temperature cycle, a weaker weekly cycle (e.g., *warmer weekends*), or even daily temperature fluctuations (if the data were more granular).

## `Fast Fourier Transform` (`FFT`)

> ***Mathematics***

  * **Meaning:** The **Fast Fourier Transform** (or *FFT*) is an efficient algorithm used to compute the **Discrete Fourier Transform (DFT)**. In essence, it takes a sequence of numbers (discrete data points, like audio samples) and transforms them into a sequence of numbers that represent the different frequencies present in the original data, along with their magnitudes and phases.

> 
  * **Example:**
> Given a finite set of digital audio samples, the FFT quickly calculates the exact set of sine and cosine waves (each with a specific frequency and strength) that, when added together, perfectly reconstruct the original sequence of samples. This transformation is crucial for analyzing digital signals in frequency domain.--\>

## `hop_length`

> ***Variable***

  * **Meaning:** How far the *listening window* (`n_fft`) slides forward (in number of samples) to take the next frequency snapshot.

> 
  * **Example:**
> If `hop_length=512`, the window (or `object_event`) moves **512 samples to the right** for the next analysis, overlapping with the previous window (`object_event`).

  * Playing around with the `hop_length` is often crucial for finding the right split of intervals in a given audio sample.  The `hop_length` also depends on the `SAMPLE_RATE` defined  (in the case of `DrumScript` we have chosen a `sample_rate=441000` across the library)

> There us a **more detailed explanation of `hop_length`**, along with calculated examples in the **[README.md](#README.md#faqs)**

## `n_fft`

> ***Variable***

  * **Meaning:** `n_fft` = **Number of Fast Fourier Transform** points. The size of the *listening window* (in number of samples) that is used to analyse the frequency content of an `audio_segment`.

> 
  * **Example:**
> If **`n_fft= 2048`**, the analysis looks at **2048 samples** **at a time** to determine frequencies. If your `audio_segment` is **shorter than 2048 samples**, you get a warning.

## `sample_rate` (`sr`)

> ***Variable***

  * **Meaning:** How many *snapshots* of the sound wave are taken per second when audio is digitised. A higher number means more detail.

> 
  * **Example:**
> 

```
> If **`sr = 22050 (Hz)`**, it means **`22,050`** sound measurements are recorded **every second**.
```

> 
  * **Example:**
> 

```
> If **`sr=22050 (Hz),`** and the **`input_signal`** of **one of your drum notes** is *`1744 milliseconds`* in length, then your **`sample_rate = ~38450 samples`**
```

---

<!--END-->