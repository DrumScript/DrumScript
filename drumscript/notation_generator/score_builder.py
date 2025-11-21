# DrumScript/notation_generator/score_builder.py

import music21
import os
from typing import List, Dict, Any
from collections import defaultdict
from drumscript.notation_generator import constants
from drumscript.notation_generator.helpers import round_to_nearest_subdivision

# --- IMPORTANT: Import new native PDF Engine ---
from drumscript.notation_generator.pdf_exporter import generate_custom_pdf 

def get_drum_music21_note_info(drum_type: str) -> Dict[str, Any]:
    """Retrieves notation info for XML export backup."""
    drum_map = constants.DRUM_NOTATION_MAP.get(drum_type)
    if not drum_map:
        drum_map = constants.DRUM_NOTATION_MAP['kick'] 
    
    pitch_obj = music21.pitch.Pitch(drum_map['staff_position'])
    
    return {
        'midi_pitch': drum_map['midi_program'], 
        'note_head': drum_map['note_head'],
        'display_step': pitch_obj.step,     
        'display_octave': pitch_obj.octave  
    }

def build_and_export_drum_score(
    detected_events: List[Dict[str, Any]],
    tempo: int = 120,
    output_filepath: str = "outputs/score.pdf", 
    quantization_subdivision: int = 16 
):
    """
    1. Exports MusicXML & MIDI (Data Backup).
    2. Generates Visual PDF using the Custom ReportLab Engine.
    """
    print(f"--- Building Score for: {output_filepath} ---")

    # ===========================================================
    # PART A: DATA BACKUP (MusicXML & MIDI via Music21)
    # ===========================================================
    # We keep this so you have an editable file if needed,
    # but we DO NOT use it for the PDF generation anymore.
    score = music21.stream.Score()
    score.metadata = music21.metadata.Metadata(title="Drum Transcription")
    drum_part = music21.stream.Part()
    drum_part.id = 'DrumKit'
    drum_part.insert(0, music21.clef.PercussionClef())
    drum_part.insert(0, music21.meter.TimeSignature('4/4')) 
    drum_part.insert(0, music21.instrument.Percussion())
    drum_part.insert(0, music21.tempo.MetronomeMark(number=tempo))

    # Simple Quantization for the XML backup
    events_by_time = defaultdict(list)
    for event in detected_events:
        t_beats = (event['time'] / 60.0) * tempo
        q_time = round_to_nearest_subdivision(t_beats, quantization_subdivision)
        events_by_time[q_time].extend(event['drums'])

    last_offset = 0.0
    for q_time in sorted(events_by_time.keys()):
        if q_time > last_offset:
            r = music21.note.Rest()
            r.duration.quarterLength = q_time - last_offset
            drum_part.append(r)
        
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

    # Export Data Files
    base_path = os.path.splitext(output_filepath)[0]
    try:
        score.write('musicxml', fp=f"{base_path}.musicxml")
        score.write('midi', fp=f"{base_path}.mid")
        print(f" Data backup saved: {base_path}.musicxml")
    except Exception as e:
        print(f" Data export warning: {e}")

    # ===========================================================
    # PART B: VISUAL PDF (The "Real" Score via ReportLab)
    # ===========================================================
    
    # We bypass MusicXML entirely and send the raw events to our custom engine.
    try:
        generate_custom_pdf(
            detected_events=detected_events,
            output_filepath=output_filepath,
            tempo=tempo
        )
    except Exception as e:
        print(f"Native PDF Export Failed: {e}")
        import traceback
        traceback.print_exc()