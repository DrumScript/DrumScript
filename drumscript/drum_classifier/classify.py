# DrumScript/drum_classifier/classify.py
# Requires path to audio file in cli command, ie:
# `python3 -m drumscript.drum_classifier.classify path_to_audio_file
# ------------------------------------------------------------------------------------------------------------
"""
This script determines the classification rules by which the parameters in py are applied to audio_file_path.
It fuses high-resolution acoustic DNA extraction with simultaneous HFER/LFER physics rules.
Natively detects and filters isolated single-beat cymbals/kicks using Peak Dominance.
"""

from datetime import datetime

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

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f"\ndate/time: {datetimestamp}")


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


## --- LEGACY CODE --- CLASSIFY_MEMBRANOPHONE()
# def classify_membranophone(p):

# Stage 2A: Sorts skins (kick, snare, toms).

#   detected_instruments = []

# RULE 1: KICK DRUM
#  if p['lfer'] >= KICK_LFER_MIN and (KICK_FREQ_MIN <= p['peak_freq'] <= KICK_FREQ_MAX):
#      detected_instruments.append('kick')

# RULE 2: SNARE DRUM
#  is_snare_freq = (SNARE_FREQ_MIN <= p['peak_freq'] <= SNARE_FREQ_MAX)
#  has_snare_wire = (SNARE_HFER_MIN <= p['hfer'] < 0.85)

#  if has_snare_wire and is_snare_freq:
#     detected_instruments.append('snare')

# RULE 3: TOMS
# is_pure = p['hfer'] < SNARE_HFER_MIN
# is_resonant = p['decay'] >= TOM_MIN_DECAY

# if is_pure and is_resonant:
#    if p['peak_freq'] <= TOM_FREQ_LOW_MAX:
#        if 'kick' not in detected_instruments:
#            detected_instruments.append('low_tom')
#    elif p['peak_freq'] <= TOM_FREQ_MID_MAX:
#        detected_instruments.append('mid_tom')
#    elif p['peak_freq'] <= 400:
#        detected_instruments.append('high_tom')

# return detected_instruments


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


## --- LEGACY CODE --- CLASSIFY_IDIOPHONE()
# def classify_idiophone(p):

# Stage 2B: Sorts Metals (Hats, Cymbals).

# detected_instruments = []
# decay = p['decay']

# RULE 4: METALS (Hats / Cymbals)
# if p['hfer_5k'] >= IDIOPHONE_MIN_HFER_5K:
#    if decay <= HAT_CLOSED_MAX_DECAY:
#        detected_instruments.append('hi_hat_closed')
#    elif decay <= HAT_OPEN_MAX_DECAY:
#        detected_instruments.append('hi_hat_open')
#    else:
#        if p['centroid'] > 2500:
#            detected_instruments.append('crash')
#        else:
#            detected_instruments.append('ride')

# return detected_instruments


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


## --- LEGACY CODE --- CLASSIFY_RUDIMENT_EVENTS
# def classify_rudiment_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:

# Dedicated classification engine for single beats, paradiddles, and rudiments.
# Provides precise frequency cutoffs for isolated toms vs kicks, and rides vs crashes,
# while using smart transient gating to preserve fast ghost notes but drop cymbal tails.

# from drumscript.notation_generator import constants
# classified_events = []

# global_max = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 1.0

# for onset_time in onsets:
#   start_sample = int(onset_time * sr)

# 1. TIGHTER SLICE PADDING (100ms)
# A 200ms slice will accidentally overlap fast 16th notes in a paradiddle.
# 100ms perfectly isolates individual fast stick impacts.
#  duration_short_secs = 0.100
#  end_sample_short = start_sample + int(duration_short_secs * sr)

# if end_sample_short > len(audio_data):
#     slice_data = audio_data[start_sample:]
#     pad_length = end_sample_short - len(audio_data)
#     y_window_short = np.pad(slice_data, (0, pad_length), mode='constant')
# else:
#     y_window_short = audio_data[start_sample:end_sample_short]

# if len(y_window_short) == 0:
#    continue

# slice_max = np.max(np.abs(y_window_short)) if len(y_window_short) > 0 else 0.0

# 2. NOISE FLOOR GATE
# Drops absolute dead air/reflections, but keeps light ghost notes (10% threshold)
# if slice_max < global_max * 0.10:
#    continue

# 3. FAST DE-BOUNCE LOCKOUT (80ms)
# Prevents the 63ms double-trigger on ride cymbals, but easily allows fast 125ms paradiddle strokes.
# if len(classified_events) > 0:
#    last_time = classified_events[-1]["time_sec"]
#    if float(onset_time) - last_time < 0.08:
#        continue

# 4. LONG SLICE PADDING (1.0s)
# duration_long_secs = 1.0
# end_sample_long = start_sample + int(duration_long_secs * sr)

# if end_sample_long > len(audio_data):
#    slice_data = audio_data[start_sample:]
#    pad_length = end_sample_long - len(audio_data)
#    y_window_long = np.pad(slice_data, (0, pad_length), mode='constant')
# else:
#   y_window_long = audio_data[start_sample:end_sample_long]

# Extract the physics DNA
# physics_profile = extract_features(y_window_short, y_window_long, sr)
# p = physics_profile
# instruments = []

# --- DEDICATED ISOLATED PHYSICS RULES ---

# KICK vs PHAT TOM
# Kicks have a fundamental below 105Hz. Phat toms sit at 107Hz - 129Hz.
# if p['lfer'] >= constants.KICK_LFER_MIN and p['peak_freq'] < 105.0:
#   instruments.append('kick')

# SNARE
# is_snare_freq = (constants.SNARE_FREQ_MIN <= p['peak_freq'] <= constants.SNARE_FREQ_MAX)
# if (p['hfer'] >= constants.SNARE_HFER_MIN) and is_snare_freq:
#    instruments.append('snare')

# TOMS
# is_pure = p['hfer'] < constants.SNARE_HFER_MIN
# if is_pure and p['decay'] >= constants.TOM_MIN_DECAY:
#   if p['peak_freq'] <= constants.TOM_FREQ_LOW_MAX:
#      if 'kick' not in instruments:
#         instruments.append('low_tom')
# elif p['peak_freq'] <= constants.TOM_FREQ_MID_MAX:
#   instruments.append('mid_tom')
# elif p['peak_freq'] <= 400:
#    instruments.append('high_tom')

