# DrumScript/utils/config.py (Updated for full application configuration)
from notation_generator import constants
# Audio Processing Settings
AUDIO_SAMPLE_RATE = 22050
AUDIO_SEGMENT_LENGTH_SECONDS = 0.2

# Model Settings
MODELS_DIRECTORY = 'models' # Path relative to project root
MODEL_TYPE = 'cnn' # e.g., 'random_forest', 'svm', etc.

# Notation Generation Settings
DEFAULT_TEMPO_BPM = 120
QUANTIZATION_SUBDIVISION = 16

# PDF export settings
PDF_PAGE_SIZE = 'A4'
PDF_MARGIN_TOP = 50
PDF_MARGIN_BOTTOM = 50
PDF_MARGIN_LEFT = 50
PDF_MARGIN_RIGHT = 50
PDF_FONT = 'Helvetica'
PDF_FONT_SIZE_TITLE = 24
PDF_FONT_SIZE_BODY = 12

# Staff and note rendering settings
STAFF_LINE_SPACING = 10
NOTE_HEAD_SIZE = 8

# Drum part mapping (should align with your model's classification)
"""DRUM_NOTATION_MAP = { # removing for now while testing
    'kick': {'note_head': 'x', 'staff_position': 'F2'},
    'snare': {'note_head': 'normal', 'staff_position': 'C3'},
    'hi-hat': {'note_head': 'x', 'staff_position': 'G3'},
    'crash': {'note_head': 'x', 'staff_position': 'C4'},
    'ride': {'note_head': 'x', 'staff_position': 'A3'},
    # Add more drum types as classified by your model
}
"""
def get_config():
    """
    Returns a comprehensive dictionary of all application-wide configuration settings.
    """
    return {
        'audio': {
            'sample_rate': AUDIO_SAMPLE_RATE,
            'segment_length_seconds': AUDIO_SEGMENT_LENGTH_SECONDS,
        },
        'model': {
            'models_dir': MODELS_DIRECTORY,
            'type': MODEL_TYPE,
        },
        'notation': {
            'default_tempo': DEFAULT_TEMPO_BPM,
            'subdivision': QUANTIZATION_SUBDIVISION,
            'pdf_settings': {
                'page_size': PDF_PAGE_SIZE,
                'margin_top': PDF_MARGIN_TOP,
                'margin_bottom': PDF_MARGIN_BOTTOM,
                'margin_left': PDF_MARGIN_LEFT,
                'margin_right': PDF_MARGIN_RIGHT,
                'font': PDF_FONT,
                'font_size_title': PDF_FONT_SIZE_TITLE,
                'font_size_body': PDF_FONT_SIZE_BODY,
            },
            'staff_line_spacing': STAFF_LINE_SPACING,
            'note_head_size': NOTE_HEAD_SIZE,
            #'drum_notation_map': DRUM_NOTATION_MAP,
            'drum_notation_map': constants.DRUM_NOTATION_MAP
        }
    }