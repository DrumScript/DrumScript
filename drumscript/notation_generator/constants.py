# DrumScript/notation_generator/constants.py

# Master map for drum notation, referencing midi_percussion_map.csv
# This map MUST include all drum types output by drum_classifier/predict.py
# and all keys required by notation_generator/score_builder.py and helpers.py


DRUM_NOTATION_MAP = {
    # --- Bass Drums ---
    'kick': {
        'display_name': 'Kick Drum',
        'midi_program': 36,
        'note_head': 'normal',
        'staff_position': 'F3' # Bottom Space (Space 1)
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
        'staff_position': 'C4' # Space 3 (Second space from top)
    },
    
    # --- Hi-Hats ---
    'hi_hat_closed': {
        'display_name': 'Hi-Hat (Closed)',
        'midi_program': 42,
        'note_head': 'x',
        'staff_position': 'G4' # Sitting above the top line
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
        'staff_position': 'A3' # Space 2
    },
    
    # --- Cymbals ---
    'crash': {
        'display_name': 'Crash Cymbal',
        'midi_program': 49,
        'note_head': 'x',
        'staff_position': 'A4' # Ledger line above staff
    },
    'ride': {
        'display_name': 'Ride Cymbal',
        'midi_program': 51,
        'note_head': 'x',
        'staff_position': 'F4' # Top Line
    }
}

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
#MIDI_KICK = 36         # C2 on piano
#MIDI_SNARE_ACOUSTIC = 38 # D2 on piano
#MIDI_SNARE_SIDE_STICK = 37 # C#2
#MIDI_HI_HAT_CLOSED = 42 # F#2
#MIDI_HI_HAT_PEDAL = 44  # G#2
#MIDI_HI_HAT_OPEN = 46   # A#2
#MIDI_CRASH_CYMBAL_1 = 49 # C#3
#MIDI_RIDE_CYMBAL_1 = 51  # D#3
#MIDI_TOM_HIGH = 50      # D3
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