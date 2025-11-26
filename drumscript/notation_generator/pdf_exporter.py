# DrumScript/notation_generator/pdf_exporter.py

import os
from collections import defaultdict
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
import music21
from drumscript.notation_generator import constants
# from datetime import datetime

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')

# --- Constants ---
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN_X, MARGIN_Y = 50, 50
STAFF_SPACING, LINE_SPACING = 120, 6
CLEF_WIDTH = 40     
BARS_PER_SYSTEM = 4 
REF_PITCH_MIDDLE_LINE = music21.pitch.Pitch('B3')

def get_vertical_position(staff_position_str: str, staff_y_base: float) -> float:
    if not staff_position_str: return staff_y_base + (2 * LINE_SPACING)
    target = music21.pitch.Pitch(staff_position_str)
    diff = target.diatonicNoteNum - REF_PITCH_MIDDLE_LINE.diatonicNoteNum
    return staff_y_base + (2 * LINE_SPACING) + (diff * (LINE_SPACING / 2))

def draw_staff(c, x, y, width):
    c.setLineWidth(1); c.setStrokeColor(colors.black)
    for i in range(5):
        ly = y + (i * LINE_SPACING)
        c.line(x, ly, x + width, ly)

def draw_clef(c, x, y):
    h, y_pos = 2.5 * LINE_SPACING, y + LINE_SPACING
    c.rect(x, y_pos, 4, h, fill=1, stroke=0)
    c.rect(x + 8, y_pos, 4, h, fill=1, stroke=0)

def draw_time_signature(c, x, y, num, den):
    c.setFont("Helvetica-Bold", 16)
    c.drawString(x + 20, y + (2 * LINE_SPACING) + 1, f"{num}")
    c.drawString(x + 20, y + 1, f"{den}")

def draw_bar_line(c, x, y):
    c.setLineWidth(1)
    c.line(x, y, x, y + (4 * LINE_SPACING))

def draw_note(c, x, y, note_type, base_y):
    r = 2.7
    if y >= base_y + (5 * LINE_SPACING): c.line(x-6, y, x+6, y)
    elif y <= base_y - LINE_SPACING: c.line(x-6, y, x+6, y)

    if note_type in ['x', 'circle-x']:
        c.setLineWidth(2)
        c.line(x-r, y-r, x+r, y+r); c.line(x-r, y+r, x+r, y-r)
        if note_type == 'circle-x': 
            c.setLineWidth(1); c.circle(x, y, r+1.5, stroke=1, fill=0)
    else:
        c.saveState(); c.translate(x, y); c.scale(1.2, 0.8)
        c.circle(0, 0, r, fill=1, stroke=0); c.restoreState()
    
    c.setLineWidth(1)
    c.line(x+r, y, x+r, y+25)

def generate_custom_pdf(detected_events, output_filepath, tempo, time_signature="4/4"):
    if canvas is None: return
    
    try: num, den = map(int, time_signature.split('/'))
    except: num, den = 4, 4

    c = canvas.Canvas(output_filepath, pagesize=A4)
    c.setTitle("DrumScript Transcription")
    
    # Layout
    sys_w = PAGE_WIDTH - (2 * MARGIN_X)
    meas_w = (sys_w - CLEF_WIDTH) / BARS_PER_SYSTEM
    
    # Timing
    beat_dur = 60.0 / tempo
    if den == 8: beat_dur /= 2.0
    meas_dur = beat_dur * num

    # Grouping
    detected_events.sort(key=lambda x: x['time'])
    measures = defaultdict(list)
    max_m = 0
    for e in detected_events:
        m = int(e['time'] / meas_dur)
        measures[m].append(e)
        max_m = max(max_m, m)

    curr_y = PAGE_HEIGHT - 150
    
    c.setFont("Helvetica-Bold", 24)
    c.drawString(MARGIN_X, PAGE_HEIGHT - 50, "DrumScript Transcription")
    c.setFont("Helvetica", 12)
    c.drawString(MARGIN_X, PAGE_HEIGHT - 70, f"Tempo: {int(tempo)} BPM")

    for m in range(max_m + 1):
        # System Break
        if m % BARS_PER_SYSTEM == 0:
            if m > 0: curr_y -= STAFF_SPACING
            if curr_y < MARGIN_Y:
                c.showPage(); curr_y = PAGE_HEIGHT - 100
                c.setFont("Helvetica", 10)
                c.drawString(MARGIN_X, PAGE_HEIGHT-50, "DrumScript Transcription (Cont.)")
            
            draw_staff(c, MARGIN_X, curr_y, sys_w)
            draw_clef(c, MARGIN_X + 5, curr_y)
            draw_time_signature(c, MARGIN_X, curr_y, num, den)

        slot = m % BARS_PER_SYSTEM
        mx = MARGIN_X + CLEF_WIDTH + (slot * meas_w)
        draw_bar_line(c, mx + meas_w, curr_y)

        if m in measures:
            for e in measures[m]:
                rel_t = e['time'] % meas_dur
                px = mx + 15 + ((rel_t / meas_dur) * (meas_w - 30))
                
                for d_name in e['drums']:
                    info = constants.DRUM_NOTATION_MAP.get(d_name, constants.DRUM_NOTATION_MAP['kick'])
                    ny = get_vertical_position(info['staff_position'], curr_y)
                    draw_note(c, px, ny, info['note_head'], curr_y)

    c.save()
    print(f"   -> PDF saved: {output_filepath}")
    
    # print("\n# ------------------------------------------------------------------------------------")