# Filename: notation_generator/drum_notation_tester.py
# Purpose: Test script to generate a clean drum score, removing accidentals and beams.

import json
import subprocess
import music21
from music21 import stream, note, chord, meter, clef, instrument, beam
import constants # Import the constants from the same module

def generate_drum_score(events, tempo=120, output_filename="drum_test_score"):
    """
    Generates a clean drum score PDF and MusicXML file from a list of timed events.
    """
    score = stream.Score()
    drum_part = stream.Part()
    drum_part.insert(0, instrument.Percussion())
    drum_part.insert(0, clef.PercussionClef())
    drum_part.insert(0, meter.TimeSignature('4/4'))

    TOLERANCE = 0.02
    grouped_events = []
    if not events:
        print("No events to process.")
        return
    events.sort(key=lambda x: x['onset_time_seconds'])
    current_group = [events[0]]
    for i in range(1, len(events)):
        if events[i]['onset_time_seconds'] - current_group[-1]['onset_time_seconds'] <= TOLERANCE:
            current_group.append(events[i])
        else:
            grouped_events.append(current_group)
            current_group = [events[i]]
    grouped_events.append(current_group)

    for i, group in enumerate(grouped_events):
        onset_time_sec = group[0]['onset_time_seconds']
        offset = onset_time_sec * (tempo / 60.0)

        if i < len(grouped_events) - 1:
            next_onset_time_sec = grouped_events[i+1][0]['onset_time_seconds']
            duration_sec = next_onset_time_sec - onset_time_sec
            duration_qn = duration_sec * (tempo / 60.0)
        else:
            duration_qn = 0.5

        # --- MODIFIED SECTION ---
        # Look up the MIDI pitch for each drum type from constants map
        midi_pitches = [constants.DRUM_NOTATION_MAP[event['drum_type']]['midi_pitch'] for event in group]

        if len(midi_pitches) == 1:
            n = note.Note(midi_pitches[0])
        else:
            n = chord.Chord(midi_pitches)


        #if len(group) == 1:
         #   n = note.Note(group[0]['midi_pitch'])
        #else:
         #   midi_pitches = [event['midi_pitch'] for event in group]
          #  n = chord.Chord(midi_pitches)
        # --- END MODIFIED SECTION ---
        

  
        if n.isChord:       #  Hide accidentals without changing the note's pitch
            for p in n.pitches:
                if p.accidental: # Check if an accidental exists
                    p.accidental.displayStatus = False

        else:
            if n.pitch.accidental: # Check if an accidental exists
                n.pitch.accidental.displayStatus = False

        n.beams = beam.Beams() #  Remove beams (the "tails" connecting notes)


        n.duration.quarterLength = duration_qn
        drum_part.insert(offset, n)

    score.append(drum_part)
    score.makeMeasures(inPlace=True)
    print("Score created successfully. Generating output files...")

    #xml_path = f"{output_filename}.musicxml"
    xml_path = f"{output_filename}.xml" # Note: Changed to .xml for clarity
    score.write('musicxml', fp=xml_path)
    print(f"MusicXML file saved to: {xml_path}")

    musescore_path = '/Applications/MuseScore 4.app/Contents/MacOS/mscore'
    pdf_path = f"{output_filename}.pdf"
    try:
        print("🎵 Attempting to generate PDF using MuseScore...")
        command = [musescore_path, '-o', pdf_path, xml_path]
        subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"PDF file successfully generated at: {pdf_path}")
    except FileNotFoundError:
        print(f"ERROR: MuseScore executable not found at '{musescore_path}'. Please check the path.")
    except subprocess.CalledProcessError as e:
        print(f"ERROR: MuseScore failed to convert the file.")
        print(f"   Error Output: {e.stderr}")

if __name__ == '__main__':
    # --- UPDATED MOCK DATA using human-readable drum types ---
    mock_drum_hits = [
        {'onset_time_seconds': 0.0, 'drum_type': 'kick'},
        {'onset_time_seconds': 0.0, 'drum_type': 'crash_cymbal'},
        {'onset_time_seconds': 0.5, 'drum_type': 'hi-hat_closed'},
        {'onset_time_seconds': 1.0, 'drum_type': 'snare'},
        {'onset_time_seconds': 1.0, 'drum_type': 'hi-hat_closed'},
        {'onset_time_seconds': 1.5, 'drum_type': 'hi-hat_closed'},
        {'onset_time_seconds': 2.0, 'drum_type': 'kick'},
        {'onset_time_seconds': 2.0, 'drum_type': 'hi-hat_closed'},
        {'onset_time_seconds': 2.5, 'drum_type': 'hi-hat_closed'},
        {'onset_time_seconds': 3.0, 'drum_type': 'snare'},
        {'onset_time_seconds': 3.0, 'drum_type': 'hi-hat_closed'},
        {'onset_time_seconds': 3.5, 'drum_type': 'hi-hat_closed'},
    ]
    generate_drum_score(mock_drum_hits, tempo=120)