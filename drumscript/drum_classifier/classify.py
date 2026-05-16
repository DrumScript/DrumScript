# DrumScript/drum_classifier/classify.py
# Requires path to audio file in cli command, ie:
# `python3 -m drumscript.drum_classifier.classify path_to_audio_file
# ------------------------------------------------------------------------------------------------------------
"""
This script determines the classification rules by which the parameters in py are applied to audio_file_path.
It fuses high-resolution acoustic DNA extraction with simultaneous HFER/LFER physics rules.
Natively detects and filters isolated single-beat cymbals/kicks using Peak Dominance.
"""

import librosa
import numpy as np

from drumscript.notation_generator import constants
from drumscript.notation_generator.constants import (
    HAT_CLOSED_MAX_DECAY,
    HAT_OPEN_MAX_DECAY,
    HOP_LENGTH,
    IDIOPHONE_MIN_HFER_5K,
    KICK_FREQ_MAX,
    KICK_FREQ_MIN,
    KICK_LFER_MIN,
    N_FFT,
    ONSET_SLICE_DURATION_MS,
    SNARE_FREQ_MAX,
    SNARE_FREQ_MIN,
    SNARE_HFER_MIN,
    TOM_FREQ_LOW_MAX,
    TOM_FREQ_MID_MAX,
    TOM_MIN_DECAY,
)


def get_audio_slice(audio_data: np.ndarray, onset_time: float, sr: int) -> np.ndarray:
    """
    Cuts a specific millisecond slice of audio starting exactly at the onset time.
    """
    start_sample = int(onset_time * sr)
    # Convert duration from ms to seconds, then to samples
    duration_secs = ONSET_SLICE_DURATION_MS / 1000.0
    end_sample = start_sample + int(duration_secs * sr)

    # Pad with zeros if the slice goes past the end of the audio file
    if end_sample > len(audio_data):
        slice_data = audio_data[start_sample:]
        pad_length = end_sample - len(audio_data)
        slice_data = np.pad(slice_data, (0, pad_length), mode="constant")
        return slice_data

    return audio_data[start_sample:end_sample]


def extract_features(audio_slice_short: np.ndarray, audio_slice_long: np.ndarray, sr: int) -> dict:
    """
    Analyses the audio slice and extracts the physical DSP features.
    Uses a short 200ms slice for spectral purity, and a long 1.5s slice for decay.
    Wraps numpy outputs in float() to ensure JSON serialization.
    """
    features = {}

    # 1. Compute the Frequency Spectrum (FFT) on SHORT slice
    stft = np.abs(librosa.stft(audio_slice_short, n_fft=N_FFT, hop_length=HOP_LENGTH))

    spectrum = np.mean(stft, axis=1)
    frequencies = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)

    # 2. Find the Peak Frequency (The strongest fundamental tone)
    peak_idx = np.argmax(spectrum)
    features["peak_freq"] = float(frequencies[peak_idx])

    # 3. Calculate Spectral Centroid (The "Center of Mass" or Brightness)
    centroid = librosa.feature.spectral_centroid(S=stft, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)
    features["centroid"] = float(np.mean(centroid))

    # 4. Resonance (Decay Time) - ON LONG SLICE
    rms = librosa.feature.rms(y=audio_slice_long)[0]
    peak_rms_idx = np.argmax(rms)
    threshold = np.max(rms) * 0.1  # -20dB point

    decay_frames = 0
    for i in range(peak_rms_idx, len(rms)):
        if rms[i] < threshold:
            break
        decay_frames += 1
    features["decay"] = float(librosa.frames_to_time(decay_frames, sr=sr))

    # 5. Calculate Energy Ratios (LFER & HFER) on SHORT slice
    total_energy = np.sum(spectrum)
    if total_energy == 0:
        features["lfer"] = 0.0
        features["hfer"] = 0.0
        features["hfer_5k"] = 0.0
        return features

    # Low Frequency Energy Ratio (Energy below 150Hz)
    low_idx = np.where(frequencies <= 150.0)[0]
    features["lfer"] = float(np.sum(spectrum[low_idx]) / total_energy)

    # snare Wire Energy Ratio (Energy > 2000Hz)
    high_idx = np.where(frequencies > 2000.0)[0]
    features["hfer"] = float(np.sum(spectrum[high_idx]) / total_energy)

    # Cymbal/Hat Energy Ratio (Energy > 5000Hz)
    metal_idx = np.where(frequencies > 5000.0)[0]
    features["hfer_5k"] = float(np.sum(spectrum[metal_idx]) / total_energy)

    return features


