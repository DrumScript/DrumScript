    # The JSON file is in the drum_classifier directory
# DrumScript/notation_generator/score_builder.py

import music21
from typing import List, Dict, Any
from collections import defaultdict
from drumscript.notation_generator import constants
from drumscript.notation_generator.constants import DRUM_NOTATION_MAP # Assuming constants.py defines DRUM_NOTATION_MAP
from drumscript.notation_generator.helpers import round_to_nearest_subdivision, get_note_duration_name # Assuming these are useful
from drumscript.notation_generator.pdf_exporter import generate_pdf # To actually export the PDF

def get_drum_music21_note_info(drum_type: str) -> Dict[str, Any]:
    """
    Retrieves music21-specific notation info for a given drum type from constants.DRUM_NOTATION_MAP.
    """
    drum_map = constants.DRUM_NOTATION_MAP.get(drum_type)
    if not drum_map:
        print(f"Warning: No notation mapping found for drum type: {drum_type}. Using default kick.")
        drum_map = constants.DRUM_NOTATION_MAP['kick'] # Fallback
    
    # music21.pitch.Pitch needs a nameWithOctave (e.g., 'F2', 'C3')
    # music21.note.Unpitched needs a displayStep and displayOctave or a MIDI number
    # The constants.py currently uses 'F2', 'C3' directly for staff_position, which is good.
    
    # We can use music21.pitch.Pitch to parse these string representations
    # and get the MIDI number or display pitch properties for Unpitched notes.
    

    # Use the 'staff_position' string for visual placement and the 'midi_program' for sound.
    # music21's Unpitched note uses .pitch.midi for positioning/playback.
    # The 'display_step' and 'display_octave' are derived from the staff_position.
    pitch_obj = music21.pitch.Pitch(drum_map['staff_position'])
    
    return {
        'midi_pitch': drum_map['midi_program'], # Use midi_program from map for accurate playback
        'note_head': drum_map['note_head'],
        'display_step': pitch_obj.step,     # E.g., 'F', 'C' - for visual staff placement
        'display_octave': pitch_obj.octave  # E.g., 2, 3 - for visual staff placement
    }


