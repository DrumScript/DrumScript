# DrumScript/drum_classifier/predict.py
import os
import json
import librosa
import numpy as np
from typing import List, Dict, Any

# --- Drum Mapping Dictionary for Enhanced Output ---
DRUM_METADATA = {
    'kick': { 'midi_pitch': 36, 'note_head_type': 'normal', 'staff_position': 'F2', 'display_name': 'Kick Drum' },
    'snare': { 'midi_pitch': 38, 'note_head_type': 'normal', 'staff_position': 'C3', 'display_name': 'Snare Drum' },
    'hi_hat_closed': { 'midi_pitch': 42, 'note_head_type': 'x', 'staff_position': 'F#3', 'display_name': 'Hi-Hat (Closed)' },
    'hi_hat_open': { 'midi_pitch': 46, 'note_head_type': 'x-open', 'staff_position': 'F#3', 'display_name': 'Hi-Hat (Open)' },
    'low_tom': { 'midi_pitch': 41, 'note_head_type': 'normal', 'staff_position': 'A2', 'display_name': 'Low Tom' },
    # --- Add metadata for our mid tom ---
    'mid_tom': { 'midi_pitch': 45, 'note_head_type': 'normal', 'staff_position': 'C3', 'display_name': 'Mid Tom' }
}

# --- Rule-based thresholds ---
# --- Make the kick rule even more specific ---
KICK_SPECTRAL_CENTROID_MAX = 400  # Kicks are very low. Let's cap them at 400 Hz.

# --- Define a rule space for our Mid Tom ---
MID_TOM_CENTROID_MIN = 400
MID_TOM_CENTROID_MAX = 800 # This now captures our 656.55 value.
MID_TOM_ZCR_MAX = 0.05    # Toms are tonal, not noisy.

# Low Tom rule remains the same
LOW_TOM_CENTROID_MIN = 800
LOW_TOM_CENTROID_MAX = 1500
LOW_TOM_ZCR_MAX = 0.05

SNARE_CENTROID_MIN = 1000
SNARE_CENTROID_MAX = 4000
SNARE_ZCR_MIN = 0.09

HIHAT_CENTROID_MIN = 9000
HIHAT_ZCR_MIN = 0.2
HIHAT_SUSTAIN_THRESHOLD = 0.5

# --- Refractory period constants ---
OPEN_HIHAT_REFRACTORY_PERIOD_S = 0.6
TOM_REFRACTORY_PERIOD_S = 3.0 # Keep this long to handle all toms