# METALS
# if p['hfer_5k'] >= constants.IDIOPHONE_MIN_HFER_5K:
#    if p['decay'] <= constants.HAT_CLOSED_MAX_DECAY:
#       instruments.append('hi_hat_closed')
#   elif p['decay'] <= constants.HAT_OPEN_MAX_DECAY:
#       instruments.append('hi_hat_open')
#   else:
# RIDE vs CRASH
# Centroid > 5500 clearly separates bright crashes from dark rides
#      if p['centroid'] > 5500:
#          instruments.append('crash')
#     else:
#         instruments.append('ride')

# if not instruments:
#   instruments.append('unknown')
#
# classified_events.append({
#  "time_sec": float(onset_time),
#  "instruments": instruments,
#  "debug_features": physics_profile
# })

# --- CYMBAL WOBBLE CULLING ---
# In a rudiment track, we forcefully drop all subsequent hits that are quieter
# than 25% of the global max. This preserves intentional human ghost notes in a
# snare loop, but kills the long, decaying tail wobbles of an isolated cymbal test.
# final_events = []
# for ev in classified_events:
#   time_s = ev["time_sec"]

#  s_start = int(time_s * sr)
# s_end = s_start + int(0.100 * sr)
# s_data = audio_data[s_start:min(s_end, len(audio_data))]
# v_max = np.max(np.abs(s_data)) if len(s_data) > 0 else 0

# Always keep the first strike, OR any hit that is > 25% volume
# if time_s < 0.2 or v_max > global_max * 0.25:
#     final_events.append(ev)

# return final_events


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

            # --- LEGACY CODE --- OLD KICK LOGIC ---
            # # Kick decay is short. Toms ring out.
            # if is_kick_freq and is_thump and p['decay'] < 0.45:
            #     instruments.append('kick')

            # Kick decay is short and punchy. add a tighter decay (< 0.40) and
            # a centroid check (> 1000) to ensure the beater click is present,
            # separating real kicks from muffled low toms and stem bleed.
            if is_kick_freq and is_thump and p["decay"] < 0.40 and p["centroid"] > 1000.0:
                instruments.append("kick")

            # --- LEGACY CODE --- OLD SNARE LOGIC ---
            # elif p['hfer'] > 0.20:
            #   instruments.append('snare')

            # Bumped the High-Frequency Energy Ratio to 0.22 to prevent punchy toms from bleeding in
            elif p["hfer"] > 0.22:
                instruments.append("snare")

            else:
                ## --- LEGACY CODE -- OLD TOM LOGIC ---
                # Toms have long decay and low hfer, separated by hard freq limits
                # if p['peak_freq'] < 90.0:
                #   instruments.append('low_tom')
                # elif p['peak_freq'] < 115.0:
                #   instruments.append('mid_tom')
                # else:
                #   instruments.append('high_tom')

                # Toms have long decay and low hfer. Boundaries shifted up to catch higher tunings.
                # if p['peak_freq'] < 135.0:
                #   instruments.append('low_tom')
                # elif p['peak_freq'] < 180.0:
                #    instruments.append('mid_tom')
                # else:
                #    instruments.append('high_tom')
                # Toms have long decay and low hfer.
                # We use decay as the primary separator for low toms because floor toms
                # physically sustain much longer than rack toms.
                if p["decay"] > 0.75 or p["peak_freq"] < 95.0:
                    instruments.append("low_tom")
                elif p["peak_freq"] < 180.0:
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

        # --- LEGACY CODE --- LOCKOUT LOGIC ---
        # # Lockout (Allows 150BPM 16th notes = 100ms)
        # lockout = 0.15 if is_last_metal else 0.09

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

        # --- REMOVED 2% DEAD SILENCE GATE ---
        # We removed the global `slice_max < 0.02 * global_max` check here.
        # For highly dynamic tracks like TGOO, we must trust the onset detector to
        # find the quiet ghost notes without artificially gating them out.

        ## --- LEGACY CODE -- SINGLE BEAT GATE ---
        # --- SINGLE BEAT GATE ---
        # if is_single_beat:
        # 1. Strict Gate for isolated cymbal/kick tails
        #   if slice_max < global_max * 0.50:
        #      continue

        # 2. De-Bounce Lockout
        # if len(classified_events) > 0:
        #    last_time = classified_events[-1]["time_sec"]
        #   if float(onset_time) - last_time < 0.15:
        #      continue

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


# def classify_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:

# Restored the explicit `physics_profile` variable name throughout the consolidated rule block for clarity and strict consistency with JSON exports.

# Wrapper to route validated onsets through the Physics-First Classification Engine.
# Natively detects and filters isolated single-beat cymbals/kicks using Peak Dominance.
# All classification rules (membranophone/idiophone) are integrated natively.

# from drumscript.notation_generator import constants
# classified_events = []

# global_max = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 1.0
# duration = len(audio_data) / sr

# --- NATIVE PEAK DOMINANCE CHECK (Single-Beat Detection) ---
# loud_hit_count = 0
# for t in onsets:
#    s_start = int(t * sr)
#    s_end = s_start + int(0.1 * sr)
#    s_data = audio_data[s_start:min(s_end, len(audio_data))]
#    s_vol = np.max(np.abs(s_data)) if len(s_data) > 0 else 0.0

#    if s_vol > global_max * 0.50:
#        loud_hit_count += 1

# If the track is short and has exactly ONE loud hit, it is a single drum sample.
# is_single_beat = (loud_hit_count == 1 and duration < 30.0)

# for onset_time in onsets:
#    start_sample = int(onset_time * sr)

# --- SHORT SLICE PADDING LOGIC (200ms) ---
#    duration_short_secs = constants.ONSET_SLICE_DURATION_MS / 1000.0
#    end_sample_short = start_sample + int(duration_short_secs * sr)

#    if end_sample_short > len(audio_data):
#        slice_data = audio_data[start_sample:]
#        pad_length = end_sample_short - len(audio_data)
#        y_window_short = np.pad(slice_data, (0, pad_length), mode='constant')
#    else:
#        y_window_short = audio_data[start_sample:end_sample_short]

# if len(y_window_short) == 0:
#   continue

# slice_max = np.max(np.abs(y_window_short)) if len(y_window_short) > 0 else 0.0

# Standard safety: Drop absolute dead silence
# if slice_max < 0.02 * global_max:
#    continue

# --- SINGLE BEAT GATE ---
# if is_single_beat:
# 1. Strict Gate
#    if slice_max < global_max * 0.50:
#        continue

