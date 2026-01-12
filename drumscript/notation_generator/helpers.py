# DrumScript/notation_generator/helpers.py

"""
Helper functions for musical calculations.
"""

import math
from . import constants
# from drumscript.notation_generator.constants import DURATION_WHOLE, DURATION_EIGHTH, DURATION_HALF, DURATION_QUARTER, DURATION_SIXTEENTH, DURATION_THIRTY_SECOND
from typing import Dict, Any # Added for type hinting


def round_to_nearest_subdivision(time_in_beats: float, subdivision: int) -> float:
    """
    Rounds a time value (in beats) to the nearest specified rhythmic subdivision.

    :param time_in_beats: Time in beats.
    :type time_in_beats: float
    :param subdivision: Subdivision grid (e.g., 16).
    :type subdivision: int
    :return: Quantized time in beats.
    :rtype: float
    """
    if subdivision == 0:
        raise ValueError("Subdivision cannot be zero.")

    unit_duration_in_beats = 4.0 / subdivision
        
    rounded_time = round(time_in_beats / unit_duration_in_beats) * unit_duration_in_beats
    return rounded_time

def get_note_duration_name(duration_beats: float, tempo_bpm: int) -> str:
    """
    Converts a duration in beats to a standard musical note name (e.g., 'quarter', 'eighth').
    This function can be further refined for more complex duration mappings (e.g., dotted notes).

    :param duration_beats: Duration in beats.
    :type duration_beats: float
    :param tempo_bpm: Tempo in BPM.
    :type tempo_bpm: int
    :return: Name of the note duration (e.g., 'quarter').
    :rtype: str
    """
    # This is a simplified mapping. For real applications, you might need a more robust system
    # that considers tempo and exact beat fractions.
    if abs(duration_beats - constants.DURATION_WHOLE) < 0.001:
        return 'whole'
    elif abs(duration_beats - constants.DURATION_HALF) < 0.001:
        return 'half'
    elif abs(duration_beats - constants.DURATION_QUARTER) < 0.001:
        return 'quarter'
    elif abs(duration_beats - constants.DURATION_EIGHTH) < 0.001:
        return 'eighth'
    elif abs(duration_beats - constants.DURATION_SIXTEENTH) < 0.001:
        return '16th'
    elif abs(duration_beats - constants.DURATION_THIRTY_SECOND) < 0.001:
        return '32nd'
    else:
        # Fallback for unexpected durations, or calculate based on smallest unit
        # For simplicity, returning a generic 'note' or 'n/th' for now
        return f"{duration_beats} beats" # Or raise an error, or round to nearest known duration

def format_drum_event(drum_type: str, onset_time_seconds: float) -> Dict[str, Any]:
    """
    Formats a classified drum event into a dictionary containing notation-specific information
    using the DRUM_NOTATION_MAP imported from constants.py

    :param drum_type: Type of drum (e.g., 'kick').
    :type drum_type: str
    :param onset_time_seconds: Time of onset.
    :type onset_time_seconds: float
    :return: Formatted event dictionary.
    :rtype: Dict[str, Any]
    """
    drum_info = constants.DRUM_NOTATION_MAP.get(drum_type)

    if not drum_info:
        print(f"Warning: No notation mapping found for drum type: {drum_type}. Using default kick properties.")
        # Fallback to a default, e.g., 'kick'
        drum_info = constants.DRUM_NOTATION_MAP['kick'] 
    
    formatted_event = {
        'drum_type': drum_type,
        'onset_time_seconds': onset_time_seconds,
        'midi_pitch': drum_info['midi_program'], # Get MIDI program from the map
        'note_head_type': drum_info['note_head'], # Get note head from the map
        'staff_position': drum_info['staff_position'], # Get staff position from the map
        'display_name': drum_info['display_name'] # Get display name from the map
    }
    return formatted_event

# Example of a simple mathematical helper (e.g., for musical interval calculations)
# This might be overkill depending on your needs, but shows the concept.
def calculate_cents_difference(freq1: float, freq2: float) -> float:
    """
    Formats a classified drum event into a dictionary containing notation-specific information. Calculates the difference between two frequencies in cents.
    Useful for tuning or pitch analysis:
     - freq1 (float): First frequency in Hz.
     - freq2 (float): Second frequency in Hz.
     - returns float: Difference in cents. Positive if freq2 is higher, negative if lower.

    Calculates the difference between two frequencies in cents.
    Useful for tuning or pitch analysis.

    :param freq1: First frequency in Hz.
    :type freq1: float
    :param freq2: Second frequency in Hz.
    :type freq2: float
    :return: Difference in cents. Positive if freq2 is higher, negative if lower.
    :rtype: float
    """

    if freq1 <= 0 or freq2 <= 0:
        raise ValueError("Frequencies must be positive.")
    return 1200 * math.log2(freq2 / freq1)