# --- Core Classification Logic ---
def predict_drum_hits(onset_features: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    classified_events = []
    last_open_hihat_time = -1.0
    last_tom_time = -1.0

    for onset in onset_features:
        # Refractory period checks
        if last_open_hihat_time > 0 and (onset['onset_time'] - last_open_hihat_time) < OPEN_HIHAT_REFRACTORY_PERIOD_S:
            print(f"\n--- Ignoring Onset at {onset['onset_time']:.2f}s (within refractory period of an open hi-hat) ---")
            continue
        if last_tom_time > 0 and (onset['onset_time'] - last_tom_time) < TOM_REFRACTORY_PERIOD_S:
            print(f"\n--- Ignoring Onset at {onset['onset_time']:.2f}s (within refractory period of a tom) ---")
            continue

        # Debugging block
        print(f"\n--- Processing Onset at {onset['onset_time']:.2f}s ---")
        print(f"  - Spectral Centroid: {onset['spectral_centroid']:.2f}")
        print(f"  - Zero-Crossing Rate: {onset['zero_crossing_rate']:.4f}")
        print(f"  - Sustain Level: {onset['sustain_level']:.2f}")

        # --- RULE 1: Kick Drum (Now more specific) ---
        if onset['spectral_centroid'] < KICK_SPECTRAL_CENTROID_MAX:
            print("  - RESULT: Classified as KICK.")
            classified_events.extend(create_detailed_drum_events(['kick'], onset['onset_time']))
            continue

        # --- NEW RULE: Mid Tom ---
        elif MID_TOM_CENTROID_MIN < onset['spectral_centroid'] < MID_TOM_CENTROID_MAX and \
             onset['zero_crossing_rate'] < MID_TOM_ZCR_MAX:
            print("  - RESULT: Classified as MID TOM.")
            classified_events.extend(create_detailed_drum_events(['mid_tom'], onset['onset_time']))
            last_tom_time = onset['onset_time'] # Trigger tom cooldown
            continue

        # --- RULE 3: Low Tom ---
        elif LOW_TOM_CENTROID_MIN < onset['spectral_centroid'] < LOW_TOM_CENTROID_MAX and \
             onset['zero_crossing_rate'] < LOW_TOM_ZCR_MAX:
            print("  - RESULT: Classified as LOW TOM.")
            classified_events.extend(create_detailed_drum_events(['low_tom'], onset['onset_time']))
            last_tom_time = onset['onset_time'] # Trigger tom cooldown
            continue

        # --- RULE 4: Snare Drum ---
        elif SNARE_CENTROID_MIN < onset['spectral_centroid'] < SNARE_CENTROID_MAX and \
             onset['zero_crossing_rate'] >= SNARE_ZCR_MIN:
            print("  - RESULT: Classified as SNARE.")
            classified_events.extend(create_detailed_drum_events(['snare'], onset['onset_time']))
            continue

        # --- RULE 5: Hi-Hat ---
        elif onset['spectral_centroid'] > HIHAT_CENTROID_MIN and \
             onset['zero_crossing_rate'] >= HIHAT_ZCR_MIN:
            print("  - RESULT: Potentially a Hi-Hat. Checking sustain...")
            if onset['sustain_level'] > HIHAT_SUSTAIN_THRESHOLD:
                print("    - Sustain is HIGH. Classified as OPEN HI-HAT.")
                classified_events.extend(create_detailed_drum_events(['hi_hat_open'], onset['onset_time']))
                last_open_hihat_time = onset['onset_time']
            else:
                print("    - Sustain is LOW. Classified as CLOSED HI-HAT.")
                classified_events.extend(create_detailed_drum_events(['hi_hat_closed'], onset['onset_time']))
            continue
        
        print("  - RESULT: No rule matched.")
    return classified_events

# This helper function is still very useful. It now takes a
# list of classified labels for a single onset (for now, just one label, but
# this supports concurrent hits in the future) and creates the detailed output.
def create_detailed_drum_events(predicted_drums: List[str], onset_time: float) -> List[Dict[str, Any]]:
    
    # Creates detailed drum event objects with metadata for a list of predicted drums.
    
    detailed_events = []
    for drum_type in predicted_drums:
        if drum_type in DRUM_METADATA:
            event = {
                'drum_type': drum_type,
                'onset_time_seconds': round(onset_time, 2),
                'midi_pitch': DRUM_METADATA[drum_type]['midi_pitch'],
                'note_head_type': DRUM_METADATA[drum_type]['note_head_type'],
                'staff_position': DRUM_METADATA[drum_type]['staff_position'],
            }
            detailed_events.append(event)
    return detailed_events


# --- Main execution block for testing ---
if __name__ == "__main__":
        # --- Project-Specific Imports ---
    # These functions are now imported from the audio_processor module,
    # creating a clear workflow: 1. Process Audio -> 2. Classify Features.
    # from DrumScriptimport audio_processor
    from audio_processor.audio_loader import load_audio
    from audio_processor.onset_detector import detect_onsets
    from audio_processor.feature_extractor import extract_features_for_onsets

    # This block now demonstrates the new, correct workflow:
    # 1. Load audio and find onsets using audio_processor.
    # 2. Extract features for those onsets using audio_processor.
    # 3. Classify the features using the rule-based system in this script.

    print("--- Running Rule-Based Drum Classifier Example ---")

    # Define paths
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir)) # Go up two levels
    # IMPORTANT: Place a test audio file in test_audio folder to run the example.
    test_audio_path = os.path.join(project_root, "test_audio", "test.wav")
    print(f'project_root: {project_root}')
    print(f'test_audio_path: {test_audio_path}')
    

    if not os.path.exists(test_audio_path):
        print(f"Error: Test audio file not found at {test_audio_path}")
        print("Please place a .wav file named 'test.wav' in the 'test_audio' directory.")
    else:
        # --- 1. Audio Processing ---
        print(f"Loading and processing audio file: {test_audio_path}")
        y, sr = load_audio(test_audio_path, sr=44100)
        onset_times = detect_onsets(y, sr)
        print(f"Detected {len(onset_times)} onsets.")

        # --- 2. Feature Extraction ---
        print("Extracting features for each onset...")
        all_onset_features = extract_features_for_onsets(y, sr, onset_times)
        print("Feature extraction complete.")

        # --- 3. Classification ---
        print("Classifying onsets using rule-based system...")
        classified_drum_events = predict_drum_hits(all_onset_features)
        # print(f"Classification complete. Found {len(classified_drum_events)} potential kick drum events.") # COMMENT OUT BUT KEEP FOR NOW. REMOVE LATER
        print(f"Classification complete. Found {len(classified_drum_events)} drum events.")

        # --- 4. Output Results ---
        if classified_drum_events:
            output_dir = os.path.dirname(__file__)
            output_filepath = os.path.join(output_dir, "prediction_output.json")

            try:
                with open(output_filepath, 'w') as f:
                    json.dump(classified_drum_events, f, indent=4)
                print(f"\nSuccessfully exported classified events to: {output_filepath}")
            except Exception as e:
                print(f"\nError exporting results to JSON file: {e}")

            print("\n--- First 10 Classified Events ---")
            for event in classified_drum_events[:10]:
                print(f"Time: {event['onset_time_seconds']:.2f}s, Type: {event['drum_type']}")
        else:
            print("\nNo drum events were classified based on the current rules.")
            print("-------------------------------------------------------------")



