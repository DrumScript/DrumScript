# DrumScript/data_labeller/data_labeller.py

import os
import sys
# This ensures the 'DrumScript' root directory is in sys.path
# allowing for imports like 'from audio_processor import ...'
# when data_labeller.py is run from DrumScript/data_labeller/
current_script_dir = os.path.dirname(os.path.abspath(__file__))
# Go up one level from 'data_labeller/' to reach the 'DrumScript/' root
project_root = os.path.abspath(os.path.join(current_script_dir, os.pardir))

if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Your existing imports follow ---
import librosa
import numpy as np
import json
import csv
from pathlib import Path
from typing import List, Dict, Any
import sounddevice as sd
import soundfile as sf
import time

# Now these imports should work because DrumScript/ (the project root) is on sys.path
from audio_processor.audio_loader import load_audio, normalise_audio
from audio_processor.onset_detector import detect_onsets
from audio_processor.feature_extractor import extract_features


def play_audio_segment(y: np.ndarray, sr: int):
    """Plays an audio segment."""
    print("Playing segment...")
    try:
        sd.play(y, sr)
        sd.wait() # Wait until playback is finished
    except Exception as e:
        print(f"Error playing audio segment: {e}. Make sure sounddevice is configured correctly.")
        print("You might need to install portaudio: `brew install portaudio` (macOS), `sudo apt-get install libportaudio2` (Ubuntu/Debian) or similar for your OS.")

def extract_features_for_segment(y_segment: np.ndarray, sr: int) -> Dict[str, Any]:
    """
    Extracts relevant features for a given audio segment.
    Includes spectral centroid as a 'frequency' representative.
    """
    features = {}
    if len(y_segment) > 0:
        # MFCCs (commonly used for drum classification)
        # Using a fixed n_mfcc=13, which is common
        mfccs = librosa.feature.mfcc(y=y_segment, sr=sr, n_mfcc=13)
        features['mfccs_mean'] = mfccs.mean(axis=1).tolist() if mfccs.size > 0 else [0.0]*13
        features['mfccs_std'] = mfccs.std(axis=1).tolist() if mfccs.size > 0 else [0.0]*13

        # Spectral Centroid (a good indicator of 'brightness' or average frequency)
        # Add a small epsilon to prevent division by zero for very quiet segments
        spectral_centroids = librosa.feature.spectral_centroid(y=y_segment + 1e-6, sr=sr)
        features['spectral_centroid_mean_hz'] = float(spectral_centroids.mean()) if spectral_centroids.size > 0 else 0.0
        features['spectral_centroid_std_hz'] = float(spectral_centroids.std()) if spectral_centroids.size > 0 else 0.0

        # Root Mean Square (RMS) energy (loudness)
        rms = librosa.feature.rms(y=y_segment)
        features['rms_mean'] = float(rms.mean()) if rms.size > 0 else 0.0
        features['rms_std'] = float(rms.std()) if rms.size > 0 else 0.0

    return features

