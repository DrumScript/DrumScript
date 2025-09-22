# DrumScript/notation_generator/constants.py

# A standardized map based on the General MIDI Level 1 Percussion Key Map.
# This map links the drum type (as might be classified by an ML model)
# to its standard notation properties.
DRUM_NOTATION_MAP = {
    'kick': {
        'midi_pitch': 36,      # MIDI Key# 36 is Bass Drum 1
        'staff_pos': 'F2',     # Standard notation staff position for kick
        'note_head': 'normal', # Standard notehead
        'display_name': 'Bass Drum'
    },
    'snare': {
        'midi_pitch': 38,      # MIDI Key# 38 is Acoustic Snare
        'staff_pos': 'C3',     # Standard notation staff position for snare
        'note_head': 'normal',
        'display_name': 'Snare Drum'
    },
    'hi-hat_closed': {
        'midi_pitch': 42,      # MIDI Key# 42 is Closed Hi-Hat
        'staff_pos': 'F#3',    # Often placed on the top line or space above
        'note_head': 'x',      # 'x' notehead is standard for cymbals/hi-hats
        'display_name': 'Hi-Hat (Closed)'
    },
    'hi-hat_open': {
        'midi_pitch': 46,      # MIDI Key# 46 is Open Hi-Hat
        'staff_pos': 'G#3',    # Often placed above the closed hi-hat position
        'note_head': 'x',
        'display_name': 'Hi-Hat (Open)'
    },
    'crash_cymbal': {
        'midi_pitch': 49,      # MIDI Key# 49 is Crash Cymbal 1
        'staff_pos': 'C#4',    # Typically placed on a ledger line above the staff
        'note_head': 'x',
        'display_name': 'Crash Cymbal'
    },
    'ride_cymbal': {
        'midi_pitch': 51,      # MIDI Key# 51 is Ride Cymbal 1
        'staff_pos': 'A3',     # Often placed on the top line of the staff
        'note_head': 'x',
        'display_name': 'Ride Cymbal'
    },
    'high_tom': {
        'midi_pitch': 50,      # MIDI Key# 50 is High Tom
        'staff_pos': 'E3',
        'note_head': 'normal',
        'display_name': 'High Tom'
    },
    'low_tom': {
        'midi_pitch': 45,      # MIDI Key# 45 is Low Tom
        'staff_pos': 'A2',
        'note_head': 'normal',
        'display_name': 'Low Tom'
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