# 2. De-Bounce Lockout
#    if len(classified_events) > 0:
#        last_time = classified_events[-1]["time_sec"]
#        if float(onset_time) - last_time < 0.15:
#            continue

# --- LONG SLICE PADDING LOGIC (1.5s) ---
# duration_long_secs = 1.5
# end_sample_long = start_sample + int(duration_long_secs * sr)

# if end_sample_long > len(audio_data):
#    slice_data = audio_data[start_sample:]
#    pad_length = end_sample_long - len(audio_data)
#    y_window_long = np.pad(slice_data, (0, pad_length), mode='constant')
# else:
#    y_window_long = audio_data[start_sample:end_sample_long]

# 1. Extract the physics DNA
# physics_profile = extract_features(y_window_short, y_window_long, sr)

# 2. Apply Classification Rules (Integrated Logic)
# instruments = []

# --- MEMBRANOPHONES (skins) ---
# RULE 1: KICK DRUM
# if physics_profile['lfer'] >= KICK_LFER_MIN and (KICK_FREQ_MIN <= physics_profile['peak_freq'] <= KICK_FREQ_MAX):
#    instruments.append('kick')

# RULE 2: SNARE DRUM
# is_snare_freq = (SNARE_FREQ_MIN <= physics_profile['peak_freq'] <= SNARE_FREQ_MAX)
# has_snare_wire = (SNARE_HFER_MIN <= physics_profile['hfer'] < 0.85)
# if has_snare_wire and is_snare_freq:
#    instruments.append('snare')

# RULE 3: TOMS
# is_pure = physics_profile['hfer'] < SNARE_HFER_MIN
# is_resonant = physics_profile['decay'] >= TOM_MIN_DECAY
# if is_pure and is_resonant:
#    if physics_profile['peak_freq'] <= TOM_FREQ_LOW_MAX:
#        if 'kick' not in instruments:
#            instruments.append('low_tom')
#    elif physics_profile['peak_freq'] <= TOM_FREQ_MID_MAX:
#        instruments.append('mid_tom')
#    elif physics_profile['peak_freq'] <= 400:
#        instruments.append('high_tom')

# --- IDIOPHONES (Metals) ---
# RULE 4: METALS (Hats / Cymbals)
# if physics_profile['hfer_5k'] >= IDIOPHONE_MIN_HFER_5K:
#    if physics_profile['decay'] <= HAT_CLOSED_MAX_DECAY:
#        instruments.append('hi_hat_closed')
#    elif physics_profile['decay'] <= HAT_OPEN_MAX_DECAY:
#        instruments.append('hi_hat_open')
#    else:
#        if physics_profile['centroid'] > 2500:
#            instruments.append('crash')
#        else:
#            instruments.append('ride')

# Fallback for undetected sounds
# if not instruments:
#    instruments.append('unknown')

# 3. Append with unified compatible keys
# classified_events.append({
#    "time_sec": float(onset_time),
#    "instruments": instruments,
#    "debug_features": physics_profile
# })

# return classified_events


## --- LEGACY CODE ---
# def classify_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:
#
# Wrapper to route detected onsets through the new Physics-First Classification Engine.
# Uses the unified dictionary keys: time_sec, instruments, debug_features.
# Natively detects and filters isolated single-beat cymbals/kicks using Peak Dominance.
#
#   classified_events = []

# Calculate global parameters to evaluate amplitude gating for single hits
#  global_max = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 1.0
#  duration = len(audio_data) / sr

# --- Peak Dominance Check (Single-Beat Detection) ---
# Look ahead at the volume of all detected onsets. A ringing cymbal might hallucinate 30 fake onsets due to "shimmer", but only the initial stick
# impact will be loud.
# loud_hit_count = 0
# for t in onsets:
#    s_start = int(t * sr)
#    s_end = s_start + int(0.1 * sr) # Look at the first 100ms of the hit
#    s_data = audio_data[s_start:min(s_end, len(audio_data))]
#    s_vol = np.max(np.abs(s_data)) if len(s_data) > 0 else 0.0

#    if s_vol > global_max * 0.50:
#        loud_hit_count += 1

# If the track is short and has exactly ONE loud hit, it is a single drum sample.
# is_single_beat = (loud_hit_count == 1 and duration < 30.0)
# is_isolated_sample = (loud_hit_count == 1 and duration < 30.0)

# --- DYNAMIC ISOLATED SAMPLE DETECTION ---
# Cymbals ring out for 5-15 seconds, bypassing our old 'duration < 2.0' check.
# We use Onset Density instead. A single hit test sample is sparse (< 1.5 hits per second).
# A real drum track is dense (e.g., 60bpm 8th notes = 2 hits per second).
# onset_density = len(onsets) / duration if duration > 0 else 0
# is_isolated_sample = (duration < 20.0) and (onset_density < 1.5 or len(onsets) <= 5)

# for onset_time in onsets:
#    start_sample = int(onset_time * sr)

# --- SHORT SLICE PADDING LOGIC (200ms) ---
#    duration_short_secs = constants.ONSET_SLICE_DURATION_MS / 1000.0
#    end_sample_short = start_sample + int(duration_short_secs * sr)

#    if end_sample_short > len(audio_data):
#        slice_data = audio_data[start_sample:]
#        pad_length = end_sample_short - len(audio_data)
#        y_window_short = np.pad(slice_data, (0, pad_length), mode='constant')
#    else:
#        y_window_short = audio_data[start_sample:end_sample_short]
#
#
#    if len(y_window_short) == 0:
#        continue

#    slice_max = np.max(np.abs(y_window_short)) if len(y_window_short) > 0 else 0.0

# Standard safety: Drop absolute dead silence to keep the noise floor clean
#    if slice_max < 0.02 * global_max:
#        continue

# --- Single Beat 'Amplitude Gate' ---
# For full songs, we do NOT interfere. We let the onset detector do its job  so ghost notes are perfectly preserved (guaranteeing backward
# compatibility). We only apply the 50% max volume drop to sparse, isolated single-beat samples
#    if is_isolated_sample:
# 1. Strict Gate: Drop the quiet cymbal shimmers/kick sub-bass tails
# slice_max = np.max(np.abs(y_window_short)) if len(y_window_short) > 0 else 0.0
#        if slice_max < 0.5 * global_max:
#           continue

# 2. De-Bounce Lockout: Prevent double-triggering within 150ms of the valid hit
#        if len(classified_events) > 0:
#            last_time = classified_events[-1]["time_sec"]
#            if float(onset_time) - last_time < 0.15:
#                continue