def process_and_label_audio(
    audio_filepath: Path,
    output_dir: Path, # Directory to save labelled data and audio segments
    onset_offset_ms: int = 50, # Time before onset to start segment
    onset_duration_ms: int = 200, # Duration after onset for segment
    onset_pre_max: int = 1, # Parameters for librosa onset detection
    onset_post_max: int = 1,
    onset_pre_avg: int = 1,
    onset_post_avg: int = 1,
    onset_wait: int = 1,
    onset_delta: float = 0.03, # Lower delta can make it more sensitive to small peaks (e.g., fast double bass)
    onset_backtrack: bool = False # Set to False for very fast, distinct hits to avoid merging
) -> List[Dict[str, Any]]:
    """
    Loads an audio file, detects onsets, and interactively prompts the user
    to label each detected drum event. It also saves each segment to an audio file.
    """
    print(f"\n--- Processing '{audio_filepath.name}' for labelling ---")
    y, sr = load_audio(str(audio_filepath))
    y = normalise_audio(y)

    # Create a subdirectory for audio segments within the main output_dir 
    audio_segments_output_path = output_dir / "audio_segments"
    audio_segments_output_path.mkdir(parents=True, exist_ok=True)

    # Use existing onset detection logic, potentially with refined parameters
    onset_frames = detect_onsets(
        audio_data=y, sr=sr
        #audio_data=y, sr=sr,
        #pre_max=onset_pre_max, post_max=onset_post_max,
        #pre_avg=onset_pre_avg, post_avg=onset_post_avg,
        #wait=onset_wait, delta=onset_delta, backtrack=onset_backtrack
    )

    onset_times = librosa.frames_to_time(onset_frames, sr=sr)
    print(f"Detected {len(onset_times)} onsets in '{audio_filepath.name}'.")

    labelled_events = []
    for i, onset_time in enumerate(onset_times):
        # Define segment boundaries
        start_time = max(0, onset_time - (onset_offset_ms / 1000.0))
        end_time = min(librosa.get_duration(y=y, sr=sr), onset_time + (onset_duration_ms / 1000.0))

        # Convert times to sample indices
        start_sample = int(start_time * sr)
        end_sample = int(end_time * sr)

        # Extract audio segment
        y_segment = y[start_sample:end_sample]

        # Save the audio segment to a file
        segment_filename = f"{audio_filepath.stem}_event_{i+1}_onset_{onset_time:.2f}s.wav"
        segment_filepath = audio_segments_output_path / segment_filename
        
        try:
            sf.write(str(segment_filepath), y_segment, sr)
            print(f"Saved segment to: {segment_filepath}")
        except Exception as e:
            print(f"Error saving audio segment {segment_filepath}: {e}")
            segment_filepath = None # Mark as failed if saving fails

        print(f"\n--- Event {i+1}/{len(onset_times)} at {onset_time:.2f}s ---")
        play_audio_segment(y_segment, sr)

        # Extract features for the segment
        segment_features = extract_features_for_segment(y_segment, sr)

        # Prompt for user label
        label = input("Enter label(s) for this drum event (e.g., kick, snare, kick+snare): ").strip()
        while not label:
            print("Label cannot be empty. Please provide a label.")
            label = input("Enter label(s) for this drum event (e.g., kick, snare, kick+snare): ").strip()

        event_data = {
            "audio_filename": audio_filepath.name,
            "onset_time_s": float(onset_time),
            "segment_start_s": float(start_time),
            "segment_end_s": float(end_time),
            "segment_duration_s": float(end_time - start_time),
            "label": label,
            "saved_audio_segment_path": str(segment_filepath) if segment_filepath else None,
            "features": segment_features
        }
        labelled_events.append(event_data)

    print(f"Finished processing '{audio_filepath.name}'.")
    return labelled_events

