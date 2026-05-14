# DrumScript/notation_generator/constants.py

"""
This script defines ALL parameters used throughout modules in DrumScript
"""

# --- GLOBAL AUDIO CONFIG ---
# --- Configuration ---
# These should ideally be imported from a central 'constants.py'
# TO DO: Move these all to constants
# but for now, we'll keep them consistent by defining them here.
SAMPLE_RATE = 44100
SEGMENT_LENGTH_SECONDS = 0.2  # SEGMENT_LENGTH_SECONDS is the duration of the audio snapshot the script analyses at one time. To give two extremes.
# If you increase it (e.g., to 1.0): You would capture several drum hits in one fingerprint, making it impossible for the model to know which sound
# happened when, if you decrease it (e.g., to 0.05): You might only capture the initial "click" of the drum hit and miss the sound's body, losing
# important information. 0.2 is (seconds) is usually good-enough for drum events, ie kick+snare
# HOP_LENGTH = 512
# HOP_LENGTH = 256
HOP_LENGTH = 128
# HOP_LENGTH = 64
# NEW: Define a fixed duration for the audio slice to analyze around each onset
ONSET_SLICE_DURATION_MS = 200  # 200 milliseconds

# n_fft = 2048
# N_FFT = 1024 # N_FFT is the 'size of the window for the fourier transform" N_FFT = 1024 (Frequency Resolution)
# N_FFT = 512 # This is the size of the analysis window for the Fourier Transform, which breaks the sound down into its constituent frequencies.
# A larger N_FFT gives you a more detailed picture of which frequencies are present but a less precise idea of exactly when they happened.
# If you increase it (e.g., to 2048): You get a very precise frequency analysis, which could help distinguish two very similar-sounding cymbals.
# If you decrease it (e.g., to 512): You get better timing precision but a "blurrier" picture of the frequencies.

N_FFT = 2048

# --- CLASSIFICATION ZONES (Refined based on Fundamental Frequencies) ---

# FUNDAMENTAL FREQUENCY RANGES (Hz) (Based on testing audio manually)
# Copy and comment out most recent previous freq for reference, when amending
# KICK_RANGE = (50, 60)
KICK_RANGE = (64, 87)  # majority of kick drum fundaemtals either 64.60 or 86.13 HZ, so this is a good baseline
# LOW_TOM_RANGE = (90, 110)
# SNARE_RANGE = (120, 240)
LOW_TOM_RANGE = (88, 118)  # ie between snare and kick??
SNARE_RANGE = (119, 216)  # majority of snares in this range, per my analysis
SNARE_SPECTRAL_CENTROID = (3000, 5000)  # majority of snares in this range, per my analysis. Could also be MAX 6000
MID_TOM_RANGE = (217, 350)  # these ranges are GUESSWORK, based on snare fundamental freq analysis
HIGH_TOM_RANGE = (351, 450)  # these ranges are GUESSWORK, based on snare fundamental freq analysis
OPEN_HAT_RANGE = (240, 400)  # Fundamental frequency
CLOSED_HAT_RANGE = (400, 450)
RIDE_RANGE = (450, 550)
CRASH_RANGE = (550, 8000)


# Overlap Handling:
# MID_TOM (120-150) is inside SNARE (120-240).
# The classifier will check MID_TOM first. If identified, it stops.

# LEGACY BANDS (Commented out to replace with specific ranges above)
# BAND_LOW = (20, 800)
# BAND_MID = (800, 5000)
# BAND_HIGH = (5000, 16000)

# --- ENERGY THRESHOLDS ---
# If energy in a specific band exceeds this ratio of the TOTAL energy, we trigger it.
THRESH_KICK = 0.15
THRESH_SNARE = 0.15
THRESH_HAT = 0.10
THRESH_CYMBAL = 0.10

# --- SECONDARY FEATURES ---
CLOSED_HAT_MAX_DECAY = 0.25
CRASH_MIN_DECAY = 0.45
NOISE_THRESH_SNARE = 0.05


# legacy: keep for now
# Add more drum types as classified by your model
# Example for other possible drum types (already present in the original file, just for context):
# 'floor_tom': {'note_head': 'normal', 'STAFF_POS': 'A2'}, # A2 for floor tom
# 'mid_tom': {'note_head': 'normal', 'STAFF_POS': 'B2'}, # B2 for mid tom

# --- Musical Durations ---
# Common note durations as fractions of a whole note (1.0 means whole note)
DURATION_WHOLE = 4.0
DURATION_HALF = 2.0
DURATION_QUARTER = 1.0
DURATION_EIGHTH = 0.5
DURATION_SIXTEENTH = 0.25
DURATION_THIRTY_SECOND = 0.125

