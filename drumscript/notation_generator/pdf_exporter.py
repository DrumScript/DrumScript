# DrumScript/notation_generator/pdf_exporter.py

"""
Module for rendering the drum score to PDF using ReportLab.
"""

from collections import defaultdict

from drumscript.notation_generator import constants

# --- Configuration Constants ---
try:
    from reportlab.lib.pagesizes import A4

    PAGE_WIDTH, PAGE_HEIGHT = A4
except (ImportError, ValueError):
    # Fallback for Sphinx autodoc mock imports
    PAGE_WIDTH, PAGE_HEIGHT = 595.27, 841.89

try:
    import music21
    from reportlab.lib import colors
    from reportlab.pdfgen import canvas
except ImportError:
    music21 = None
    colors = None
    canvas = None

MARGIN_X = 50
MARGIN_Y = 50
# STAFF_SPACING = 120
STAFF_SPACING = 90  # Tweak 1: Brought bars closer together vertically
LINE_SPACING = 6
CLEF_WIDTH = 40
BARS_PER_SYSTEM = 4

try:
    REF_PITCH_MIDDLE_LINE = music21.pitch.Pitch("B3")
except (AttributeError, TypeError):
    REF_PITCH_MIDDLE_LINE = None


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
    # c.setLineWidth(1)
    c.setLineWidth(0.5)  # Tweak 5: Thinner staff lines for a cleaner look
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
    c.setFont("Helvetica-Bold", 16)
    text_x = x + 20
    c.drawString(text_x, y + (2 * LINE_SPACING), f"{numerator}")
    c.drawString(text_x, y, f"{denominator}")


def draw_bar_line(c, x, y):
    """Draws a vertical bar line."""
    # c.setLineWidth(1)
    c.setLineWidth(0.75)  # Tweak 5: Cleaner bar lines
    staff_height = 4 * LINE_SPACING
    c.line(x, y, x, y + staff_height)


def draw_notehead(c, x, y, note_type, staff_y_base, accent=False):
    """Draws ONLY the notehead and ledger lines (stems are handled by beaming)."""
    r = 3.5
    top_line_y = staff_y_base + (4 * LINE_SPACING)
    bottom_line_y = staff_y_base

    # Ledger lines
    if y >= top_line_y + LINE_SPACING:
        # c.setLineWidth(1)
        c.setLineWidth(0.75)  # Tweak 5: Cleaner ledger lines
        c.line(x - 8, y, x + 8, y)
    elif y <= bottom_line_y - LINE_SPACING:
        # c.setLineWidth(1)
        c.setLineWidth(0.75)
        c.line(x - 8, y, x + 8, y)

    if note_type == "x" or note_type == "circle-x":
        # c.setLineWidth(2)
        c.setLineWidth(1.5)  # Tweak 5: Cleaner hi-hat cross lines
        c.line(x - r, y - r, x + r, y + r)
        c.line(x - r, y + r, x + r, y - r)
        if note_type == "circle-x":
            # c.setLineWidth(1)
            c.setLineWidth(0.75)
            c.circle(x, y, r + 1.5, stroke=1, fill=0)
    else:
        c.saveState()
        c.translate(x, y)
        c.scale(1.2, 0.8)
        c.circle(0, 0, r, fill=1, stroke=0)
        c.restoreState()

    # Tweak 4: Future-proofing for Accents! Draws a ">" symbol above the notehead.
    if accent:
        c.setLineWidth(1)
        c.line(x - 4, y + 12, x + 4, y + 9)
        c.line(x - 4, y + 6, x + 4, y + 9)