# --- LONG SLICE PADDING LOGIC (1.5s) ---
#    duration_long_secs = 1.5
#    end_sample_long = start_sample + int(duration_long_secs * sr)

#    if end_sample_long > len(audio_data):
#        slice_data = audio_data[start_sample:]
#        pad_length = end_sample_long - len(audio_data)
#        y_window_long = np.pad(slice_data, (0, pad_length), mode='constant')
#    else:
#        y_window_long = audio_data[start_sample:end_sample_long]


# 1. Extract the physics DNA
#    physics_profile = extract_features(y_window_short, y_window_long, sr)

# 2. Run the simultaneous rules
#    instruments = classify_event(physics_profile)

# 3. Append with unified compatible keys
#    classified_events.append(
#       {
#           "time_sec": float(onset_time),
#           "instruments": instruments,
#          "debug_features": physics_profile
#      }
#  )

# return classified_events

# def classify_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:
#
# Wrapper to route detected onsets through the new Physics-First Classification Engine.
# Uses the unified dictionary keys: time_sec, instruments, debug_features.
#
# classified_events = []

# Calculate global parameters to evaluate amplitude gating for single hits
# global_max = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 1.0
# duration = len(audio_data) / sr

# --- DYNAMIC ISOLATED SAMPLE DETECTION ---
# Cymbals ring out for 5-15 seconds, bypassing our old 'duration < 2.0' check.
# We use Onset Density instead. A single hit test sample is sparse (< 1.5 hits per second).
# A real drum track is dense (e.g., 60bpm 8th notes = 2 hits per second).
# onset_density = len(onsets) / duration if duration > 0 else 0
# is_isolated_sample = (duration < 20.0) and (onset_density < 1.5 or len(onsets) <= 5)

# for onset_time in onsets:
#    start_sample = int(onset_time * sr)

# --- SHORT SLICE PADDING LOGIC (200ms) ---
#   duration_short_secs = ONSET_SLICE_DURATION_MS / 1000.0
#   end_sample_short = start_sample + int(duration_short_secs * sr)

# if end_sample_short > len(audio_data):
#  slice_data = audio_data[start_sample:]
#  pad_length = end_sample_short - len(audio_data)
#  y_window_short = np.pad(slice_data, (0, pad_length), mode='constant')
# else:
#   y_window_short = audio_data[start_sample:end_sample_short]

# if len(y_window_short) == 0:
#   continue

# --- STRICT SINGLE-BEAT AMPLITUDE GATE ---
# For full songs, we do NOT interfere. We let the onset detector do its job
# so ghost notes are perfectly preserved (guaranteeing backward compatibility).
# We only apply the 50% max volume drop to sparse, isolated single-beat samples
# if is_isolated_sample:
#   slice_max = np.max(np.abs(y_window_short)) if len(y_window_short) > 0 else 0.0
#   if slice_max < 0.5 * global_max:
#       continue

# --- LONG SLICE PADDING LOGIC (1.5s) ---
# duration_long_secs = 1.5
# end_sample_long = start_sample + int(duration_long_secs * sr)

# if end_sample_long > len(audio_data):
#    slice_data = audio_data[start_sample:]
#    pad_length = end_sample_long - len(audio_data)
#    y_window_long = np.pad(slice_data, (0, pad_length), mode='constant')
# else:
#    y_window_long = audio_data[start_sample:end_sample_long]

# 1. Extract the physics DNA
# physics_profile = extract_features(y_window_short, y_window_long, sr)

# 2. Run the simultaneous rules
# instruments = classify_event(physics_profile)

# 3. Append with unified compatible keys
# classified_events.append(
#   {
#       "time_sec": float(onset_time),
#       "instruments": instruments,
#       "debug_features": physics_profile
#  }
# )

# return classified_events

# Reasoning: Replaced the static 2.0s duration check with an Onset Density check to safely gate long-ringing cymbals whilst protecting full songs.

# --- LEGACY CODE --
# def classify_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:

# Wrapper to route detected onsets through the new Physics-First Classification Engine.
# Uses the unified dictionary keys: time_sec, instruments, debug_features.

# classified_events = []

# Calculate global parameters to evaluate amplitude gating for single hits
# global_max = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 1.0
# duration = len(audio_data) / sr

# for onset_time in onsets:
#    start_sample = int(onset_time * sr)

# --- SHORT SLICE PADDING LOGIC (200ms) ---
#   duration_short_secs = ONSET_SLICE_DURATION_MS / 1000.0
#   end_sample_short = start_sample + int(duration_short_secs * sr)

#  if end_sample_short > len(audio_data):
#      slice_data = audio_data[start_sample:]
#      pad_length = end_sample_short - len(audio_data)
#      y_window_short = np.pad(slice_data, (0, pad_length), mode='constant')
#  else:
#      y_window_short = audio_data[start_sample:end_sample_short]

# if len(y_window_short) == 0:
#     continue

# --- STRICT SINGLE-BEAT AMPLITUDE GATE ---
# For full songs (> 2.0s), we do NOT interfere. We let the onset detector do its job
# so ghost notes are perfectly preserved (guaranteeing backward compatibility).
# We only apply the 50% max volume drop to short, isolated single-beat samples
# if duration < 2.0:
#   slice_max = np.max(np.abs(y_window_short)) if len(y_window_short) > 0 else 0.0
#  if len(classified_events) > 0 and slice_max < 0.5 * global_max:
#     continue

# --- LONG SLICE PADDING LOGIC (1.5s) ---
# duration_long_secs = 1.5
# end_sample_long = start_sample + int(duration_long_secs * sr)

# if end_sample_long > len(audio_data):
#    slice_data = audio_data[start_sample:]
#    pad_length = end_sample_long - len(audio_data)
#    y_window_long = np.pad(slice_data, (0, pad_length), mode='constant')
# else:
#    y_window_long = audio_data[start_sample:end_sample_long]

# 1. Extract the physics DNA
# physics_profile = extract_features(y_window_short, y_window_long, sr)

# 2. Run the simultaneous rules
# instruments = classify_event(physics_profile)

# 3. Append with unified compatible keys
# classified_events.append(
#   {
#      "time_sec": float(onset_time),
#      "instruments": instruments,
#      "debug_features": physics_profile
# }
# )

# return classified_events

# Reasoning: Restricted the amplitude gate strictly to files under 2.0 seconds. This stops double-triggering on single beats while completely
# bypassing full songs, ensuring 100% backward compatibility for tracks like "My Love for the Stars".