""" OLD CODE BLOCK (ML-BASED LOGIC) --- KEEP FOR NOW
# --- Feature Extraction Helper (copy from model_trainer.py) ---
def _extract_features(audio_segment, sr, segment_length_seconds):
    
    # Extracts MFCC features from an audio segment (numpy array)."
    # Ensures the segment has the expected length, padding if necessary."
    
    try:
        # Pad with zeros if the segment is shorter than expected
        if len(audio_segment) < int(sr * segment_length_seconds):
            pad_length = int(sr * segment_length_seconds) - len(audio_segment)
            audio_segment = np.pad(audio_segment, (0, pad_length), mode='constant')
        elif len(audio_segment) > int(sr * segment_length_seconds):
            # Trim if the segment is longer (shouldn't happen with proper slicing)
            audio_segment = audio_segment[:int(sr * segment_length_seconds)]

        mfccs = librosa.feature.mfcc(y=audio_segment, sr=sr, n_mfcc=40)
        mfccs = mfccs.T # Transpose to (time_frames, n_mfccs)
        return mfccs
    except Exception as e:
        # print(f"Error extracting features from segment: {e}") # Uncomment for verbose debugging
        return None

# --- Prediction Function (modified to take audio array) ---
def predict_drum_type_from_array(audio_array: np.ndarray, model, scaler, label_map):
    
    # Predicts multi-label drum types for a single audio segment (numpy array).
    
    # 1. Extract features
    features = _extract_features(audio_array, SAMPLE_RATE, SEGMENT_LENGTH_SECONDS)
    
    if features is None:
        return [] # Return empty list if feature extraction failed

    # Ensure features have the correct shape (num_time_steps, num_mfccs)
    # The model expects a batch dimension: (1, num_time_steps, num_mfccs)
    # The time_steps calculation must match model_trainer's _extract_features
    expected_time_steps = int(SEGMENT_LENGTH_SECONDS * SAMPLE_RATE / 512) + 1
    if features.shape != (expected_time_steps, 40):
        # This could happen if the final segment is too short, even after padding.
        # For simplicity, we'll skip it if the shape is fundamentally wrong.
        # A more robust solution might involve further padding/resampling.
        return []

    # Reshape for scaler (flatten time_steps * n_mfcc)
    original_shape = features.shape
    features_reshaped_for_scaler = features.reshape(1, -1) # Reshape to (1, total_features)

    # Scale the features
    scaled_features = scaler.transform(features_reshaped_for_scaler)

    # Reshape back for the CNN model: (num_samples, time_steps, n_mfccs)
    scaled_features_for_cnn = scaled_features.reshape(1, original_shape[0], original_shape[1])

    # 2. Make prediction
    predictions = model.predict(scaled_features_for_cnn, verbose=0) # verbose=0 to suppress Keras output for each segment
    
    # 3. Interpret prediction (multi-label)
    # Apply a threshold (e.g., 0.5) to get binary predictions for each drum type
    threshold = 0.5
    binary_predictions = (predictions > threshold).astype(int)[0] # [0] to get rid of batch dimension
    
    predicted_drums = [
        drum_name for i, drum_name in enumerate(ALL_DRUM_TYPES)
        if binary_predictions[label_map[drum_name]] == 1 # Check if the corresponding label index is 1
    ]

    return predicted_drums

# --- Enhanced Function to Create Detailed Drum Events ---
def create_detailed_drum_events(predicted_drums, onset_time):
    # Creates detailed drum event objects with metadata from a list of predicted drums.
    detailed_events = []
    for drum_type in predicted_drums:
        if drum_type in DRUM_METADATA:
            event = {
                'drum_type': drum_type,
                'onset_time_seconds': onset_time,
                'midi_pitch': DRUM_METADATA[drum_type]['midi_pitch'],
                'note_head_type': DRUM_METADATA[drum_type]['note_head_type'],
                'staff_position': DRUM_METADATA[drum_type]['staff_position'],
                'display_name': DRUM_METADATA[drum_type]['display_name']
            }
            detailed_events.append(event)
    return detailed_events

# --- Enhanced Function to Process Longer Audio Files ---
def process_long_audio_and_predict(audio_filepath: str, model, scaler, label_map, detailed_output=True):
    # Loads a longer audio file, segments it, and predicts drum types for each segment.
    # Returns either detailed events (if detailed_output=True) or simple events.

    print(f"\nProcessing long audio file: {audio_filepath}")
    
    y, sr = librosa.load(audio_filepath, sr=SAMPLE_RATE, mono=True)
    
    segment_length_samples = int(SEGMENT_LENGTH_SECONDS * sr)
    hop_length_samples = int(HOP_LENGTH_SECONDS * sr)

    all_events = []

    # Iterate through the audio, segment by segment
    total_segments = int(np.ceil((len(y) - segment_length_samples + hop_length_samples) / hop_length_samples))
    if total_segments <= 0: # Handle very short files
        print("Audio file too short to create any segments.")
        return []

    for i in tqdm(range(0, len(y) - segment_length_samples + 1, hop_length_samples), total=total_segments, desc="Segmenting & Predicting"):
        start_sample = i
        end_sample = i + segment_length_samples
        
        # Extract segment
        segment = y[start_sample:end_sample]
        
        # Predict for the segment
        predicted_drums = predict_drum_type_from_array(segment, model, scaler, label_map)
        
        if predicted_drums: # Only record if drums were detected
            start_time = librosa.samples_to_time(start_sample, sr=sr)
            
            if detailed_output:
                # Create detailed events for each drum type detected
                detailed_events = create_detailed_drum_events(predicted_drums, start_time)
                all_events.extend(detailed_events)
            else:
                # Create simple event (original format)
                all_events.append({'time': start_time, 'drums': predicted_drums})
            
    if not all_events:
        print("No drum events detected in the entire audio file.")

    return all_events


if __name__ == "__main__":
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_script_dir, os.pardir))

    model_load_directory = os.path.join(project_root, "models")
    
    # Paths for your saved model components
    model_file = os.path.join(model_load_directory, "multi_label_drum_classifier_model.h5") 
    scaler_file = os.path.join(model_load_directory, "multi_label_scaler.joblib")
    label_map_file = os.path.join(model_load_directory, "multi_label_label_map.json")

    # Check if model files exist
    if not all(os.path.exists(f) for f in [model_file, scaler_file, label_map_file]):
        print("Error: One or more model files not found. Please ensure model_trainer.py was run successfully.")
        exit(1)

    # Load the trained model, scaler, and label map
    print("Loading trained model, scaler, and label map...")
    loaded_model = tf.keras.models.load_model(model_file)
    loaded_scaler = joblib.load(scaler_file)
    with open(label_map_file, 'r') as f:
        loaded_label_map = json.load(f)
    print("Model components loaded.")

    # --- Example 1: Predict single segment (as before) ---
    print("\n--- Single Segment Drum Prediction Example ---")
    # Replace with a valid path to an actual audio segment from ENST_processed
    single_segment_audio_path = os.path.join(project_root, "training_data", "ENST_processed", "1_rock-prog_125_beat_4-4.wav") 
    
    if not os.path.exists(single_segment_audio_path):
        print(f"Error: Single segment example audio file not found at {single_segment_audio_path}")
        print("Please replace '1_rock-prog_125_beat_4-4.wav' with a valid path to an actual segment for testing.")
    else:
        print(f"Predicting drum types for single segment: {single_segment_audio_path}")
        predicted_drums_single = predict_drum_type_from_array(
            librosa.load(single_segment_audio_path, sr=SAMPLE_RATE, mono=True)[0], 
            loaded_model, loaded_scaler, loaded_label_map
        )
        print(f"Predicted drum types: {predicted_drums_single}")

    # --- Example 2: Process a longer audio file with detailed output ---
    print("\n--- Longer Audio File Prediction Example (Detailed Output) ---")
    # IMPORTANT: Replace this with the path to your actual longer audio file
    # This could be an MP3, WAV, etc. (librosa supports various formats)
    #long_audio_filepath = os.path.join(project_root, "reference_audio", "test.mp3") 
    long_audio_filepath = os.path.join(project_root, "test_audio", "test.wav") 
    
    if not os.path.exists(long_audio_filepath):
        print(f"Error: Long audio file not found at {long_audio_filepath}")
        print("Please place your longer audio file (e.g., 'test.mp3' or 'test.wav') inside the 'DrumScript/test_audio/' directory, or update the path.")
    else:
        # Generate detailed output
        detailed_results = process_long_audio_and_predict(long_audio_filepath, loaded_model, loaded_scaler, loaded_label_map, detailed_output=True)
        
        if detailed_results:
            print("\n--- Detected Drum Events (Detailed Format) ---")
            for i, event in enumerate(detailed_results[:10]):  # Show first 10 events
                print(f"Event {i}: {event['drum_type']} at {event['onset_time_seconds']:.2f}s - {event['display_name']} (MIDI: {event['midi_pitch']})")
            
            if len(detailed_results) > 10:
                print(f"... and {len(detailed_results) - 10} more events")
            
            # Define the output file path
            output_filepath = os.path.join(current_script_dir, "prediction_output.json")
            
            # Export the detailed results to a JSON file
            try:
                with open(output_filepath, 'w') as f:
                    json.dump(detailed_results, f, indent=4)
                print(f"\nSuccessfully exported detailed drum events to: {output_filepath}")
            except Exception as e:
                print(f"\nError exporting detailed results to JSON file: {e}")

            # Print some detailed events
            print(f"\n--- Sample Detailed Events ---")
            for i, event in enumerate(detailed_results[:5]):
                print(f"Event {i}: {json.dumps(event, indent=2)}")

        else:
            print("\nNo drum events detected in the longer audio file.")
            print("-------------------------------------------------------------")
"""
    
    