# --- General MIDI Standard Percussion Map ---
# These are common MIDI note numbers for drum sounds.
# Ensure these align with your model's classification output and desired notation.
# MIDI_KICK = 36          # C2 on piano
# MIDI_SNARE_ACOUSTIC = 38 # D2 on piano
# MIDI_SNARE_SIDE_STICK = 37 # C#2
# MIDI_HI_HAT_CLOSED = 42 # F#2
# MIDI_HI_HAT_PEDAL = 44  # G#2
# MIDI_HI_HAT_OPEN = 46   # A#2
# MIDI_CRASH_CYMBAL_1 = 49 # C#3
# MIDI_RIDE_CYMBAL_1 = 51  # D#3
# MIDI_TOM_HIGH = 50       # D3
# MIDI_TOM_MID = 47       # A2
# MIDI_TOM_LOW = 45       # G2#

# --- Notation Symbols / Mapping Hints ---
# These are conceptual for score generation (e.g., using MusicXML or a drawing library)
# Actual rendering depends on the chosen notation library/method.
# NOTEHEAD_NORMAL = 'normal'
# NOTEHEAD_X = 'x' # For cymbals, hi-hats, often snare side stick

# --- Staff Positions (conceptual, depends on rendering library's coordinate system) ---
# These might relate to MIDI pitch or specific lines/spaces on a percussion staff.
# For a 5-line percussion staff, these are relative positions.
# Actual Y-coordinates would be calculated by pdf_exporter or score_builder.
# STAFF_POS_KICK = -2    # Example relative position for kick drum
# STAFF_POS_SNARE = 0    # Example relative position for snare drum
# STAFF_POS_HI_HAT = 2   # Example relative position for hi-hat
# ... and so on for other drums

# STAFF_POS_SNARE = 0 #This is the baseline (e.g., the 3rd space).
# STAFF_POS_KICK = -2
# STAFF_POS_HIHAT_OPEN = 7
# STAFF_POS_HIHAT_CLOSED = -4
# STAFF_POS_RIDE = 6
# STAFF_POS_CRASH = 8
# STAFF_POS_TOM1 = 3
# STAFF_POS_TOM2 = 4
# STAFF_POS_TOM3 = 5

# Physical Constants for DrumScript Classification.
# i. --- KICK DRUM PHYSICS ---
# Analysis Source: 20 user-provided wav files (7 Feb 2026)
# Range observed: Peak Freq 43-129Hz | LFER 46-99%
# Derived from audio analysis of 5 sample kick drum beats (kick_0001 to kick_0005)
KICK_MIN_PEAK_FREQ = 40.0  # Hz
KICK_FREQ_MIN = 40.0  # Hz
# KICK_MAX_PEAK_FREQ = 100.0  # Hz
KICK_MAX_PEAK_FREQ = 100.0  # Hz/
KICK_FREQ_MAX = 140.0  # Hz (Safety margin above observed 129Hz)
KICK_MAX_CENTROID = 400.0  # Hz (Generous upper bound, refined by LFER)
# KICK_MIN_LFER = 0.50        # Min 50% of energy must be below 150Hz [UPDATE weds-25-mar-26: commenting out due to duplication (ie KICK_MIN_LFER)]
# KICK_LFER_MIN = 0.40   # 40% (Safety margin below observed 46.9%)
# KICK_LFER_MIN = 0.32  # Min 32% energy must be < 150Hz [UPDATE weds-25-mar-26: added in]

# 2. --- SNARE DRUM PHYSICS ---
# Analysis Source: 20 user-provided wav files
# Range: Peak Freq 64-366Hz | Centroid 1300-6000Hz

# 1. The "Body" Check (Fundamental Frequency)
# Most snares sit here. If a sound is here, it's almost certainly a snare.
# SNARE_FREQ_MIN = 130.0  # Hz (Just above the Kick's max of 129Hz)
# SNARE_FREQ_MAX = 400.0  # Hz

# 2. The "Wire" Check (High Frequency Energy > 2000Hz)
# Used as a tie-breaker for deep snares (like snare_0004) vs clicky kicks.
# A kick typically has < 15% high energy. A snare typically has > 20%.
# SNARE_HFER_MIN = 0.20  # 20%

# 3. -- TOM PHYSICS ---
# Analysis Source: 15 user-provided wav files, from dugg-funnie reverse tom dataset
# low, mid and high-tom data provided.
# Characteristics: Extremely low high-freq energy, long decay.