# --- LEGACY CODE ---
# Reasoning: Added a volume-based amplitude gate within the `classify_events` loop to discard quiet room reflections in short audio clips,
# thereby stopping double-triggering without affecting full-song transcriptions.
# def classify_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:
#     """
#     Wrapper to route detected onsets through the new Physics-First Classification Engine.
#     Uses the unified dictionary keys: time_sec, instruments, debug_features.
#     """
#     classified_events = []
#
#     for onset_time in onsets:
#         start_sample = int(onset_time * sr)
#
#         # --- SHORT SLICE PADDING LOGIC (200ms) ---
#         duration_short_secs = ONSET_SLICE_DURATION_MS / 1000.0
#         end_sample_short = start_sample + int(duration_short_secs * sr)
#
#         if end_sample_short > len(audio_data):
#             slice_data = audio_data[start_sample:]
#             pad_length = end_sample_short - len(audio_data)
#             y_window_short = np.pad(slice_data, (0, pad_length), mode='constant')
#         else:
#             y_window_short = audio_data[start_sample:end_sample_short]
#
#         if len(y_window_short) == 0:
#             continue
#
#         # --- LONG SLICE PADDING LOGIC (1.5s) ---
#         duration_long_secs = 1.5
#         end_sample_long = start_sample + int(duration_long_secs * sr)
#
#         if end_sample_long > len(audio_data):
#             slice_data = audio_data[start_sample:]
#             pad_length = end_sample_long - len(audio_data)
#             y_window_long = np.pad(slice_data, (0, pad_length), mode='constant')
#         else:
#             y_window_long = audio_data[start_sample:end_sample_long]
#
#
#         # 1. Extract the physics DNA
#         physics_profile = extract_features(y_window_short, y_window_long, sr)
#
#         # 2. Run the simultaneous rules
#         instruments = classify_event(physics_profile)
#
#         # 3. Append with unified compatible keys
#         classified_events.append(
#             {
#                 "time_sec": float(onset_time),
#                 "instruments": instruments,
#                 "debug_features": physics_profile
#             }
#         )
#
#     return classified_events


# --- LEGACY CODE ---
# def classify_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:
# Wrapper to route detected onsets through the new Physics-First Classification Engine.
# Uses the unified dictionary keys: time_sec, instruments, debug_features.

#  classified_events = []

# Calculate global parameters to evaluate amplitude gating
# global_max = np.max(np.abs(audio_data)) if len(audio_data) > 0 else 1.0
# duration = len(audio_data) / sr

# for onset_time in onsets:
#  start_sample = int(onset_time * sr)

# --- SHORT SLICE PADDING LOGIC (200ms) ---
# duration_short_secs = ONSET_SLICE_DURATION_MS / 1000.0
# end_sample_short = start_sample + int(duration_short_secs * sr)

#        if end_sample_short > len(audio_data):
#           slice_data = audio_data[start_sample:]
#           pad_length = end_sample_short - len(audio_data)
#           y_window_short = np.pad(slice_data, (0, pad_length), mode='constant')
#       else:
#           y_window_short = audio_data[start_sample:end_sample_short]
#
#
#        if len(y_window_short) == 0:
#            continue
#
# --- AMPLITUDE GATING FILTER ---
#        slice_max = np.max(np.abs(y_window_short)) if len(y_window_short) > 0 else 0.0
#
#        # Drop absolute silence (< 2% of max)
#        if slice_max < 0.02 * global_max:
#            continue
#
#        # For isolated drum samples (< 2.0s), drop secondary quiet room reflections/tails (< 50% max)
#        if duration < 2.0 and len(classified_events) > 0:
#            if slice_max < 0.5 * global_max:
#                continue

#        # --- LONG SLICE PADDING LOGIC (1.5s) ---
#        duration_long_secs = 1.5
#        end_sample_long = start_sample + int(duration_long_secs * sr)

#        if end_sample_long > len(audio_data):
# slice_data = audio_data[start_sample:]
# pad_length = end_sample_long - len(audio_data)
# y_window_long = np.pad(slice_data, (0, pad_length), mode='constant')
# else:
#   y_window_long = audio_data[start_sample:end_sample_long]


# 1. Extract the physics DNA
# physics_profile = extract_features(y_window_short, y_window_long, sr)

# 2. Run the simultaneous rules
# instruments = classify_event(physics_profile)

# 3. Append with unified compatible keys
# classified_events.append(
#    {
#        "time_sec": float(onset_time),
#        "instruments": instruments,
#        "debug_features": physics_profile
#    }
# )

# return classified_events


# --- EXTRACT_FEATURES ---
# This restores the linear magnitude scale from _classifier.py so the thresholds
# (like KICK_LFER_MIN and SNARE_HFER_MIN) work flawlessly again.
# def extract_features(audio_slice: np.ndarray, sr: int) -> dict:

# Analyses the audio slice and extracts the physical DSP features.
# Wraps numpy outputs in float() to ensure JSON serialization.

# features = {}

# 1. Compute the Frequency Spectrum (FFT)
# We use magnitude (abs) of the Short-Time Fourier Transform
# stft = np.abs(librosa.stft(audio_slice, n_fft=N_FFT, hop_length=HOP_LENGTH))

# Average the spectrum across the tiny time slice to get one master frequency profile
# spectrum = np.mean(stft, axis=1)
# frequencies = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)

# 2. Find the Peak Frequency (The strongest fundamental tone)
# peak_idx = np.argmax(spectrum)
# features['peak_freq'] = float(frequencies[peak_idx]) # Added float() casting

# 3. Calculate Spectral Centroid (The "Center of Mass" or Brightness)
# centroid = librosa.feature.spectral_centroid(S=stft, sr=sr, n_fft=N_FFT, hop_length=HOP_LENGTH)
# features['centroid'] = float(np.mean(centroid)) # Added float() casting

# 4. Resonance (Decay Time) - IMPORTED SO TOMS AND HATS CAN BE CLASSIFIED
# rms = librosa.feature.rms(y=audio_slice)[0]
# peak_rms_idx = np.argmax(rms)
# threshold = np.max(rms) * 0.1 # -20dB point

# decay_frames = 0
# for i in range(peak_rms_idx, len(rms)):
#   if rms[i] < threshold:
#       break
#   decay_frames += 1
# features['decay'] = float(librosa.frames_to_time(decay_frames, sr=sr)) # Added float() casting

