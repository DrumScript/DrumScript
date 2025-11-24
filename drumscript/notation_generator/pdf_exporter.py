# DrumScript/notation_generator/pdf_exporter.py

import os
from collections import defaultdict
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
except ImportError:
    print("Error: 'reportlab' library not found. Please run 'pip install reportlab'")
    canvas = None

import music21
from drumscript.notation_generator import constants
from datetime import datetime

print("\n# ------------------------------------------------------------------------------------")
datetimestamp = datetime.now()
print(f'\ndate/time: {datetimestamp}')

# --- Configuration Constants ---
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 50
MARGIN_Y = 50
STAFF_SPACING = 120 # Increased spacing for readability
LINE_SPACING = 6    
CLEF_WIDTH = 40     # Increased to 40 to fit Clef + Time Sig
BARS_PER_SYSTEM = 4 # Target: 4 measures per system

# Reference Pitch (Middle Line = B3)
REF_PITCH_MIDDLE_LINE = music21.pitch.Pitch('B3') # NOTE: DO WE NEED THIS FOR DRUMS? PERHAPS NOT IN GENERAL BUT THE ENGINER NEEDS TO UNDERSTAND HOW TO RUN PLACE THINGS

def get_vertical_position(staff_position_str: str, staff_y_base: float) -> float:
    """Calculates the Y-coordinate for a note based on its staff position."""
    if not staff_position_str:
        return staff_y_base + (2 * LINE_SPACING) 
        
    target_pitch = music21.pitch.Pitch(staff_position_str)
    steps_diff = target_pitch.diatonicNoteNum - REF_PITCH_MIDDLE_LINE.diatonicNoteNum
    y_offset = steps_diff * (LINE_SPACING / 2)
    middle_line_y = staff_y_base + (2 * LINE_SPACING)
    return middle_line_y + y_offset

def draw_staff(c, x, y, width):
    """Draws the 5 lines of the percussion staff."""
    c.setLineWidth(1)
    c.setStrokeColor(colors.black)
    for i in range(5):
        line_y = y + (i * LINE_SPACING)
        c.line(x, line_y, x + width, line_y)

def draw_clef(c, x, y):
    """Draws the Percussion Clef (two vertical blocks)."""
    clef_h = 2.5 * LINE_SPACING
    clef_y = y + 1 * LINE_SPACING
    c.rect(x, clef_y, 4, clef_h, fill=1, stroke=0)
    c.rect(x + 8, clef_y, 4, clef_h, fill=1, stroke=0)

def draw_time_signature(c, x, y, numerator, denominator):
    """Draws the time signature numbers centered in the correct staff spaces."""
    # Size 12 fits perfectly in 2 spaces (2 * 6px = 12px)
    c.setFont("Helvetica-Bold", 16) 
    
    # Center alignment calculation relative to the clef gap
    # x passed here is MARGIN_X. The clef takes up ~12px width.
    # We place the numbers roughly 20px in.
    text_x = x + 20
    
    # Top Number: Baseline on Line 3 (y + 12), fills up to Line 5
    c.drawString(text_x, y + (2 * LINE_SPACING), f"{numerator}")
    
    # Bottom Number: Baseline on Line 1 (y), fills up to Line 3
    c.drawString(text_x, y, f"{denominator}")

def draw_bar_line(c, x, y):
    """Draws a vertical bar line."""
    c.setLineWidth(1)
    staff_height = 4 * LINE_SPACING
    c.line(x, y, x, y + staff_height)

def draw_note(c, x, y, note_type, staff_y_base):
    """Draws a notehead and stem with ledger line logic."""
    r = 2.7 # Radius
    
    # Ledger Lines
    top_line_y = staff_y_base + (4 * LINE_SPACING)
    bottom_line_y = staff_y_base
    if y >= top_line_y + LINE_SPACING:
        c.setLineWidth(1)
        c.line(x - 6, y, x + 6, y)
    elif y <= bottom_line_y - LINE_SPACING:
        c.setLineWidth(1)
        c.line(x - 6, y, x + 6, y)

    # Notehead
    if note_type == 'x' or note_type == 'circle-x':
        c.setLineWidth(2)
        c.line(x - r, y - r, x + r, y + r)
        c.line(x - r, y + r, x + r, y - r)
        if note_type == 'circle-x':
            c.setLineWidth(1)
            c.circle(x, y, r + 1.5, stroke=1, fill=0)
    else:
        # Oval Notehead
        c.saveState()
        c.translate(x, y)
        c.scale(1.2, 0.8) 
        c.circle(0, 0, r, fill=1, stroke=0)
        c.restoreState()
        
    # Stem
    c.setLineWidth(1)
    stem_height = 25
    # Attach stem to the side of the notehead
    c.line(x + r, y, x + r, y + stem_height)