# Frequency Buckets (for classification)
# TOM_FREQ_LOW_MAX = 95.0  # Hz (Below this is Low Tom)
# TOM_FREQ_MID_MAX = 135.0  # Hz (95-135 is Mid Tom, above is High)
# TOM_FREQ_MID_MAX = 120.0

# Physics Rules
TOM_HFER_MAX = 0.05  # Max 5% high freq energy (Toms are not "hisssy")
# TOM_MIN_DECAY = 0.30  # Seconds. (Kicks usually < 0.25s, Toms > 0.35s)

# DrumScript/notation_generator/constants.py

"""
PHYSICS CONSTANTS FOR DRUM CLASSIFICATION
Derived from iterative analysis of user audio samples (Feb 2026).
"""

# ==============================================================================
# CLASS 1: MEMBRANOPHONES (SKINS)
# Characteristics: Fundamental pitch, harmonic structure, lower frequency center.
# ==============================================================================

# A. KICK DRUM (Sub-Bass, Short Decay)
KICK_FREQ_MIN = 40.0  # Hz
KICK_FREQ_MAX = 140.0  # Hz
# KICK_LFER_MIN = 0.40    # Min 40% energy must be < 150Hz  [UPDATE weds-25-mar-26: commenting out due to duplication (ie KICK_MIN_LFER)]
KICK_LFER_MIN = 0.32  # Min 32% energy must be < 150Hz [UPDATE weds-25-mar-26: commenting out due to duplication (ie KICK_MIN_LFER, ~line 207 above)]
KICK_MAX_DECAY = 0.25  # Seconds (Thud)

# B. SNARE DRUM (Wire Noise + Body)
# Note: Frequency overlaps with High Toms. "Wire Energy" is the key separator.
SNARE_FREQ_MIN = 120.0
SNARE_FREQ_MAX = 450.0
SNARE_HFER_MIN = 0.15  # Minimum 15% energy > 2000Hz (Wires)

# C. TOMS (Pure Tones, Resonance)
# Characterized by LOW high-freq energy and LONG decay vs Kicks.
TOM_MIN_DECAY = 0.28  # Seconds (Separates Low Tom from Kick)
TOM_MAX_WIRE_ENERGY = 0.05  # Max 5% energy > 2kHz (Toms are not buzzy)

# Tom Frequency Buckets
TOM_FREQ_LOW_MAX = 92.0  # Hz (Separates 86Hz Low Tom from 96Hz Mid Tom)
TOM_FREQ_MID_MAX = 120.0  # Hz (Separates 118Hz Mid Tom from 140Hz High Tom)
# TOM_FREQ_MID_MAX = 135.0  # Hz (Separates 118Hz Mid Tom from 140Hz High Tom)
# Anything > 135Hz (and not a snare) is a High Tom.


# ==============================================================================
# CLASS 2: IDIOPHONES (METALS)
# Characteristics: Inharmonic, high energy > 5kHz.
# ==============================================================================

# SEPARATION FROM SKINS
# If energy > 5000Hz is above this threshold, it is Metal.
IDIOPHONE_MIN_HFER_5K = 0.15

# A. HI-HATS (Decay-Based Separation)
# Closed Hat: Very tight. (Avg obs: 0.12s)
HAT_CLOSED_MAX_DECAY = 0.30  # Seconds

# Open Hat: Medium sustain. (Avg obs: 0.42s)
HAT_OPEN_MIN_DECAY = 0.30
HAT_OPEN_MAX_DECAY = 0.60  # Seconds (Separates Open Hat from Paperthin Crash 0.7s)

# B. CYMBALS (Long Decay + Centroid Separation)
# Any metal ringing > 0.60s is a Cymbal.
CYMBAL_MIN_DECAY = 0.60

# Centroid: The "Brightness" Check.
# Rides are "Dark" (Gong-like, ~3000Hz). Crashes are "Bright" (Explosive, ~4800Hz).
CYMBAL_CENTROID_THRESHOLD = 4000.0  # Hz


