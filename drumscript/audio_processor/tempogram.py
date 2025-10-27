# DrumScript/audio_processor/tempo_detector.py
# ------------------------------------------------------------------------------------------------------------
"""
This module contains functions for visualising tempo using librosa's tempogram function
"""
# Import packages: ------------------------------------------------------------------------------------------------
import librosa
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import librosa.display
import os
import argparse
from .audio_loader import load_audio, normalise_audio
from .tempo_detector import estimate_tempo

# --- Define function --------------------------------------------------------------------------------------------
def visualise_tempogram(audio_data, sr, hop_length=256, output_path="tempogram.png"):
    """
    Calculates and saves a tempogram visualization for the given audio.
    """
    oenv = librosa.onset.onset_strength(y=audio_data, sr=sr, hop_length=hop_length)
    tempogram = librosa.feature.tempogram(onset_envelope=oenv, sr=sr, hop_length=hop_length)
    global_tempo = estimate_tempo(audio_data, sr)

    fig, ax = plt.subplots(figsize=(12, 6))
    librosa.display.specshow(tempogram, sr=sr, hop_length=hop_length, 
                             x_axis='time', y_axis='tempo', cmap='magma', ax=ax)
    ax.axhline(global_tempo, color='w', linestyle='--', alpha=0.8, label=f'Global Tempo: {global_tempo:.2f} BPM')
    ax.set_title('Tempogram')
    ax.legend(loc='upper right')
    fig.colorbar(ax.get_children()[0], ax=ax, label='Energy')
    plt.tight_layout()

    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close(fig) # Close the figure to free up memory
    print(f"Tempogram saved to: {output_path}")

# ===========================================================================================================
# MAIN BLOCK - for local testing of this function

if __name__ == "__main__":
    from .audio_loader import load_audio, normalise_audio

    parser = argparse.ArgumentParser(description="Generate a tempogram visualization for a given audio file.")
    parser.add_argument("audio_file_path", type=str,
                        help="Path to the audio file to be processed.")
    args = parser.parse_args()
    actual_drum_recording_path = args.audio_file_path

    try:
        # Load and normalise the audio
        print(f"Attempting to load: {actual_drum_recording_path}")
        audio, sr = load_audio(actual_drum_recording_path, sr=44100)
        normalised_audio = normalise_audio(audio)
        
        # Estimate the tempo
        bpm = estimate_tempo(normalised_audio, sr)
        print(f"Estimated Tempo: {int(round(bpm))} BPM")

        # Visualise the tempogram
        current_script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_script_dir, os.pardir))
        output_image_path = os.path.join(project_root, "visuals", "tempogram.png")
        visualise_tempogram(normalised_audio, sr, output_path=output_image_path)
        
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}")
    print("\n#==================================================================================================")
        
#-----------------------------------------------------------------------------------------------------------

    