def classify_membranophone(p):
    """
    Stage 2A: Sorts skins (kick, snare, toms).
    """
    detected_instruments = []

    # RULE 1: KICK DRUM
    if p["lfer"] >= KICK_LFER_MIN and (KICK_FREQ_MIN <= p["peak_freq"] <= KICK_FREQ_MAX):
        # A kick is a short thud; a tom rings more.
        is_pure_tom = (p["hfer"] < SNARE_HFER_MIN) and (p["decay"] >= TOM_MIN_DECAY)
        if not is_pure_tom:
            detected_instruments.append("kick")

    # RULE 2: SNARE DRUM
    is_snare_freq = SNARE_FREQ_MIN <= p["peak_freq"] <= SNARE_FREQ_MAX
    has_snare_wire = SNARE_HFER_MIN <= p["hfer"] < 0.85

    if has_snare_wire and is_snare_freq:
        detected_instruments.append("snare")

    # RULE 3: TOMS
    is_pure = p["hfer"] < SNARE_HFER_MIN
    is_resonant = p["decay"] >= TOM_MIN_DECAY

    if is_pure and is_resonant:
        if p["peak_freq"] <= TOM_FREQ_LOW_MAX:
            if "kick" not in detected_instruments:
                detected_instruments.append("low_tom")
        elif p["peak_freq"] <= TOM_FREQ_MID_MAX:
            detected_instruments.append("mid_tom")
        elif p["peak_freq"] <= 400:
            detected_instruments.append("high_tom")

    return detected_instruments


def classify_idiophone(p):
    """
    Stage 2B: Sorts Metals (Hats, Cymbals).
    """
    detected_instruments = []
    decay = p["decay"]

    # RULE 4: METALS (Hats / Cymbals)
    if p["hfer_5k"] >= IDIOPHONE_MIN_HFER_5K:
        if decay <= HAT_CLOSED_MAX_DECAY:
            detected_instruments.append("hi_hat_closed")
        elif decay <= HAT_OPEN_MAX_DECAY:
            detected_instruments.append("hi_hat_open")
        else:
            # Raised Centroid from 2500 to 5500 to cleanly separate ride vs crash
            if p["centroid"] > 5500:
                detected_instruments.append("crash")
            else:
                detected_instruments.append("ride")

    return detected_instruments


def classify_event(physics):
    """
    Stage 1: Evaluates both skins and Metals simultaneously.
    """
    instruments = []
    instruments.extend(classify_membranophone(physics))
    instruments.extend(classify_idiophone(physics))

    if not instruments:
        instruments.append("unknown")

    return instruments


