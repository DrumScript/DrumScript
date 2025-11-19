# DrumScript/notation_generator/pdf_exporter.py

import os
from collections import defaultdict
import math

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
except ImportError:
    print("Error: 'reportlab' library not found. Please run 'pip install reportlab'")
    canvas = None

import music21
from drumscript.notation_generator import constants

# --- Configuration Constants ---
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X = 50
MARGIN_Y = 50
STAFF_SPACING = 120 # Increased spacing for readability
LINE_SPACING = 6    
CLEF_WIDTH = 30     # Reserved space at start of each system for the clef
BARS_PER_SYSTEM = 4 # Target: 4 bars per line

# Reference Pitch (Middle Line = B3)
REF_PITCH_MIDDLE_LINE = music21.pitch.Pitch('B3')

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

def draw_bar_line(c, x, y):
    """Draws a vertical bar line."""
    c.setLineWidth(1)
    staff_height = 4 * LINE_SPACING
    c.line(x, y, x, y + staff_height)

def draw_note(c, x, y, note_type, staff_y_base):
    """Draws a notehead and stem with ledger line logic."""
    r = 3.5 
    
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
            c.circle(x, y, r + 3, stroke=1, fill=0)
    else:
        c.saveState()
        c.translate(x, y)
        c.scale(1.2, 0.8) 
        c.circle(0, 0, r, fill=1, stroke=0)
        c.restoreState()
        
    # Stem
    c.setLineWidth(1)
    stem_height = 25
    c.line(x + r, y, x + r, y + stem_height)


def generate_custom_pdf(detected_events, output_filepath, tempo=120):
    """
    Generates a PDF drum score with 4 bars per system.
    """
    if canvas is None:
        print("❌ ReportLab missing.")
        return

    print(f"Generating 4-Bar Layout PDF: {output_filepath}")
    c = canvas.Canvas(output_filepath, pagesize=A4)
    c.setTitle("DrumScript Transcription")
    
    # --- Setup Layout Metrics ---
    system_width = PAGE_WIDTH - (2 * MARGIN_X)
    # Calculate width available for actual music (minus clef)
    music_width = system_width - CLEF_WIDTH
    # Divide exactly by 4 for the measure width
    measure_width = music_width / BARS_PER_SYSTEM
    
    # Duration of one measure in seconds (assuming 4/4 time)
    # 60 sec/min / BPM * 4 beats = sec/measure
    sec_per_measure = (60.0 / tempo) * 4.0

    # --- 1. Sort and Group Events by Measure ---
    detected_events.sort(key=lambda x: x['time'])
    events_by_measure = defaultdict(list)
    
    last_measure_idx = 0
    for event in detected_events:
        m_idx = int(event['time'] / sec_per_measure)
        events_by_measure[m_idx].append(event)
        if m_idx > last_measure_idx:
            last_measure_idx = m_idx

    # --- 2. Rendering Loop ---
    current_y = PAGE_HEIGHT - 150
    
    # Header
    c.setFont("Helvetica-Bold", 24)
    c.drawString(MARGIN_X, PAGE_HEIGHT - 50, "DrumScript Transcription")
    c.setFont("Helvetica", 12)
    c.drawString(MARGIN_X, PAGE_HEIGHT - 70, f"Tempo: {int(tempo)} BPM")
    
    # Iterate through all measures (0 to last_measure_idx)
    for m in range(last_measure_idx + 1):
        
        # Check if we need a new system (start of line)
        if m % BARS_PER_SYSTEM == 0:
            # If not the very first system, move cursor down
            if m > 0:
                current_y -= STAFF_SPACING
            
            # Check Page Wrap
            if current_y < MARGIN_Y:
                c.showPage()
                current_y = PAGE_HEIGHT - 100
                # Re-draw header on new page? Optional.
                c.setFont("Helvetica", 10)
                c.drawString(MARGIN_X, PAGE_HEIGHT - 50, "DrumScript Transcription (Cont.)")
            
            # Draw System Basics (Staff + Clef)
            draw_staff(c, MARGIN_X, current_y, system_width)
            draw_clef(c, MARGIN_X + 5, current_y) # +5 padding
            
        # Calculate placement for this specific measure
        # Which slot (0, 1, 2, 3) are we in on the current system?
        slot_index = m % BARS_PER_SYSTEM
        
        # Start X for this measure
        measure_start_x = MARGIN_X + CLEF_WIDTH + (slot_index * measure_width)
        
        # Draw Bar Line at the END of this measure
        draw_bar_line(c, measure_start_x + measure_width, current_y)
        
        # Draw Notes in this Measure
        if m in events_by_measure:
            for event in events_by_measure[m]:
                time_sec = event['time']
                drum_types = event['drums']
                
                # Relative time inside the measure (0.0 to sec_per_measure)
                rel_time = time_sec % sec_per_measure
                
                # Proportional X position
                # We add a small padding (10px) so notes don't hit the left bar line
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
    print(f"Native PDF successfully saved to: {output_filepath}")