def build_and_export_drum_score(
    detected_events: List[Dict[str, Any]],
    tempo: int = 120, # This is a fallback tempo, but will be overwritten when estimate_tempo is called through main, keep as is for now
    output_filepath: str = "output_drum_sheet.pdf",
    quantization_subdivision: int = 16 # e.g., 4 for quarter, 8 for eighth, 16 for sixteenth
):
    """
    Builds a music21 score from detected multi-label drum events and exports it to PDF.

    Args:
        detected_events (List[Dict[str, Any]]): List of detected drum events.
                                                Each event dict contains 'time' and 'drums' (list of strings).
                                                e.g., [{'time': 0.1, 'drums': ['kick', 'hi-hat']}, ...]
        tempo (int): Tempo in BPM for quantization.
        output_filepath (str): Full path where the PDF file should be saved.
        quantization_subdivision (int): Rhythmic subdivision to quantize to (e.g., 16 for 16th notes).
    """
    print("Building music21 score...")

    # Create a new Score object
    score = music21.stream.Score()
    score.metadata = music21.metadata.Metadata()
    score.metadata.title = "Drum Transcription"
    score.metadata.composer = "DrumScript AI"

    # Create a percussion Part
    drum_part = music21.stream.Part()
    drum_part.id = 'DrumKit'
    drum_part.partName = 'Drum Kit'
    drum_part.partAbbreviation = 'Dms.'

    # --- ADDED: Percussion Clef and Time Signature for proper notation display ---
    drum_part.append(music21.clef.PercussionClef())
    drum_part.append(music21.meter.TimeSignature('4/4')) # Using a default 4/4 time signature
    # ---------------------------------------------------------------------------

    # Add a Percussion instrument to the part (important for music21 to know it's a drum part)
    drum_part.append(music21.instrument.Percussion())

    # Add a tempo indication
    metronome = music21.tempo.MetronomeMark(number=tempo)
    drum_part.append(metronome)

    # Group events by quantized time to handle simultaneous hits
    # Dictionary to store {quantized_time_beats: [list_of_drum_types_at_that_time]}
    events_by_quantized_time = defaultdict(list)

    for event in detected_events:
        # FIX 1: Use the correct key 'onset_time_seconds'
        onset_time_seconds = event['onset_time_seconds'] 

        # FIX 2: Get the single 'drum_type' from the event
        drum_type = event['drum_type'] 

        # Convert seconds to beats
        time_in_beats = (onset_time_seconds / 60.0) * tempo

        # Quantize the time to the nearest musical subdivision
        quantized_time_beats = round_to_nearest_subdivision(time_in_beats, quantization_subdivision)

        # Add this single drum type to the list for this quantized time
        events_by_quantized_time[quantized_time_beats].append(drum_type)

    # Sort events by quantized time
    sorted_quantized_times = sorted(events_by_quantized_time.keys())

    # Iterate through quantized times and create music21 notes/chords
    last_offset = 0.0
    for quantized_time_beats in sorted_quantized_times:
        current_offset = quantized_time_beats # Offset in quarterLength (beats)

        # Handle rests if there's a gap between the last event and the current one
        if current_offset > last_offset:
            rest_duration = current_offset - last_offset
            if rest_duration > 0.001: # Avoid adding tiny, negligible rests
                rest = music21.note.Rest()
                rest.duration.quarterLength = rest_duration
                drum_part.append(rest)
        
        drums_at_this_time = events_by_quantized_time[quantized_time_beats]
        
        if len(drums_at_this_time) == 1:
            # Single drum hit at this time
            drum_type = drums_at_this_time[0]
            note_info = get_drum_music21_note_info(drum_type)
            
            # Use music21.note.Unpitched for percussion notes
            n = music21.note.Unpitched()
            n.storedInstrument = music21.instrument.Percussion()
            n.pitch = music21.pitch.Pitch() # Create a dummy pitch object to set properties
            n.pitch.midi = note_info['midi_pitch'] # Set MIDI pitch for playback/positioning
            n.notehead = note_info['note_head']
            n.duration.quarterLength = (4.0 / quantization_subdivision) # Duration of one subdivision (e.g., 16th note)
            drum_part.append(n)

        elif len(drums_at_this_time) > 1:
            # Multiple drum hits at this time (create a PercussionChord)
            
            notes_in_chord = []
            for drum_type in drums_at_this_time:
                note_info = get_drum_music21_note_info(drum_type)
                
                # Create an Unpitched note for each drum type in the chord
                up = music21.note.Unpitched()
                up.storedInstrument = music21.instrument.Percussion()
                #up.pitch = music21.pitch.Pitch()
                #up.pitch.midi = note_info['midi_pitch']
                pitch_for_display = music21.pitch.Pitch(note_info['staff_position'])
                up.displayStep = pitch_for_display.step
                up.displayOctave = pitch_for_display.octave
                up.midi = note_info['midi_pitch']
                up.notehead = note_info['note_head']
                notes_in_chord.append(up)
            
            # Create a PercussionChord from the list of Unpitched notes
            p_chord = music21.percussion.PercussionChord(notes_in_chord)
            p_chord.duration.quarterLength = (4.0 / quantization_subdivision) # Duration of one subdivision
            drum_part.append(p_chord)
        
        last_offset = current_offset + (4.0 / quantization_subdivision) # Update last offset for rest calculation


    score.append(drum_part)

    # --- Export to PDF ---
    # The generate_pdf function in pdf_exporter.py already handles music21 Stream to PDF conversion
    # It takes a score-like object and an output filepath.
    generate_pdf(score, output_filepath) # Pass the music21 score directly

    print(f"Music21 score built and ready for export to {output_filepath}")

    return score

# You might also want a separate function to just build the score object
# if you want to inspect it before exporting, but for now, this combined
# function is straightforward for the main script.