""" LEGACY MAPPING (KEEP FOR NOW)
DRUM_NOTATION_MAP = {
    # --- Bass Drums ---
    "kick": {
        "display_name": "Kick Drum",
        "midi_program": 36,
        "note_head": "normal",
        "staff_position": "F3",  # Bottom Space
    },
    "kick_clicky": {  # TO DO: MIGHT DELETE IN FUTURE IF TEMPORAL MODEL IS BETTER, THEN THE 'CLICKY KICK' WOULD JUST BECOME A VERY FAST KICK
        "display_name": "Kick (Clicky)",
        "midi_program": 36,
        "note_head": "normal",
        "staff_position": "F3",
    },
    # --- Snare Drums ---
    "snare": {
        "display_name": "Snare",
        "midi_program": 38,
        "note_head": "normal",
        "staff_position": "C4",  # Space 3
    },
    # --- Hi-Hats --- # assumes edge hit
    "hi_hat_closed": {
        "display_name": "Hi-Hat (Closed)",
        "midi_program": 42,
        "note_head": "x",
        "staff_position": "G4",  # Above Top Line
    },
    "hi_hat_open": {  # assumes edge hit
        "display_name": "Hi-Hat (Open)",
        "midi_program": 46,
        "note_head": "circle-x",
        "staff_position": "G4",
    },
    # --- Toms ---
    "high_tom": {
        "display_name": "High Tom",
        "midi_program": 48,
        "note_head": "normal",
        "staff_position": "E4",  # Top Space
    },
    "mid_tom": {
        "display_name": "Mid Tom",
        "midi_program": 45,
        "note_head": "normal",
        "staff_position": "D4",  # Line 4
    },
    "low_tom": {
        "display_name": "Low Tom",
        "midi_program": 41,
        "note_head": "normal",
        "staff_position": "A3",  # Space 2 (Floor Tom Position)
    },
    # --- Cymbals ---
    "crash": {  # assumes edge hit
        "display_name": "Crash Cymbal",
        "midi_program": 49,
        "note_head": "x",
        "staff_position": "A4",  # Ledger Line Above
    },
    "ride": {  # assumes edge hit
        "display_name": "Ride Cymbal",
        "midi_program": 51,
        "note_head": "x",
        "staff_position": "F4",  # Top Line
    },
}"""

"""
LEGACY MAPPING (KEEP FOR NOW)
# ==============================================================================
# NOTATION MAPPING (Used by Score Builder)
# ==============================================================================
DRUM_NOTATION_MAP = {
    "kick": {"midi_program": 36, "note_head": "normal", "staff_position": "F3"},
    "snare": {"midi_program": 38, "note_head": "normal", "staff_position": "C4"},
    "low_tom": {"midi_program": 41, "note_head": "normal", "staff_position": "A3"},
    "mid_tom": {"midi_program": 45, "note_head": "normal", "staff_position": "D4"},
    "high_tom": {"midi_program": 48, "note_head": "normal", "staff_position": "E4"},
    "hi_hat_closed": {"midi_program": 42, "note_head": "x", "staff_position": "G4"},  # assumes edge hit
    "hi_hat_open": {"midi_program": 46, "note_head": "circle-x", "staff_position": "G4"},  # assumes edge hit
    "crash": {"midi_program": 49, "note_head": "x", "staff_position": "A4"},  # assumes edge hit
    "ride": {"midi_program": 51, "note_head": "x", "staff_position": "F4"},  # assumes edge hit
}
"""

# ==============================================================================
# NOTATION MAPPING (Used by Score Builder)
# ==============================================================================
DRUM_NOTATION_MAP = {
    # --- Bass Drums ---
    "kick": {
        "display_name": "Kick Drum",
        "midi_program": 36,
        "note_head": "normal",
        "staff_position": "F3",  # Bottom Space
    },
    # --- Snare Drums ---
    "snare": {
        "display_name": "Snare",
        "midi_program": 38,
        "note_head": "normal",
        "staff_position": "C4",  # Space 3
    },
    # --- Toms ---
    "low_tom": {
        "display_name": "Low Tom",
        "midi_program": 41,
        "note_head": "normal",
        "staff_position": "A3",  # Space 2 (Floor Tom Position)
    },
    "mid_tom": {
        "display_name": "Mid Tom",
        "midi_program": 45,
        "note_head": "normal",
        "staff_position": "D4",  # Line 4
    },
    "high_tom": {
        "display_name": "High Tom",
        "midi_program": 48,
        "note_head": "normal",
        "staff_position": "E4",  # Top Space
    },
    # --- Hi-Hats --- # assumes edge hit
    "hi_hat_closed": {
        "display_name": "Hi-Hat (Closed)",
        "midi_program": 42,
        "note_head": "x",
        "staff_position": "G4",  # Above Top Line
    },
    "hi_hat_open": {
        "display_name": "Hi-Hat (Open)",
        "midi_program": 46,
        "note_head": "circle-x",
        "staff_position": "G4",
    },
    # --- Cymbals --- # assumes edge hit
    "crash": {
        "display_name": "Crash Cymbal",
        "midi_program": 49,
        "note_head": "x",
        "staff_position": "A4",  # Ledger Line Above
    },
    "ride": {
        "display_name": "Ride Cymbal",
        "midi_program": 51,
        "note_head": "x",
        "staff_position": "F4",  # Top Line
    },
}