# def generate_custom_pdf(detected_events, output_filepath, tempo, time_signature="4/4"):
def export_pdf(detected_events, output_filepath, tempo, time_signature="4/4"):
    """
    Generates a PDF drum score using ReportLab engine.
    """
    if canvas is None:
        print("ReportLab missing.")
        return

    try:
        numerator, denominator = map(int, time_signature.split("/"))
    except ValueError:
        numerator, denominator = 4, 4

    print(f"Generating PDF: {output_filepath} (Sig: {numerator}/{denominator}, {int(tempo)} BPM)")

    c = canvas.Canvas(output_filepath, pagesize=A4)
    c.setTitle("DrumScript Transcription")

    system_width = PAGE_WIDTH - (2 * MARGIN_X)
    music_width = system_width - CLEF_WIDTH
    BARS_PER_SYSTEM = 4
    measure_width = music_width / BARS_PER_SYSTEM

    seconds_per_beat = 60.0 / tempo
    if denominator == 8:
        seconds_per_beat = seconds_per_beat / 2.0

    sec_per_measure = seconds_per_beat * numerator

    # detected_events.sort(key=lambda x: x['time'])
    # ADAPTED KEY: Using 'time_sec'
    detected_events.sort(key=lambda x: x["time_sec"])
    events_by_measure = defaultdict(list)

    last_measure_idx = 0
    for event in detected_events:
        # LEGACY CODE - m_idx = int(event['time'] / sec_per_measure)
        # ADAPTED KEY: Using 'time_sec'
        m_idx = int(event["time_sec"] / sec_per_measure)
        events_by_measure[m_idx].append(event)
        if m_idx > last_measure_idx:
            last_measure_idx = m_idx

    current_y = PAGE_HEIGHT - 150

    c.setFont("Helvetica-Bold", 24)
    c.drawString(MARGIN_X, PAGE_HEIGHT - 50, "DrumScript Transcription")
    c.setFont("Helvetica", 12)
    c.drawString(MARGIN_X, PAGE_HEIGHT - 70, f"Tempo: {int(tempo)} BPM")

    for m in range(last_measure_idx + 1):
        if m % BARS_PER_SYSTEM == 0:
            if m > 0:
                current_y -= STAFF_SPACING
            if current_y < MARGIN_Y:
                c.showPage()
                current_y = PAGE_HEIGHT - 100
                c.setFont("Helvetica", 10)
                c.drawString(MARGIN_X, PAGE_HEIGHT - 50, "DrumScript Transcription (Cont.)")

            draw_staff(c, MARGIN_X, current_y, system_width)
            draw_clef(c, MARGIN_X + 5, current_y)
            draw_time_signature(c, MARGIN_X, current_y, numerator, denominator)

        slot_index = m % BARS_PER_SYSTEM
        measure_start_x = MARGIN_X + CLEF_WIDTH + (slot_index * measure_width)

        draw_bar_line(c, measure_start_x + measure_width, current_y)

        # --- LEGACY CODE - DRAW MEASURE NUMBERS (Italics and Offset) ---
        # c.setFont("Helvetica-Oblique", 9)
        # c.drawString(measure_start_x + 5, current_y + (6 * LINE_SPACING), str(m + 1))

        # --- DRAW MEASURE NUMBERS (Tweak 1: Flush left, Roboto-style Helvetica) ---
        c.setFont("Helvetica", 9)
        c.drawString(measure_start_x, current_y + (6 * LINE_SPACING), str(m + 1))

        # --- DUAL-VOICE BEAMING RENDERING LOOP ---
        if m in events_by_measure:
            # 1. Group all events in this measure by Beat (Quarter Note)
            beats = defaultdict(list)
            for event in events_by_measure[m]:
                # LEGACY CODE - rel_time = event['time'] % sec_per_measure
                # ADAPTED KEY: Using 'time_sec'
                rel_time = event["time_sec"] % sec_per_measure
                beat_idx = int(rel_time / seconds_per_beat)
                beats[beat_idx].append(event)

            # 2. Render each beat group by separating into Voices
            for beat_idx, event_list in beats.items():
                voice_up_notes = []  # Idiophones (Cymbals, Hats) -> Stems up
                voice_down_notes = []  # Membranophones (Kicks, Snares, Toms) -> Stems down

                x_coords_up = set()
                x_coords_down = set()

                for event in event_list:
                    # LEGACY CODE - rel_time = event['time'] % sec_per_measure
                    # ADAPTED KEY: Using 'time_sec'
                    rel_time = event["time_sec"] % sec_per_measure
                    padding = 15
                    usable_width = measure_width - (2 * padding)
                    rel_x = (rel_time / sec_per_measure) * usable_width
                    note_x = measure_start_x + padding + rel_x

                    # Tweak 4: Grab accent status (defaults to False if not yet implemented in classifier)
                    is_accent = event.get("accent", False)

                    # Split instruments into voices based on physical type
                    # LEGACY CODE - for drum_type in event['drums']:
                    # ADAPTED KEY: Using 'instruments'
                    for drum_type in event["instruments"]:
                        d_map = constants.DRUM_NOTATION_MAP.get(drum_type, constants.DRUM_NOTATION_MAP["kick"])
                        staff_pos = d_map.get("staff_position", "F3")
                        note_head = d_map.get("note_head", "normal")
                        note_y = get_vertical_position(staff_pos, current_y)

                        # Tweak 4: Expanded Idiophone routing list for future-proofing
                        idiophones = ["hi_hat_closed", "hi_hat_open", "ride", "crash", "splash", "china", "bell"]

                        # Idiophones get upward stems, Membranophones get downward stems
                        if drum_type in idiophones:
                            voice_up_notes.append((note_x, note_y, note_head, is_accent))
                            x_coords_up.add(note_x)
                        else:
                            voice_down_notes.append((note_x, note_y, note_head, is_accent))
                            x_coords_down.add(note_x)

                # stem_length = 25
                stem_length = 18  # Tweak 2: Made the note tail length a bit shorter!
                stem_offset = 3.2

                # --- DRAW VOICE 1: STEMS UP (Cymbals) ---
                if voice_up_notes:
                    highest_y = max([ny for nx, ny, nh, acc in voice_up_notes])
                    lowest_y_at_x = {}

                    for nx, ny, nhead, acc in voice_up_notes:
                        draw_notehead(c, nx, ny, nhead, current_y, accent=acc)
                        if nx not in lowest_y_at_x or ny < lowest_y_at_x[nx]:
                            lowest_y_at_x[nx] = ny

                    beam_y = highest_y + stem_length
                    unique_x = sorted(list(x_coords_up))

                    # c.setLineWidth(1)
                    c.setLineWidth(0.75)  # Tweak 5: Cleaner stems
                    c.setStrokeColor(colors.black)
                    for nx in unique_x:
                        bot_y = lowest_y_at_x[nx]
                        c.line(nx + stem_offset, bot_y, nx + stem_offset, beam_y)  # Stem on right side

                    if len(unique_x) > 1:
                        first_x, last_x = unique_x[0], unique_x[-1]
                        # c.setLineWidth(3)
                        c.setLineWidth(2.5)  # Tweak 5: Slightly cleaner primary beam
                        c.line(first_x + stem_offset, beam_y, last_x + stem_offset, beam_y)
                        if len(unique_x) > 2:  # Draw secondary 16th beam
                            c.setLineWidth(1.5)
                            c.line(first_x + stem_offset, beam_y - 4, last_x + stem_offset, beam_y - 4)
                    # Tweak 3: Commented out the single-note flag flick!
                    # else:
                    #     nx = unique_x[0]
                    #     c.setLineWidth(1)
                    #     c.line(nx + stem_offset, beam_y, nx + 8, beam_y - 8) # Upward flag hook

                # --- DRAW VOICE 2: STEMS DOWN (Drums) ---
                if voice_down_notes:
                    lowest_y = min([ny for nx, ny, nh, acc in voice_down_notes])
                    highest_y_at_x = {}

                    for nx, ny, nhead, acc in voice_down_notes:
                        draw_notehead(c, nx, ny, nhead, current_y, accent=acc)
                        if nx not in highest_y_at_x or ny > highest_y_at_x[nx]:
                            highest_y_at_x[nx] = ny

                    beam_y = lowest_y - stem_length
                    unique_x = sorted(list(x_coords_down))

                    # c.setLineWidth(1)
                    c.setLineWidth(0.75)  # Tweak 5: Cleaner stems
                    c.setStrokeColor(colors.black)
                    for nx in unique_x:
                        top_y = highest_y_at_x[nx]
                        c.line(nx - stem_offset, top_y, nx - stem_offset, beam_y)  # Stem on left side

                    if len(unique_x) > 1:
                        first_x, last_x = unique_x[0], unique_x[-1]
                        # c.setLineWidth(3)
                        c.setLineWidth(2.5)  # Tweak 5: Slightly cleaner primary beam
                        c.line(first_x - stem_offset, beam_y, last_x - stem_offset, beam_y)
                        if len(unique_x) > 2:  # Draw secondary 16th beam
                            c.setLineWidth(1.5)
                            c.line(first_x - stem_offset, beam_y + 4, last_x - stem_offset, beam_y + 4)
                    # Tweak 3: Commented out the single-note flag flick!
                    # else:
                    #     nx = unique_x[0]
                    #     c.setLineWidth(1)
                    #     c.line(nx - stem_offset, beam_y, nx + 2, beam_y + 6) # Downward flag hook

    c.save()
    # print("\n# ------------------------------------------------------------------------------------")
    print(f"PDF successfully saved to: {output_filepath}")