# 5. Calculate Energy Ratios (LFER & HFER)
# total_energy = np.sum(spectrum)
# if total_energy == 0: # Prevent division by zero on silent slices
#    features['lfer'] = 0.0
#    features['hfer'] = 0.0
#    features['hfer_5k'] = 0.0
#    return features

# Low Frequency Energy Ratio (Energy below 150Hz)
# low_idx = np.where(frequencies <= 150.0)[0]
# features['lfer'] = float(np.sum(spectrum[low_idx]) / total_energy) # Added float() casting

# snare Wire Energy Ratio (Energy > 2000Hz)
# high_idx = np.where(frequencies > 2000.0)[0]
# features['hfer'] = float(np.sum(spectrum[high_idx]) / total_energy) # Added float() casting

# Cymbal/Hat Energy Ratio (Energy > 5000Hz)
# metal_idx = np.where(frequencies > 5000.0)[0]
# features['hfer_5k'] = float(np.sum(spectrum[metal_idx]) / total_energy) # Added float() casting

# return features


# --- COMMENTED OUT GET_PHYSICS_PROFILE ---
# REASON: The Welch method calculates Power (amplitude squared), which breaks
# the LFER/HFER percentage thresholds. STFT magnitude (extract_features) restores accuracy.
# def get_physics_profile(y, sr):
#     """
#     Extracts the 'DNA' of the drum hit:
#     Pitch, Decay, Brightness, and Energy Ratios.
#     """
#     # 1. Frequency Analysis (High Resolution)
#     freqs, psd = scipy.signal.welch(y, sr, nperseg=4096)
#     peak_idx = np.argmax(psd)
#     peak_freq = freqs[peak_idx]
#
#     # 2. Spectral Centroid (Brightness - Critical for Cymbals)
#     centroid = np.mean(librosa.feature.spectral_centroid(y=y, sr=sr))
#
#     # 3. Energy Distribution Ratios
#     total_energy = np.sum(psd) + 1e-9
#
#     # Bass Energy (<150Hz) - kick detection
#     low_energy = np.sum(psd[freqs < 150])
#     lfer = low_energy / total_energy
#
#     # Wire Energy (>2000Hz) - snare vs High Tom detection
#     mid_high_energy = np.sum(psd[freqs > 2000])
#     hfer_2k = mid_high_energy / total_energy
#
#     # Shimmer Energy (>5000Hz) - Skin vs Metal detection
#     high_energy = np.sum(psd[freqs > 5000])
#     hfer_5k = high_energy / total_energy
#
#     # 4. Resonance (Decay Time)
#     rms = librosa.feature.rms(y=y)[0]
#     peak_rms_idx = np.argmax(rms)
#     threshold = np.max(rms) * 0.1 # -20dB point
#
#     decay_frames = 0
#     for i in range(peak_rms_idx, len(rms)):
#         if rms[i] < threshold:
#             break
#         decay_frames += 1
#     decay_time = librosa.frames_to_time(decay_frames, sr=sr)
#
#     return {
#         "peak_freq": peak_freq,
#         "centroid": centroid,
#         "lfer": lfer,
#         "hfer_2k": hfer_2k,
#         "hfer": hfer_2k,      # Mapped to 'hfer' to ensure compatibility with classify_onset
#         "hfer_5k": hfer_5k,
#         "decay": decay_time
#     }


# --- LEGACY CODE - COMMENTED OUT CLASSIFY_MEMBRANOPHONE (March 17 Interim) ---
# def classify_membranophone(p):
#     """
#     Stage 2A: Sorts skins (kick, snare, toms).
#     Updated to merge Feb 9 explicit logic with simultaneous hit routing.
#     """
#     detected_instruments = []
#
#     # RULE 1: KICK DRUM (Using exact Feb 9 explicit logic)
#     is_kick_freq = KICK_FREQ_MIN <= p['peak_freq'] <= KICK_FREQ_MAX
#     is_thump = p['lfer'] >= KICK_LFER_MIN
#     not_too_crisp = p['hfer'] < SNARE_HFER_MIN # Excludes fat snares
#
#     if is_kick_freq and is_thump and not_too_crisp:
#         detected_instruments.append('kick')
#
#     # RULE 2: SNARE DRUM (Standard + Fat snare catches)
#     is_snare_freq = (SNARE_FREQ_MIN <= p['peak_freq'] <= SNARE_FREQ_MAX)
#     has_snare_wire = (SNARE_HFER_MIN <= p['hfer'] < 0.85)
#
#     if has_snare_wire and (is_snare_freq or p['peak_freq'] < SNARE_FREQ_MIN):
#         detected_instruments.append('snare')
#
#     # RULE 3: TOMS (Integrating exact Feb 9 Purity & Resonance checks)
#     is_pure = p['hfer'] < SNARE_HFER_MIN  # toms have almost no 'wire' noise
#     is_resonant = p['decay'] >= TOM_MIN_DECAY # toms ring longer than kicks
#
#     if is_pure and is_resonant:
#         if p['peak_freq'] <= TOM_FREQ_LOW_MAX:
#             # Prevent duplicate tagging if decay pushed it into Low Tom territory
#             if 'low_tom' not in detected_instruments:
#                 detected_instruments.append('low_tom')
#         elif p['peak_freq'] <= TOM_FREQ_MID_MAX:
#             detected_instruments.append('mid_tom')
#         elif p['peak_freq'] <= 400: # Upper safety bound
#             detected_instruments.append('high_tom')
#
#     return detected_instruments

# def classify_membranophone(p):
#
# Stage 2A: Sorts skins (kick, snare, toms).
# Fuses logic from _classifier.py (kick/snare) with the Tom logic from v0.1.0.
#
# detected_instruments = []

# RULE 1: KICK DRUM (logic from _classifier.py)
# Does not rely on decay, so overlapping cymbals won't turn kicks into Low toms
# if p['lfer'] >= KICK_LFER_MIN and (KICK_FREQ_MIN <= p['peak_freq'] <= KICK_FREQ_MAX):
#   detected_instruments.append('kick')

# --- LEGACY CODE - COMMENTED OUT SNARE RULE (Fat snare catch caused kick+Hat hallucinations) ---
# is_snare_freq = (SNARE_FREQ_MIN <= p['peak_freq'] <= SNARE_FREQ_MAX)
# has_snare_wire = (SNARE_HFER_MIN <= p['hfer'] < 0.85)
#
# if has_snare_wire and (is_snare_freq or p['peak_freq'] < SNARE_FREQ_MIN):
#     detected_instruments.append('snare')