def classify_rudiment_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:
    """
    Dedicated classification engine for single beats, paradiddles, and rudiments.
    Uses strict, data-driven physics boundaries and ADSR Transient Gating
    to guarantee perfect single beats and clean ghost notes.
    """
    classified_events = []

    global_max = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 1.0

    for onset_time in onsets:
        start_sample = int(onset_time * sr)

        # 1. TIGHT SLICE PADDING (100ms)
        duration_short_secs = 0.100
        end_sample_short = start_sample + int(duration_short_secs * sr)

        if end_sample_short > len(audio_data):
            slice_data = audio_data[start_sample:]
            pad_length = end_sample_short - len(audio_data)
            y_window_short = np.pad(slice_data, (0, pad_length), mode="constant")
        else:
            y_window_short = audio_data[start_sample:end_sample_short]

        if len(y_window_short) == 0:
            continue

        slice_max = np.max(np.abs(y_window_short)) if len(y_window_short) > 0 else 0.0

        # 2. NOISE FLOOR GATE (10%)
        if slice_max < global_max * 0.10:
            continue

        # 3. LONG SLICE PADDING (1.5s) (for Tom Decay)
        duration_long_secs = 1.5
        end_sample_long = start_sample + int(duration_long_secs * sr)

        if end_sample_long > len(audio_data):
            slice_data = audio_data[start_sample:]
            pad_length = end_sample_long - len(audio_data)
            y_window_long = np.pad(slice_data, (0, pad_length), mode="constant")
        else:
            y_window_long = audio_data[start_sample:end_sample_long]

        # Extract the physics DNA
        physics_profile = extract_features(y_window_short, y_window_long, sr)
        p = physics_profile
        instruments = []

        # --- RUDIMENT PHYSICS RULES ---
        # 1. IS IT METAL OR SKIN? (Metals have > 20% energy above 5kHz)
        is_metal = p["hfer_5k"] > 0.20

        if is_metal:
            # It's a Cymbal or Hat
            if p["decay"] <= constants.HAT_CLOSED_MAX_DECAY:
                instruments.append("hi_hat_closed")
            elif p["decay"] <= 0.50:
                instruments.append("hi_hat_open")
            else:
                # Ride vs Crash (Ride is darker < 6000Hz, Crash is brighter > 6000Hz)
                if p["centroid"] > 6000:
                    instruments.append("crash")
                else:
                    instruments.append("ride")
        else:
            # It's a Kick, Snare, or Tom
            is_kick_freq = p["peak_freq"] < 105.0
            is_thump = p["lfer"] > 0.35

            # Kick decay is short and punchy. add a tighter decay (< 0.40) and
            # a centroid check (> 1000) to ensure the beater click is present,
            # separating real kicks from muffled low toms and stem bleed.
            if is_kick_freq and is_thump and p["decay"] < 0.40 and p["centroid"] > 1000.0:
                instruments.append("kick")

            # Bumped the High-Frequency Energy Ratio to 0.22 to prevent punchy toms from bleeding in
            elif p["hfer"] > 0.22:
                instruments.append("snare")

            else:
                if p["decay"] > 0.75 or p["peak_freq"] < TOM_FREQ_LOW_MAX:
                    instruments.append("low_tom")
                elif p["peak_freq"] <= TOM_FREQ_MID_MAX:
                    instruments.append("mid_tom")
                else:
                    instruments.append("high_tom")

        if not instruments:
            instruments.append("unknown")

        classified_events.append({"time_sec": float(onset_time), "instruments": instruments, "debug_features": physics_profile})

    # --- TRANSIENT ATTACK GATING (kills wobbles/reverb/shimmer of idiophones) ---
    final_events = []
    last_time = -999.0

    for i, ev in enumerate(classified_events):
        time_s = ev["time_sec"]

        # Always keep the absolute first stick strike
        if i == 0:
            final_events.append(ev)
            last_time = time_s
            continue

        last_insts = final_events[-1]["instruments"]
        is_last_metal = any(inst in ["crash", "ride", "hi_hat_open", "hi_hat_closed"] for inst in last_insts)
        is_last_tom = any(inst in ["low_tom", "mid_tom", "high_tom"] for inst in last_insts)

        # Lockout (Allows 150BPM 16th notes = 100ms)
        # Toms are given a longer lockout (0.18s) to prevent their resonant wobble
        # from double-triggering as a ghost onset.
        if is_last_metal:
            lockout = 0.15
        elif is_last_tom:
            lockout = 0.18
        else:
            lockout = 0.09

        if time_s - last_time < lockout:
            continue

        # --- ADSR TRANSIENT CHECK ---
        # Compare 30ms before onset to 50ms after onset.
        # A stick hit explodes in volume. A wobble/reverb just sustains smoothly.
        pre_start = max(0, int((time_s - 0.030) * sr))
        pre_end = int(time_s * sr)
        post_end = min(len(audio_data), int((time_s + 0.050) * sr))

        pre_data = audio_data[pre_start:pre_end]
        post_data = audio_data[pre_end:post_end]

        pre_vol = np.max(np.abs(pre_data)) if len(pre_data) > 0 else 0.0
        post_vol = np.max(np.abs(post_data)) if len(post_data) > 0 else 0.0

        # If the volume didn't jump by at least +25%, it's a fake resonance trigger
        if post_vol < pre_vol * 1.25:
            continue

        # --- OVERALL VOLUME GATE ---
        # Metals require 40% volume spike. Skins require 15% (for ghost notes).
        required_vol = global_max * 0.40 if is_last_metal else global_max * 0.15

        if post_vol > required_vol:
            final_events.append(ev)
            last_time = time_s

    return final_events


