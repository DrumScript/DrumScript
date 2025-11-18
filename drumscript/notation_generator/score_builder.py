# DrumScript/notation_generator/score_builder.py

import music21
import os
from typing import List, Dict, Any
from collections import defaultdict
from drumscript.notation_generator import constants
from drumscript.notation_generator.helpers import round_to_nearest_subdivision

# --- FIX: Import the correct function name from your new pdf_exporter ---
from drumscript.notation_generator.pdf_exporter import generate_custom_pdf 

def get_drum_music21_note_info(drum_type: str) -> Dict[str, Any]:
    """
    Retrieves music21-specific notation info for a given drum type from constants.DRUM_NOTATION_MAP.
    """
    drum_map = constants.DRUM_NOTATION_MAP.get(drum_type)
    if not drum_map:
        print(f"Warning: No notation mapping found for drum type: {drum_type}. Using default kick.")
        drum_map = constants.DRUM_NOTATION_MAP['kick'] # Fallback
    
    # Parse the staff position string (e.g., 'F2', 'C3') into a music21 Pitch object
    # to easily extract the step ('F') and octave (2).
    pitch_obj = music21.pitch.Pitch(drum_map['staff_position'])
    
    return {
        'midi_pitch': drum_map['midi_program'], 
        'note_head': drum_map['note_head'],
        'staff_position': drum_map['staff_position'],
        'display_step': pitch_obj.step,     # E.g., 'F'
        'display_octave': pitch_obj.octave  # E.g., 2
    }


def build_and_export_drum_score(
    detected_events: List[Dict[str, Any]],
    tempo: int = 120,
    output_filepath: str = "outputs/score.pdf", # Default to .pdf
    quantization_subdivision: int = 16 
):
    """
    Builds a music21 score for XML/MIDI export (Data Layer).
    Calls custom ReportLab exporter for PDF (Presentation Layer).
    """
    print(f"--- Building Score for: {output_filepath} ---")

    # ===========================================================
    # PART A: DATA EXPORT (MusicXML & MIDI) - Using music21
    # ===========================================================
    score = music21.stream.Score()
    score.metadata = music21.metadata.Metadata(title="Drum Transcription")
    drum_part = music21.stream.Part()
    drum_part.id = 'DrumKit'
    
    # Using insert(0, ...) ensures these are at the very start
    drum_part.insert(0, music21.clef.PercussionClef())
    drum_part.insert(0, music21.meter.TimeSignature('4/4')) 
    drum_part.insert(0, music21.instrument.Percussion())
    drum_part.insert(0, music21.tempo.MetronomeMark(number=tempo))

    # Quantize events for XML/MIDI structure
    events_by_time = defaultdict(list)
    for event in detected_events:
        # Convert seconds -> beats
        t_beats = (event['time'] / 60.0) * tempo
        q_time = round_to_nearest_subdivision(t_beats, quantization_subdivision)
        events_by_time[q_time].extend(event['drums'])

    last_offset = 0.0
    for q_time in sorted(events_by_time.keys()):
        # Rests
        if q_time > last_offset:
            r = music21.note.Rest()
            r.duration.quarterLength = q_time - last_offset
            drum_part.append(r)
        
        # Notes
        drums = events_by_time[q_time]
        notes = []
        for d in drums:
            info = get_drum_music21_note_info(d)
            n = music21.note.Unpitched()
            n.storedInstrument = music21.instrument.Percussion()
            n.displayStep = info['display_step']
            n.displayOctave = info['display_octave']
            n.notehead = info['note_head']
            notes.append(n)
        
        dur = 4.0 / quantization_subdivision
        if len(notes) == 1:
            notes[0].duration.quarterLength = dur
            drum_part.append(notes[0])
        else:
            chord = music21.percussion.PercussionChord(notes)
            chord.duration.quarterLength = dur
            drum_part.append(chord)
            
        last_offset = q_time + dur
        
    score.append(drum_part)

    # Export Data Files (XML and MIDI)
    base_path = os.path.splitext(output_filepath)[0]
    try:
        score.write('musicxml', fp=f"{base_path}.musicxml")
        score.write('midi', fp=f"{base_path}.mid")
        print(f"✅ Data files saved: {base_path}.musicxml / .mid")
    except Exception as e:
        print(f"⚠️  Data export warning: {e}")

    # ===========================================================
    # PART B: VISUAL EXPORT (PDF) - Using Native Exporter
    # ===========================================================
    
    # Pass the raw 'detected_events' directly to our custom renderer.
    try:
        generate_custom_pdf(
            detected_events=detected_events,
            output_filepath=output_filepath,
            tempo=tempo
        )
    except Exception as e:
        print(f"❌ Native PDF Export Failed: {e}")
        import traceback
        traceback.print_exc()