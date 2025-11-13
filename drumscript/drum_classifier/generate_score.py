# DrumScript/drum_classifier/generate_score.py

import os
import sys
import json
import music21
from collections import defaultdict
import math
from typing import List, Dict, Any
from drumscript.notation_generator.constants import DRUM_NOTATION_MAP

# --- Embedded Helper Functions (from notation_generator/helpers.py) ---
def round_to_nearest_subdivision(time_in_beats: float, subdivision: int) -> float:
    """
    Rounds a time value (in beats) to the nearest specified rhythmic subdivision.
    """
    if subdivision == 0:
        raise ValueError("Subdivision cannot be zero.")

    unit_duration_in_beats = 4.0 / subdivision
    rounded_time = round(time_in_beats / unit_duration_in_beats) * unit_duration_in_beats
    return rounded_time

def get_drum_music21_note_info(drum_type: str) -> Dict[str, Any]:
    """
    Retrieves music21-specific notation info for a given drum type.
    This is an embedded version of the function from notation_generator/score_builder.py.
    """
    drum_map = DRUM_NOTATION_MAP.get(drum_type)
    if not drum_map:
        print(f"Warning: No notation mapping found for drum type: {drum_type}. Using default kick.")
        drum_map = DRUM_NOTATION_MAP['kick']

    pitch_obj = music21.pitch.Pitch(drum_map['staff_position'])
    
    return {
        'midi_pitch': pitch_obj.midi, 
        'note_head': drum_map['note_head'],
        'staff_position': drum_map['staff_position']
    }

# --- End Embedded Helper Functions ---


def generate_midi_and_xml_from_json(input_json_path: str, midi_output_path: str, xml_output_path: str):
    """
    Reads a JSON file of drum events and generates a MIDI and MusicXML file
    in separate, specified directories using the music21 library.
    """
    if not os.path.exists(input_json_path):
        print(f"Error: Input JSON file not found at '{input_json_path}'.")
        return

    # Create the output directories if they don't exist
    os.makedirs(midi_output_path, exist_ok=True)
    os.makedirs(xml_output_path, exist_ok=True)

    print(f"Reading drum events from: {input_json_path}")
    try:
        with open(input_json_path, 'r') as f:
            drum_events = json.load(f)
        print(f"Successfully loaded {len(drum_events)} drum events.")
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading JSON file: {e}")
        return

    # --- Robust Score Building Logic ---

    score = music21.stream.Score()
    score.metadata = music21.metadata.Metadata()
    score.metadata.title = "Drum Transcription"
    score.metadata.composer = "DrumScript AI"

    drum_part = music21.stream.Part()
    drum_part.partName = 'Drum Kit'
    drum_part.partAbbreviation = 'Dms.'
    
    drum_part.insert(0, music21.clef.PercussionClef())
    drum_part.insert(0, music21.meter.TimeSignature('4/4'))
    drum_part.insert(0, music21.instrument.Percussion())

    tempo_bpm = 65 
    quantization_subdivision = 16
    drum_part.insert(0, music21.tempo.MetronomeMark(number=tempo_bpm))

    quantized_events = defaultdict(list)
    for event in drum_events:
        onset_time_seconds = event['onset_time_seconds']
        
        beats_per_second = tempo_bpm / 60.0
        time_in_beats = onset_time_seconds * beats_per_second
        
        quantized_time_beats = round_to_nearest_subdivision(time_in_beats, quantization_subdivision)
        quantized_events[quantized_time_beats].append(event)

    sorted_quantized_times = sorted(quantized_events.keys())

    last_offset = 0.0
    for current_offset in sorted_quantized_times:
        rest_duration = current_offset - last_offset
        if rest_duration > 0.001:
            rest = music21.note.Rest()
            rest.duration.quarterLength = rest_duration
            drum_part.append(rest)
        
        events_at_this_time = quantized_events[current_offset]
        
        notes_in_cluster = []
        for event_data in events_at_this_time:
            up = music21.note.Unpitched()
            up.storedInstrument = music21.instrument.Percussion()
            up.midi = get_drum_music21_note_info(event_data['drum_type'])['midi_pitch']
            up.notehead = get_drum_music21_note_info(event_data['drum_type'])['note_head']
            notes_in_cluster.append(up)
        
        duration_of_subdivision = 4.0 / quantization_subdivision
        if len(notes_in_cluster) > 1:
            p_chord = music21.percussion.PercussionChord(notes_in_cluster)
            p_chord.duration.quarterLength = duration_of_subdivision
            drum_part.append(p_chord)
        else:
            n = notes_in_cluster[0]
            n.duration.quarterLength = duration_of_subdivision
            drum_part.append(n)
        
        last_offset = current_offset + duration_of_subdivision

    score.insert(0, drum_part)

    # Generate output file paths
    output_filename = os.path.splitext(os.path.basename(input_json_path))[0]
    
    # Write the score to MIDI and MusicXML files in their respective directories
    print("\nGenerating MIDI and MusicXML files...")
    midi_filepath = os.path.join(midi_output_path, f"{output_filename}.mid")
    score.write('midi', fp=midi_filepath)
    
    xml_filepath = os.path.join(xml_output_path, f"{output_filename}.xml")
    score.write('musicxml', fp=xml_filepath)
    
    print(f"Successfully generated MIDI file: {midi_filepath}")
    print(f"Successfully generated MusicXML file: {xml_filepath}")


if __name__ == "__main__":
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_script_dir, os.pardir))

    input_json = os.path.join(current_script_dir, "prediction_output.json")
    midi_output_dir = os.path.join(project_root, "outputs", "drum_classifier", "midi")
    xml_output_dir = os.path.join(project_root, "outputs", "drum_classifier", "xml")

    generate_midi_and_xml_from_json(input_json, midi_output_dir, xml_output_dir)