def generate_labelled_dataset(audio_file_paths: List[str], output_dir: str):
    """
    Main function to generate a labelled dataset from multiple audio files.

    Args:
        audio_file_paths (List[str]): List of paths to input audio files.
        output_dir (str): Directory to save the JSON and CSV output files,
                          and a subdirectory for audio segments.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    all_labelled_events = []
    test_audio_path = os.path.join(project_root, "DrumScript/test_audio", "test.wav") # Change .wav to .mp3 if using MP3, or other audio format

    print(f"test_audio_path: {test_audio_path}")
    print(f"audio_file_path: {audio_file_paths}")

    for test_audio_path in audio_file_paths:
        file_path = Path(test_audio_path)
        if not file_path.exists():
            print(f"Warning: Audio file not found: {test_audio_path}. Skipping.")
            continue
        if not file_path.suffix.lower() in ['.mp3', '.wav', '.flac', '.ogg']:

            print(f"Warning: Unsupported audio format for {test_audio_path}. Skipping.")
            continue

        labelled_events_for_file = process_and_label_audio(file_path, output_path)
        all_labelled_events.extend(labelled_events_for_file)

    if not all_labelled_events:
        print("No events were labelled. No output files generated.")
        return

    # Save to JSON
    json_output_filepath = output_path / "labelled_drum_dataset.json"
    with open(json_output_filepath, 'w') as f:
        json.dump(all_labelled_events, f, indent=4)
    print(f"\nLabelled dataset saved to: {json_output_filepath}")

    # Save to CSV
    csv_output_filepath = output_path / "labelled_drum_dataset.csv"
    if all_labelled_events:
        csv_data = []
        # Dynamically build feature headers based on actual extracted features
        mfcc_mean_headers = [f"mfccs_mean_{i}" for i in range(13)]
        mfcc_std_headers = [f"mfccs_std_{i}" for i in range(13)]
        
        feature_specific_headers = [
            "spectral_centroid_mean_hz", "spectral_centroid_std_hz",
            "rms_mean", "rms_std"
        ]
        
        base_headers = [
            "audio_filename", "onset_time_s", "segment_start_s",
            "segment_end_s", "segment_duration_s", "label",
            "saved_audio_segment_path" # Added this field
        ]
        
        all_headers = base_headers + mfcc_mean_headers + mfcc_std_headers + feature_specific_headers

        for event in all_labelled_events:
            row = {
                "audio_filename": event["audio_filename"],
                "onset_time_s": event["onset_time_s"],
                "segment_start_s": event["segment_start_s"],
                "segment_end_s": event["segment_end_s"],
                "segment_duration_s": event["segment_duration_s"],
                "label": event["label"],
                "saved_audio_segment_path": event["saved_audio_segment_path"] # Added this field
            }
            # Flatten MFCCs and other features
            features_dict = event.get("features", {})
            for i, val in enumerate(features_dict.get("mfccs_mean", [])):
                row[f"mfccs_mean_{i}"] = val
            for i, val in enumerate(features_dict.get("mfccs_std", [])):
                row[f"mfccs_std_{i}"] = val
            
            row["spectral_centroid_mean_hz"] = features_dict.get("spectral_centroid_mean_hz")
            row["spectral_centroid_std_hz"] = features_dict.get("spectral_centroid_std_hz")
            row["rms_mean"] = features_dict.get("rms_mean")
            row["rms_std"] = features_dict.get("rms_std")
            
            csv_data.append(row)

        with open(csv_output_filepath, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=all_headers)
            writer.writeheader()
            writer.writerows(csv_data)
        print(f"Labelled dataset saved to: {csv_output_filepath}")

if __name__ == "__main__":
    # --- IMPORTANT: Replace with your actual paths for testing ---
    # Example usage: 
    input_audio_paths = [
        "../test_audio/test.wav", # Corrected path to point to DrumScript/test_audio/test.wav
        # If you also have test.mp3 and want to include it later, it would be:
         #"../test_audio/test.mp3",
    ]
#if __name__ == "__main__":
    # --- IMPORTANT: Replace with your actual paths for testing ---
    # Create example_recordings directory and put your .mp3 or .wav files there.
    # For initial testing, you can use the provided test.mp3/test.wav:
    # "test_audio/test.mp3" or "test_audio/test.wav"
    
    # Example usage:
    #input_audio_paths = [
        #"test_audio/reference_audio/test.mp3", # Example 
        #"test_audio/test.mp3", # Change .mp3 to .wav if using WAV, or other audio format
     #   "test_audio/test.wav" # Change .wav to .mp3if using MP3, or other audio format
        # "path/to/your/groove_1.wav",
        # "path/to/your/double_bass_run.mp3",
        # Add as many audio files as you want to label
    #]

    output_dataset_dir = "labelled_datasets" # This directory will be created

    print("Starting labelled dataset generation...")
    generate_labelled_dataset(input_audio_paths, output_dataset_dir)
    print("Labelled dataset generation complete.")