# RULE 2: SNARE DRUM (strict logic from _classifier.py to prevent kick+Hat hallucinations)
# is_snare_freq = (SNARE_FREQ_MIN <= p['peak_freq'] <= SNARE_FREQ_MAX)
# has_snare_wire = (SNARE_HFER_MIN <= p['hfer'] < 0.85)

# if has_snare_wire and is_snare_freq:
#   detected_instruments.append('snare')

# RULE 3: TOMS (From v0.1.0 - pure tone and longer decay)
# is_pure = p['hfer'] < SNARE_HFER_MIN  # toms have almost no 'wire' noise
# is_resonant = p['decay'] >= TOM_MIN_DECAY # toms ring longer than isolated kicks

# if is_pure and is_resonant:
#   if p['peak_freq'] <= TOM_FREQ_LOW_MAX:
#       if 'kick' not in detected_instruments: # Don't label a kick as a Low Tom
#           detected_instruments.append('low_tom')
#   elif p['peak_freq'] <= TOM_FREQ_MID_MAX:
#       detected_instruments.append('mid_tom')
#   elif p['peak_freq'] <= 400: # Upper safety bound
#       detected_instruments.append('high_tom')

# return detected_instruments


# --- LEGACY CODE - COMMENTED OUT CLASSIFY_IDIOPHONE (March 17 Interim) ---
# def classify_idiophone(p):
#     """
#     Stage 2B: Sorts Metals (Hats, Cymbals).
#     Updated to return a list of simultaneous hits.
#     """
#     detected_instruments = []
#     decay = p['decay']
#
#     # RULE 4: METALS (Hats / Cymbals)
#     if p['hfer_5k'] >= IDIOPHONE_MIN_HFER_5K:
#         if decay <= HAT_CLOSED_MAX_DECAY:
#             detected_instruments.append('hi_hat_closed')
#         elif decay <= HAT_OPEN_MAX_DECAY:
#             detected_instruments.append('hi_hat_open')
#         else:
#             if p['centroid'] > 2500:
#                 detected_instruments.append('crash')
#             else:
#                 detected_instruments.append('ride')
#
#     return detected_instruments

# def classify_idiophone(p):

# Stage 2B: Sorts Metals (Hats, Cymbals).
# Uses Feb 9 Decay logic + _classifier.py Centroid thresholds.

# detected_instruments = []
# decay = p['decay']

# RULE 4: METALS (Hats / Cymbals)
# if p['hfer_5k'] >= IDIOPHONE_MIN_HFER_5K:
#    if decay <= HAT_CLOSED_MAX_DECAY:
#        detected_instruments.append('hi_hat_closed')
#    elif decay <= HAT_OPEN_MAX_DECAY:
#        detected_instruments.append('hi_hat_open')
#    else:
# Merged logic: use 2500 from _classifier to prevent kick overlaps looking like rides
#        if p['centroid'] > 2500:
#            detected_instruments.append('crash')
#        else:
#            detected_instruments.append('ride')
#
# return detected_instruments

# --- LEGACY CODE - COMMENTED OUT CLASSIFY_EVENT ---
# def classify_event(audio_segment, sr):
#     """
#     Stage 1: Class Separation (Skin vs Metal)
#     """
#     # physics = get_physics_profile(audio_segment, sr)
#     #
#     # # Is it Metal? (High energy > 5kHz)
#     # if physics['hfer_5k'] >= IDIOPHONE_MIN_HFER_5K:
#     #     return classify_idiophone(physics)
#     # else:
#     #     return classify_membranophone(physics)

# def  classify_event(audio_segment, sr):
#
# Stage 1: Evaluates both skins and Metals simultaneously.
# Returns a list because multiple drums can hit simultaneously

# LEGACY CODE - physics = get_physics_profile(audio_segment, sr)
#   physics = extract_features(audio_segment, sr)
#   instruments = []

# Check skins
#  instruments.extend(classify_membranophone(physics))

# Check metals
#  instruments.extend(classify_idiophone(physics))

# Fallback
# if not instruments:
#        instruments.append('unknown')

#   return instruments

# --- LEGACY CODE - COMMENTED OUT CLASSIFY_EVENTS ---
# def classify_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:
#     """
#     Wrapper to route detected onsets through the Physics-First Classification Engine.
#     Uses the unified dictionary keys: time_sec, instruments, debug_features.
#     """
#     classified_events = []
#
#     for onset_time in onsets:
#         start_sample = int(onset_time * sr)
#
#         # --- LEGACY CODE -  TRUNCATING LOGIC ---
#         # end_sample = int((onset_time + 0.2) * sr)
#         # #duration_secs = ONSET_SLICE_DURATION_MS / 1000.0
#         # #end_sample = start_sample + int(duration_secs * sr)
#         #
#         # if end_sample > len(audio_data):
#         #     end_sample = len(audio_data)
#         # if start_sample >= end_sample:
#         #     continue
#         #
#         # y_window = audio_data[start_sample:end_sample]
#         # if len(y_window) == 0:
#         #     continue
#
#         # --- PADDING LOGIC (Prevents SciPy/Librosa STFT Warnings at End of File) ---
#         duration_secs = ONSET_SLICE_DURATION_MS / 1000.0
#         end_sample = start_sample + int(duration_secs * sr)
#
#         if end_sample > len(audio_data):
#             slice_data = audio_data[start_sample:]
#             pad_length = end_sample - len(audio_data)
#             y_window = np.pad(slice_data, (0, pad_length), mode='constant')
#         else:
#             y_window = audio_data[start_sample:end_sample]
#
#         if len(y_window) == 0:
#             continue
#
#         # 1. Extract the physics DNA
#         physics_profile = get_physics_profile(y_window, sr)
#
#         # 2. Run the simultaneous rules
#         instruments = classify_event(y_window, sr)
#
#         # 3. Append with unified compatible keys
#         classified_events.append(
#             {
#                 "time_sec": float(onset_time),
#                 "instruments": instruments,
#                 "debug_features": physics_profile
#             }
#         )
#
#     return classified_events


# LEGACY CODE
# def classify_events(audio_data: np.ndarray, sr: int, onsets: list[float]) -> list[dict]:
#
#  Wrapper to route detected onsets through the Physics-First Classification Engine.
#  Uses the unified dictionary keys: time_sec, instruments, debug_features.
#
# classified_events = []

# for onset_time in onsets:
#   start_sample = int(onset_time * sr)