""" LEGACY (KEEP FOR ALPHA)


# --- COMMENTED OUT LEGACY DRAW_NOTE (Individual Upward Stems) ---
# def draw_note(c, x, y, note_type, staff_y_base):
     #Draws a notehead and stem with ledger line logic.#
#     r = 2.7
#     top_line_y = staff_y_base + (4 * LINE_SPACING)
#     bottom_line_y = staff_y_base
#     if y >= top_line_y + LINE_SPACING:
#         c.setLineWidth(1)
#         c.line(x - 6, y, x + 6, y)
#     elif y <= bottom_line_y - LINE_SPACING:
#         c.setLineWidth(1)
#         c.line(x - 6, y, x + 6, y)
#
#     if note_type == 'x' or note_type == 'circle-x':
#         c.setLineWidth(2)
#         c.line(x - r, y - r, x + r, y + r)
#         c.line(x - r, y + r, x + r, y - r)
#         if note_type == 'circle-x':
#             c.setLineWidth(1)
#             c.circle(x, y, r + 1.5, stroke=1, fill=0)
#     else:
#         c.saveState()
#         c.translate(x, y)
#         c.scale(1.2, 0.8)
#         c.circle(0, 0, r, fill=1, stroke=0)
#         c.restoreState()
#
#     c.setLineWidth(1)
#     stem_height = 25
#     c.line(x + r, y, x + r, y + stem_height)

# --- COMMENTED OUT OLD BEAM-READY NOTEHEAD FUNCTION ---
# def draw_notehead(c, x, y, note_type, staff_y_base):
#     #Draws ONLY the notehead and ledger lines (stems are handled by beaming).#
#     r = 3.5 # Tweak 3: Increased from 2.7 to make the note blobs a wee bit bigger
#     top_line_y = staff_y_base + (4 * LINE_SPACING)
#     bottom_line_y = staff_y_base
#
#     # Ledger lines
#     if y >= top_line_y + LINE_SPACING:
#         c.setLineWidth(1)
#         c.line(x - 8, y, x + 8, y)
#     elif y <= bottom_line_y - LINE_SPACING:
#         c.setLineWidth(1)
#         c.line(x - 8, y, x + 8, y)
#
#     if note_type == 'x' or note_type == 'circle-x':
#         c.setLineWidth(2)
#         c.line(x - r, y - r, x + r, y + r)
#         c.line(x - r, y + r, x + r, y - r)
#         if note_type == 'circle-x':
#             c.setLineWidth(1)
#             c.circle(x, y, r + 1.5, stroke=1, fill=0)
#     else:
#         c.saveState()
#         c.translate(x, y)
#         c.scale(1.2, 0.8)
#         c.circle(0, 0, r, fill=1, stroke=0)
#         c.restoreState()

# --- COMMENTED OUT OLD RENDERING LOOP ---
        # if m in events_by_measure:
        #     for event in events_by_measure[m]:
        #         time_sec = event['time']
        #         drum_types = event['drums']
        #         rel_time = time_sec % sec_per_measure
        #         padding = 15
        #         usable_width = measure_width - (2 * padding)
        #         rel_x = (rel_time / sec_per_measure) * usable_width
        #         note_x = measure_start_x + padding + rel_x
        #
        #         for drum_type in drum_types:
        #             d_map = constants.DRUM_NOTATION_MAP.get(drum_type, constants.DRUM_NOTATION_MAP['kick'])
        #             staff_pos = d_map.get('staff_position', 'F3')
        #             note_head = d_map.get('note_head', 'normal')
        #             note_y = get_vertical_position(staff_pos, current_y)
        #             draw_note(c, note_x, note_y, note_head, current_y)

        # --- COMMENTED OUT SINGLE-VOICE BEAMING RENDERING LOOP ---
        # if m in events_by_measure:
        #     # 1. Group all events in this measure by Beat (Quarter Note)
        #     beats = defaultdict(list)
        #     for event in events_by_measure[m]:
        #         rel_time = event['time'] % sec_per_measure
        #         beat_idx = int(rel_time / seconds_per_beat)
        #         beats[beat_idx].append(event)
        #
        #     # 2. Render each beat group
        #     for beat_idx, event_list in beats.items():
        #         beat_x_coords = []
        #         notes_info = []
        #
        #         # Lowest note dictates how far down the stems go
        #         lowest_y = current_y + 100
        #
        #         for event in event_list:
        #             rel_time = event['time'] % sec_per_measure
        #             padding = 15
        #             usable_width = measure_width - (2 * padding)
        #             rel_x = (rel_time / sec_per_measure) * usable_width
        #             note_x = measure_start_x + padding + rel_x
        #
        #             beat_x_coords.append(note_x)
        #
        #             for drum_type in event['drums']:
        #                 d_map = constants.DRUM_NOTATION_MAP.get(drum_type, constants.DRUM_NOTATION_MAP['kick'])
        #                 staff_pos = d_map.get('staff_position', 'F3')
        #                 note_head = d_map.get('note_head', 'normal')
        #                 note_y = get_vertical_position(staff_pos, current_y)
        #
        #                 if note_y < lowest_y:
        #                     lowest_y = note_y
        #
        #                 notes_info.append((note_x, note_y, note_head))
        #
        #         # 3. Draw the actual Noteheads
        #         highest_y_at_x = {}
        #         for nx, ny, nhead in notes_info:
        #             draw_notehead(c, nx, ny, nhead, current_y)
        #             # Track the highest note in a chord to attach the downward stem to
        #             if nx not in highest_y_at_x or ny > highest_y_at_x[nx]:
        #                 highest_y_at_x[nx] = ny
        #
        #         # 4. Draw Stems (Pointing DOWN) and Beams
        #         if beat_x_coords:
        #             stem_length = 25
        #             # Beam sits below the lowest note in the group
        #             beam_y = lowest_y - stem_length
        #
        #             unique_x_coords = sorted(list(set(beat_x_coords)))
        #
        #             # Draw individual downward stems (left side of notehead)
        #             c.setLineWidth(1)
        #             c.setStrokeColor(colors.black)
        #             for nx in unique_x_coords:
        #                 top_y = highest_y_at_x[nx]
        #                 c.line(nx - 2.7, top_y, nx - 2.7, beam_y)
        #
        #             # If multiple rhythmic hits exist in this beat, draw the connecting beam
        #             if len(unique_x_coords) > 1:
        #                 first_x = unique_x_coords[0]
        #                 last_x = unique_x_coords[-1]
        #
        #                 # Primary Beam (8th notes)
        #                 c.setLineWidth(3)
        #                 c.line(first_x - 2.7, beam_y, last_x - 2.7, beam_y)
        #
        #                 # Secondary Beam (16th notes)
        #                 if len(unique_x_coords) > 2:
        #                     c.line(first_x - 2.7, beam_y + 4, last_x - 2.7, beam_y + 4)
        #             else:
        #                 # If it's a single note, give it a tiny 'flag' hook to indicate 8th note
        #                 nx = unique_x_coords[0]
        #                 c.setLineWidth(1)
        #                 c.line(nx - 2.7, beam_y, nx + 2, beam_y + 5)
"""


# --------------------------------------------------------------------------uncomment during testing
# from datetime import datetime
# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndate/time: {datetimestamp}')
# --------------------------------------------------------------------------------------------------