def classify_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:
    """
    Wrapper to route validated onsets through the Physics-First Classification Engine.
    Natively detects and filters isolated single-beat cymbals/kicks using Peak Dominance.
    All classification rules (membranophone/idiophone) are integrated natively.
    """
    classified_events = []

    global_max = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 1.0
    duration = len(audio_data) / sr

    # --- NATIVE PEAK DOMINANCE CHECK (Single-Beat Detection) ---
    loud_hit_count = 0
    for t in onsets:
        s_start = int(t * sr)
        s_end = s_start + int(0.1 * sr)
        s_data = audio_data[s_start : min(s_end, len(audio_data))]
        s_vol = np.max(np.abs(s_data)) if len(s_data) > 0 else 0.0

        if s_vol > global_max * 0.50:
            loud_hit_count += 1

    # If the track is short and has exactly ONE loud hit, it is a single drum sample.
    is_single_beat = loud_hit_count == 1 and duration < 30.0

    for onset_time in onsets:
        start_sample = int(onset_time * sr)

        # --- SHORT SLICE PADDING LOGIC (200ms) ---
        duration_short_secs = constants.ONSET_SLICE_DURATION_MS / 1000.0
        end_sample_short = start_sample + int(duration_short_secs * sr)

        if end_sample_short > len(audio_data):
            slice_data = audio_data[start_sample:]
            pad_length = end_sample_short - len(audio_data)
            y_window_short = np.pad(slice_data, (0, pad_length), mode="constant")
        else:
            y_window_short = audio_data[start_sample:end_sample_short]

        if len(y_window_short) == 0:
            continue

        slice_max = np.max(np.abs(y_window_short)) if len(y_window_short) > 0 else 0.0

        # --- SINGLE BEAT GATE ---
        if is_single_beat:
            # 1. Stricter gate for isolated cymbal/kick tails
            if slice_max < global_max * 0.50:
                continue

            # 2. De-Bounce Lockout
            if len(classified_events) > 0:
                last_time = classified_events[-1]["time_sec"]
                # Increased from 0.15 to 0.35 to deal with ride cymbal shimmers
                if float(onset_time) - last_time < 0.35:
                    continue
        # --- LONG SLICE PADDING LOGIC (1.5s) ---
        duration_long_secs = 1.5
        end_sample_long = start_sample + int(duration_long_secs * sr)

        if end_sample_long > len(audio_data):
            slice_data = audio_data[start_sample:]
            pad_length = end_sample_long - len(audio_data)
            y_window_long = np.pad(slice_data, (0, pad_length), mode="constant")
        else:
            y_window_long = audio_data[start_sample:end_sample_long]

        # 1. Extract the physics DNA
        physics_profile = extract_features(y_window_short, y_window_long, sr)

        # 2. Apply Classification Rules (Integrated Logic)
        instruments = []

        # --- MEMBRANOPHONES (skins) ---
        # RULE 1: KICK DRUM
        if physics_profile["lfer"] >= KICK_LFER_MIN and (KICK_FREQ_MIN <= physics_profile["peak_freq"] <= KICK_FREQ_MAX):
            instruments.append("kick")

        # RULE 2: SNARE DRUM
        is_snare_freq = SNARE_FREQ_MIN <= physics_profile["peak_freq"] <= SNARE_FREQ_MAX
        has_snare_wire = SNARE_HFER_MIN <= physics_profile["hfer"] < 0.85
        if has_snare_wire and is_snare_freq:
            instruments.append("snare")

        # RULE 3: TOMS
        is_pure = physics_profile["hfer"] < SNARE_HFER_MIN
        is_resonant = physics_profile["decay"] >= TOM_MIN_DECAY
        if is_pure and is_resonant:
            if physics_profile["peak_freq"] <= TOM_FREQ_LOW_MAX:
                if "kick" not in instruments:
                    instruments.append("low_tom")
            elif physics_profile["peak_freq"] <= TOM_FREQ_MID_MAX:
                instruments.append("mid_tom")
            elif physics_profile["peak_freq"] <= 400:
                instruments.append("high_tom")

        # --- IDIOPHONES (Metals) ---
        # RULE 4: METALS (Hats / Cymbals)
        if physics_profile["hfer_5k"] >= IDIOPHONE_MIN_HFER_5K:
            if physics_profile["decay"] <= HAT_CLOSED_MAX_DECAY:
                instruments.append("hi_hat_closed")
            elif physics_profile["decay"] <= HAT_OPEN_MAX_DECAY:
                instruments.append("hi_hat_open")
            else:
                if physics_profile["centroid"] > 2500:
                    instruments.append("crash")
                else:
                    instruments.append("ride")

        # Fallback for undetected sounds
        if not instruments:
            instruments.append("unknown")

        # 3. Append with unified compatible keys
        classified_events.append({"time_sec": float(onset_time), "instruments": instruments, "debug_features": physics_profile})

    return classified_events

    # --------------------------------------------------------------------------uncomment during testing
    # from datetime import datetime
    # print("\n# ------------------------------------------------------------------------------------")
    # datetimestamp = datetime.now()
    # print(f'\ndate/time: {datetimestamp}')
    # --------------------------------------------------------------------------------------------------