# def generate_custom_pdf(detected_events, output_filepath, tempo=120, time_signature="4/4"):
def generate_custom_pdf(detected_events, output_filepath, tempo, time_signature="4/4"):
    # Generates a PDF drum score using ReportLab engine.

    if canvas is None:
        print("ReportLab missing.")
        return
    
    # parse Time Signature (e.g. "3/4" -> numerator=3, denominator=4)
    try:
        numerator, denominator = map(int, time_signature.split('/'))
    except ValueError:
        print(f"Invalid time signature '{time_signature}', defaulting to 4/4")
        numerator, denominator = 4, 4
    
    # def generate_custom_pdf(detected_events, output_filepath, tempo=120, time_signature="4/4"):
    print(f"Generating PDF: {output_filepath} (Sig: {numerator}/{denominator}, {int(tempo)} BPM)")

    c = canvas.Canvas(output_filepath, pagesize=A4)
    c.setTitle("DrumScript Transcription")
    
    # Layout Metrics
    system_width = PAGE_WIDTH - (2 * MARGIN_X)
    music_width = system_width - CLEF_WIDTH

    # For 4/4 we use 4 bars per line. For 3/4, we could fit more, but let's stick to 4 for consistency.
    BARS_PER_SYSTEM = 4 
    measure_width = music_width / BARS_PER_SYSTEM
    
    # --- KEY CALCULATION: Duration of one measure ---
    # In X/4 time, a beat is a quarter note.
    # Seconds per beat = 60 / BPM
    # Seconds per measure = (60 / BPM) * Numerator
    seconds_per_beat = 60.0 / tempo
    if denominator == 8:
        seconds_per_beat = seconds_per_beat / 2.0 # An 8th note gets the beat? Depends on how BPM is defined.
        # Usually BPM is quarter notes. So 6/8 measure = 3 quarter notes duration.
    
    # Calculate duration of one measure in seconds (4/4 time)
    # (60 / BPM) * 4 beats
    sec_per_measure = seconds_per_beat * numerator

    # 1. Sort and Group Events
    detected_events.sort(key=lambda x: x['time'])
    events_by_measure = defaultdict(list)
    
    last_measure_idx = 0
    for event in detected_events:
        m_idx = int(event['time'] / sec_per_measure)
        events_by_measure[m_idx].append(event)
        if m_idx > last_measure_idx:
            last_measure_idx = m_idx

    # 2. Render
    current_y = PAGE_HEIGHT - 150
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(MARGIN_X, PAGE_HEIGHT - 50, "DrumScript Transcription")
    c.setFont("Helvetica", 12)
        # c.drawString(MARGIN_X, PAGE_HEIGHT - 70, f"Tempo: {int(tempo)} BPM")
    c.drawString(MARGIN_X, PAGE_HEIGHT - 70, f"Tempo: {int(tempo)} BPM  |  Time Sig: {numerator}/{denominator}")
    # Clean Header without duplicate time sig
    # c.drawString(MARGIN_X, PAGE_HEIGHT - 70, f"Tempo: {int(tempo)} BPM")
    
    for m in range(last_measure_idx + 1):
        
        # New System Check
        if m % BARS_PER_SYSTEM == 0:
            if m > 0:
                current_y -= STAFF_SPACING
            
            if current_y < MARGIN_Y:
                c.showPage()
                current_y = PAGE_HEIGHT - 100
                c.setFont("Helvetica", 14)
                c.drawString(MARGIN_X, PAGE_HEIGHT - 50, "DrumScript Transcription (Cont.)")
            
            draw_staff(c, MARGIN_X, current_y, system_width)
            draw_clef(c, MARGIN_X + 5, current_y) 

            # Draw Time Signature ONLY on the very first measure (Measure 0)
            # if m == 0:
            draw_time_signature(c, MARGIN_X, current_y, numerator, denominator)
            
        # Measure Placement
        slot_index = m % BARS_PER_SYSTEM
        measure_start_x = MARGIN_X + CLEF_WIDTH + (slot_index * measure_width)
        
        draw_bar_line(c, measure_start_x + measure_width, current_y)
        
        # Draw Notes
        if m in events_by_measure:
            for event in events_by_measure[m]:
                time_sec = event['time']
                drum_types = event['drums']
                
                rel_time = time_sec % sec_per_measure
                padding = 15 
                usable_width = measure_width - (2 * padding)
                rel_x = (rel_time / sec_per_measure) * usable_width
                
                note_x = measure_start_x + padding + rel_x
                
                for drum_type in drum_types:
                    d_map = constants.DRUM_NOTATION_MAP.get(drum_type, constants.DRUM_NOTATION_MAP['kick'])
                    staff_pos = d_map.get('staff_position', 'F3')
                    note_head = d_map.get('note_head', 'normal')
                    
                    note_y = get_vertical_position(staff_pos, current_y)
                    draw_note(c, note_x, note_y, note_head, current_y)

    c.save()
    print(f"PDF successfully saved to: {output_filepath}")
    print("\n# ------------------------------------------------------------------------------------")