# --- PADDING LOGIC (Prevents SciPy/Librosa STFT Warnings at End of File) ---
#  duration_secs = ONSET_SLICE_DURATION_MS / 1000.0
# end_sample = start_sample + int(duration_secs * sr)

# if end_sample > len(audio_data):
#    slice_data = audio_data[start_sample:]
#        pad_length = end_sample - len(audio_data)
#        y_window = np.pad(slice_data, (0, pad_length), mode='constant')
#    else:
#        y_window = audio_data[start_sample:end_sample]

#    if len(y_window) == 0:
#        continue

# 1. Extract the physics DNA
# LEGACY CODE - physics_profile = get_physics_profile(y_window, sr)
#    physics_profile = extract_features(y_window, sr)

# 2. Run the simultaneous rules
#    instruments = classify_event(y_window, sr)

# 3. Append with unified compatible keys
#    classified_events.append(
#        {
#            "time_sec": float(onset_time),
#            "instruments": instruments,
#            "debug_features": physics_profile
#        }
#    )

# return classified_events


# print("\n# ------------------------------------------------------------------------------------")
# LEGACY CODE (PRESERVING FOR EASE)
# Leave these uncommented so not to break orchestration and docs
# def analyze_event(y, sr):
#
#     # Calculates specific acoustic features:
#     # - f0: Fundamental Frequency (Peak Magnitude)
#     #- sc: Spectral Centroid (Brightness)
#     # - width: Spectral Bandwidth
#     # - depth: Decay Ratio (Sustain)
#
#     #:param y: Audio segment.
#     #:type y: np.ndarray
#     #:param sr: Sampling rate.
#     #:type sr: int
#     #:return: Dictionary of features [f0: (Fundamental Frequency (Peak Magnitude)),
#           sc: Spectral Centroid (Brightness), width: Spectral Bandwidth],
#       depth: Decay Ratio (Sustain)]
#     #:rtype: dict
#
#     # 1. FFT for Frequency Analysis
#     # High resolution (n_fft=2048) to see low frequencies clearly
#     # n_fft = 2048
#     # spec = np.abs(librosa.stft(y, n_fft=n_fft))
#     # freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
#     # n_fft = N_FFT
#     spec = np.abs(librosa.stft(y, n_fft=N_FFT))
#     freqs = librosa.fft_frequencies(sr=sr, n_fft=N_FFT)
#
#     # Sum magnitudes to find the strongest frequency (Fundamental)
#     sum_spec = np.sum(spec, axis=1)
#     peak_idx = np.argmax(sum_spec)
#     f0 = freqs[peak_idx]
#
#     # 2. Spectral Features
#     # sc = float(np.mean(librosa.feature.spectral_centroid(S=spec, sr=sr)))
#     # width = float(np.mean(librosa.feature.spectral_bandwidth(S=spec, sr=sr)))
#
#     sc = float(np.mean(librosa.feature.spectral_centroid(S=spec, sr=SAMPLE_RATE)))
#     width = float(np.mean(librosa.feature.spectral_bandwidth(S=spec, sr=SAMPLE_RATE)))
#     # 3. Depth / Decay (Sustain)
#     rms = librosa.feature.rms(y=y)[0]
#     split = len(rms) // 2
#     if np.mean(rms[:split]) < 1e-5:
#         decay = 0.0
#     else:
#         decay = np.mean(rms[split:]) / np.mean(rms[:split])
#
#     return {
#         "f0": float(f0),
#         "sc": float(round(sc, 2)),
#         "width": float(round(width, 2)),
#         "depth": float(round(decay, 2)),
#     }
#
#
# # Leave these uncommented so not to break orchestration and docs
# def classify_events_legacy (audio_data, sr, onsets) -> List[Dict[str, Any]]:
#     # Classifies hits strictly based on Fundamental Frequency ($f_0$) ranges.
#     # :param audio_data: Full audio array.
#     # :type audio_data: np.ndarray
#     # :param sr: Sampling rate.
#     # :type sr: int
#     # :param onsets: List of onset times.
#     # :type onsets: list
#     # :return: List of classified event dictionaries.
#     # :rtype: List[Dict[str, Any]]
#
#     classified_events = []
#
#     for onset_time in onsets:
#         # Extract 150ms window for analysis
#         start_sample = int(onset_time * sr)
#         end_sample = int((onset_time + 0.15) * sr)
#
#         if end_sample > len(audio_data):
#             end_sample = len(audio_data)
#         if start_sample >= end_sample:
#             continue
#
#         y_window = audio_data[start_sample:end_sample]
#         if len(y_window) == 0:
#             continue
#
#         # Analyze
#         features = analyze_event(y_window, sr)
#         f0 = features["f0"]
#
#         drum_type = None
#
#         # --- STRICT FREQUENCY RANGE CLASSIFICATION ---
#         # Order matters for overlaps
#
#         # 1. Low End
#         if KICK_RANGE[0] <= f0 <= KICK_RANGE[1]:
#             drum_type = "kick"
#         elif LOW_TOM_RANGE[0] <= f0 <= LOW_TOM_RANGE[1]:
#             drum_type = "low_tom"
#
#         # 2. Mids (Check Tom first to catch narrow band, then snare)
#         elif MID_TOM_RANGE[0] <= f0 <= MID_TOM_RANGE[1]:
#             drum_type = "mid_tom"
#         elif SNARE_RANGE[0] <= f0 <= SNARE_RANGE[1]:
#             drum_type = "snare"
#
#         # 3. Highs
#         elif OPEN_HAT_RANGE[0] <= f0 <= OPEN_HAT_RANGE[1]:
#             drum_type = "hi_hat_open"
#         elif CLOSED_HAT_RANGE[0] <= f0 <= CLOSED_HAT_RANGE[1]:
#             drum_type = "hi_hat_closed"
#         elif RIDE_RANGE[0] <= f0 <= RIDE_RANGE[1]:
#             drum_type = "ride"
#         elif CRASH_RANGE[0] <= f0 <= CRASH_RANGE[1]:
#             drum_type = "crash"
#
#         # If detected, append
#         if drum_type:
#             meta = DRUM_NOTATION_MAP[drum_type]
#             classified_events.append(
#                 {
#                     "drum_type": drum_type,
#                     "onset_time_seconds": round(onset_time, 2),
#                     "midi_pitch": meta["midi_program"],
#                     "note_head_type": meta["note_head"],
#                     "staff_position": meta["staff_position"],
#                     "analysis": features,
#                 }
#             )
#
#     return classified_events
