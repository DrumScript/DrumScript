# Digital Signal Processing (DSP)

DrumScript relies on three major pillars of Music Information Retrieval (MIR): Source Separation, Onset Detection, and Tempo Estimation.

## 1. Source Separation (`Demucs`)
Before transcription begins, we often need to isolate the drums from the rest of the band (guitars, vocals, etc.).

We utilise the **Demucs** model, a state-of-the-art Hybrid Transformer architecture. Unlike older spectral masking techniques, Demucs operates in the waveform domain to cleanly separate instruments with minimal "bleeding."

* **Paper:** [Hybrid Transformers for Music Source Separation (Défossez et al.)](references/HYBRID_TRANSFORMERS.pdf)
* **Implementation:** See `drumscript.audio_processor.stem_splitter`.

## 2. Onset Detection
To transcribe a drum, we first need to know *when* it was hit. This is called **Onset Detection**.

We analyze the **Spectral Flux**—essentially measuring how quickly the energy in the audio signal changes. A sudden spike in high-frequency energy usually indicates a percussive strike (a transient).

* **Library:** We use `librosa` for spectral analysis.
* **Reference:** [Real-Time Automatic Drum Transcription](references/Published_Real-Time_Automatic_Drum_Transcription.pdf)

## 3. Classification
Once a hit is detected, we classify it (Kick vs. Snare). DrumScript uses a **Rule-Based Engine** based on frequency centroids:
* **Kick:** Low frequency energy (< 100Hz).
* **Snare:** Mid-range energy (200-400Hz) with "noise" (snare wires).
* **Hi-Hats:** High-frequency energy (> 5kHz).

For a deep dive into frequency mapping, see our [MIDI Frequency Table](images/midi_frequency_table.png).