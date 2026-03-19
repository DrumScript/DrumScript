# DrumScript/notation_generator/_midi_exporter.py
"""
This module takes classified drum events and renders them into a standard MIDI file.
"""
import os
import pretty_midi
from drumscript.notation_generator.constants import DRUM_NOTATION_MAP

def export_to_midi(classified_events: list[dict], output_filepath: str, tempo: float = 120.0):
    """
    Takes a list of event dictionaries and writes a standard .mid file.
    
    :param classified_events: List of dicts containing 'time_sec' and 'instruments'.
    :param output_filepath: Where to save the file (e.g., 'output/drum_score.mid').
    :param tempo: The detected BPM of the track.
    """
    # 1. Initialize a new MIDI object with the detected tempo
    midi = pretty_midi.PrettyMIDI(initial_tempo=tempo)
    
    # 2. Create a Drum Track (program=0, is_drum=True forces it to MIDI Channel 10)
    drum_track = pretty_midi.Instrument(program=0, is_drum=True, name="DrumScript Output")
    
    # 3. Loop through your beautifully classified timeline
    for event in classified_events:
        time_sec = event["time_sec"]
        instruments = event["instruments"]
        
        # Multiple instruments can hit at the exact same millisecond!
        for inst in instruments:
            # Check if our physics engine spit out an instrument we have in our map
            if inst in DRUM_NOTATION_MAP:
                midi_pitch = DRUM_NOTATION_MAP[inst]['midi_program']
                
                # Create the MIDI Note. 
                # (Drums don't hold sustain, so a 0.1s duration is standard for sheet music)
                note = pretty_midi.Note(
                    velocity=100,             # Default strong hit
                    pitch=midi_pitch,         # E.g., 36 for Kick, 38 for Snare
                    start=time_sec,           # The exact millisecond from onset_detector
                    end=time_sec + 0.1        
                )
                
                drum_track.notes.append(note)
            else:
                # If the classifier guessed 'unknown', we skip it for the clean score
                pass
                
    # 4. Add the finished track to the file and save it
    midi.instruments.append(drum_track)
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(output_filepath), exist_ok=True)
    midi.write(output_filepath)
    
    print(f"\nSUCCESS: MIDI file generated at -> {output_filepath}")