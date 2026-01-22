# DrumScript/notation_generator/constants.py

"""
This script defines ALL parameters used throughout modules in DrumScript
"""


# --- Configuration ---
# These should ideally be imported from a central 'constants.py'
# TO DO: Move these all to constants
# but for now, we'll keep them consistent by defining them here.
SAMPLE_RATE = 44100
SEGMENT_LENGTH_SECONDS = 0.2 # SEGMENT_LENGTH_SECONDS is the duration of the audio snapshot the script analyses at one time. To give two extremes. If you increase it (e.g., to 1.0): You would capture several drum hits in one fingerprint, making it impossible for the model to know which sound happened when, if you decrease it (e.g., to 0.05): You might only capture the initial "click" of the drum hit and miss the sound's body, losing important information. 0.2 is (seconds) is usually good-enough for drum events, ie kick+snare
HOP_LENGTH = 512
# HOP_LENGTH = 256
# NEW: Define a fixed duration for the audio slice to analyze around each onset
ONSET_SLICE_DURATION_MS = 200 # 200 milliseconds

# n_fft = 2048
# N_FFT = 1024 # N_FFT is the 'size of the window for the fourier transform" N_FFT = 1024 (Frequency Resolution)
N_FFT = 512 # This is the size of the analysis window for the Fourier Transform, which breaks the sound down into its constituent frequencies. A larger N_FFT gives you a more detailed picture of which frequencies are present but a less precise idea of exactly when they happened. If you increase it (e.g., to 2048): You get a very precise frequency analysis, which could help distinguish two very similar-sounding cymbals. If you decrease it (e.g., to 512): You get better timing precision but a "blurrier" picture of the frequencies.

DRUM_NOTATION_MAP = {
    # --- Bass Drums ---
    'kick': {
        'display_name': 'Kick Drum',
        'midi_program': 36,
        'note_head': 'normal',
        'staff_position': 'F3' # Bottom Space
    },
    'kick_clicky': {
        'display_name': 'Kick (Clicky)',
        'midi_program': 36,
        'note_head': 'normal',
        'staff_position': 'F3'
    },
    
    # --- Snare Drums ---
    'snare': {
        'display_name': 'Snare',
        'midi_program': 38,
        'note_head': 'normal',
        'staff_position': 'C4' # Space 3
    },
    
    # --- Hi-Hats ---
    'hi_hat_closed': {
        'display_name': 'Hi-Hat (Closed)',
        'midi_program': 42,
        'note_head': 'x',
        'staff_position': 'G4' # Above Top Line
    },
    'hi_hat_open': {
        'display_name': 'Hi-Hat (Open)',
        'midi_program': 46,
        'note_head': 'circle-x', 
        'staff_position': 'G4'
    },
    
    # --- Toms ---
    'high_tom': {
        'display_name': 'High Tom',
        'midi_program': 48,
        'note_head': 'normal',
        'staff_position': 'E4' # Top Space
    },
    'mid_tom': {
        'display_name': 'Mid Tom',
        'midi_program': 45,
        'note_head': 'normal',
        'staff_position': 'D4' # Line 4
    },
    'low_tom': {
        'display_name': 'Low Tom',
        'midi_program': 41,
        'note_head': 'normal',
        'staff_position': 'A3' # Space 2 (Floor Tom Position)
    },
    
    # --- Cymbals ---
    'crash': {
        'display_name': 'Crash Cymbal',
        'midi_program': 49,
        'note_head': 'x',
        'staff_position': 'A4' # Ledger Line Above
    },
    'ride': {
        'display_name': 'Ride Cymbal',
        'midi_program': 51,
        'note_head': 'x',
        'staff_position': 'F4' # Top Line
    }
}

# --- CLASSIFICATION ZONES (Refined based on Fundamental Frequencies) ---

# FUNDAMENTAL FREQUENCY RANGES (Hz) (Based on testing audio manually)
# Copy and comment out most recent previous freq for reference, when amending
# KICK_RANGE = (50, 60)
KICK_RANGE = (64, 87) # majority of kick drum fundaemtals either 64.60 or 86.13 HZ, so this is a good baseline
# LOW_TOM_RANGE = (90, 110)
# SNARE_RANGE = (120, 240)
LOW_TOM_RANGE = (88, 118) # ie between snare and kick??
SNARE_RANGE = (119, 216) # majority of snares in this range, per my analysis
SNARE_SPECTRAL_CENTROID = (3000, 5000)  # majority of snares in this range, per my analysis. Could also be MAX 6000
MID_TOM_RANGE = (217, 350) # these ranges are GUESSWORK, based on snare  fundemtnal freq analysis
HIGH_TOM_RANGE = (351, 450) # these ranges are GUESSWORK, based on snare  fundemtnal freq analysis
OPEN_HAT_RANGE = (240, 400) # Fundamental frequency
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
#DURATION_WHOLE = 4.0
#DURATION_HALF = 2.0
#DURATION_QUARTER = 1.0
#DURATION_EIGHTH = 0.5
#DURATION_SIXTEENTH = 0.25
#DURATION_THIRTY_SECOND = 0.125

# --- General MIDI Standard Percussion Map ---
# These are common MIDI note numbers for drum sounds.
# Ensure these align with your model's classification output and desired notation.
#MIDI_KICK = 36          # C2 on piano
#MIDI_SNARE_ACOUSTIC = 38 # D2 on piano
#MIDI_SNARE_SIDE_STICK = 37 # C#2
#MIDI_HI_HAT_CLOSED = 42 # F#2
#MIDI_HI_HAT_PEDAL = 44  # G#2
#MIDI_HI_HAT_OPEN = 46   # A#2
#MIDI_CRASH_CYMBAL_1 = 49 # C#3
#MIDI_RIDE_CYMBAL_1 = 51  # D#3
#MIDI_TOM_HIGH = 50       # D3
#MIDI_TOM_MID = 47       # A2
#MIDI_TOM_LOW = 45       # G2#

# --- Notation Symbols / Mapping Hints ---
# These are conceptual for score generation (e.g., using MusicXML or a drawing library)
# Actual rendering depends on the chosen notation library/method.
#NOTEHEAD_NORMAL = 'normal'
#NOTEHEAD_X = 'x' # For cymbals, hi-hats, often snare side stick

# --- Staff Positions (conceptual, depends on rendering library's coordinate system) ---
# These might relate to MIDI pitch or specific lines/spaces on a percussion staff.
# For a 5-line percussion staff, these are relative positions.
# Actual Y-coordinates would be calculated by pdf_exporter or score_builder.
#STAFF_POS_KICK = -2    # Example relative position for kick drum
#STAFF_POS_SNARE = 0    # Example relative position for snare drum
#STAFF_POS_HI_HAT = 2   # Example relative position for hi-hat
# ... and so on for other drums

#STAFF_POS_SNARE = 0 #This is the baseline (e.g., the 3rd space).
#STAFF_POS_KICK = -2 
#STAFF_POS_HIHAT_OPEN = 7
#STAFF_POS_HIHAT_CLOSED = -4 
#STAFF_POS_RIDE = 6
#STAFF_POS_CRASH = 8
#STAFF_POS_TOM1 = 3 
#STAFF_POS_TOM2 = 4 
#STAFF_POS_TOM3 = 5


