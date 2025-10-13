# DrumScript/drum_classifier/model_trainer.py
# 1D CNN

import os

import joblib
import json
import pandas as pd
import numpy as np
import librosa
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, f1_score, precision_score, recall_score

# Import TensorFlow and Keras
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Flatten, Conv1D, MaxPooling1D
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.losses import BinaryCrossentropy
from tensorflow.keras.metrics import BinaryAccuracy, Precision, Recall, AUC
from tqdm import tqdm # For progress bars during feature extraction

from drum_model import create_drum_model # drum_classifier/drum_model.py


# --- Configuration ---
# SAMPLE_RATE = 22050
SAMPLE_RATE = 44100 # Amended to reflect constants in other scripts
SEGMENT_LENGTH_SECONDS = 0.2 ## NEED TO CROSS-CHECK WITH OTHER SCRIPTS FOR CONSISTENCY
# Define all UNIQUE drum types that we expect to classify.
# This must match the ALL_DRUM_TYPES list used in process_enst_dataset.py
ALL_DRUM_TYPES = sorted(['kick', 'snare', 'hi-hat', 'crash', 'ride', 'tom']) # Ensure this matches process_enst_dataset.py


# --- Feature Extraction Helper ---
def _extract_features(audio_path, sr, segment_length_seconds):
    """
    Extracts MFCC features from an audio segment.
    """
    try:
        audio, _ = librosa.load(audio_path, sr=sr, mono=True)
        # Ensure the segment has the expected length, pad if necessary
        if len(audio) < int(sr * segment_length_seconds):
            # Pad with zeros
            pad_length = int(sr * segment_length_seconds) - len(audio)
            audio = np.pad(audio, (0, pad_length), mode='constant')
        elif len(audio) > int(sr * segment_length_seconds):
            # Trim if too long
            audio = audio[:int(sr * segment_length_seconds)]

        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        # Transpose so that shape is (time_frames, n_mfccs)
        # For a 0.2s segment at 22050 Hz, this means ~9 time frames (22050 * 0.2 / 2048 hop_length = ~2.15; for MFCC, it's frame-based)
        # librosa.feature.mfcc uses default hop_length=512, so 0.2 * 22050 / 512 = 8.6, so 9 frames.
        mfccs = mfccs.T
        return mfccs
    except Exception as e:
        print(f"Error extracting features from {audio_path}: {e}")
        return None
    


# --- Data Preparation ---
def prepare_dataset(data_dir: str, sr: int, segment_length_seconds: float):
    """
    Prepares the dataset for multi-label classification.
    Loads multi_label_events.csv, extracts features, and creates labels.
    """
    print(f"Loading multi-label metadata from: {data_dir}/ENST_processed/multi_label_events.csv")
    events_filepath = os.path.join(data_dir, "ENST_processed", "multi_label_events.csv")
    
    if not os.path.exists(events_filepath):
        raise FileNotFoundError(f"'{events_filepath}' not found. Please run `process_enst_dataset.py` first.")

    df = pd.read_csv(events_filepath)

    all_features = []
    all_labels = []

    print(f"Extracting features from {len(df)} audio segments...")
    for index, row in tqdm(df.iterrows(), total=len(df), desc="Feature Extraction"):
        audio_segment_path = os.path.join(data_dir, "ENST_processed", row['filename']) # Already corrected this

        features = _extract_features(audio_segment_path, sr, segment_length_seconds)
        
        if features is not None and features.shape == (int(segment_length_seconds * sr / 512) + 1, 40):
            all_features.append(features)
            
            # FIX: Reconstruct multi-hot encoded label vector from individual drum type columns
            label_vector = np.zeros(len(ALL_DRUM_TYPES))
            for i, drum_type in enumerate(ALL_DRUM_TYPES):
                if drum_type in row: # Check if the column exists in the current row's data
                    label_vector[i] = row[drum_type] # Get the 0 or 1 value directly
                # If a drum_type column doesn't exist (unlikely if ALL_DRUM_TYPES is consistent)
                # it will remain 0 due to np.zeros initialization.
            all_labels.append(label_vector)
        else:
            # Handle cases where feature extraction failed or shape is incorrect
            pass

    X = np.array(all_features)
    y = np.array(all_labels)

    print(f"Loaded {X.shape[0]} samples. Features shape: {X.shape}, Labels shape: {y.shape}")

    # Reshape X for StandardScaler: flatten the last two dimensions (time_steps * n_mfcc)
    original_X_shape = X.shape
    X_reshaped_for_scaler = X.reshape(original_X_shape[0], -1)

    scaler = StandardScaler()
    
    X_scaled = scaler.fit_transform(X_reshaped_for_scaler)

    # Reshape X back for the CNN: (num_samples, time_steps, n_mfcc)
    X_scaled_for_cnn = X_scaled.reshape(original_X_shape)

    # Create label map (drum_type to index)
    label_map = {drum: i for i, drum in enumerate(ALL_DRUM_TYPES)}

    return X_scaled_for_cnn, y, scaler, label_map


def create_cnn_model(input_shape, num_classes):
    """
    Creates a 1D CNN model for multi-label drum sound classification.

    Args:
        input_shape (tuple): The shape of the input features (timesteps, num_features).
        num_classes (int): The number of drum classes to classify.

    Returns:
        tf.keras.Model: The compiled Keras CNN model.
    """
    # Determine input shape and number of classes from your data
    # X_train.shape[1] is the number of features (should be 43)
    # y_train.shape[1] is the number of drum types
    # input_shape = X_train.shape[1]

    model = Sequential([
        # First Convolutional Block
        Conv1D(filters=64, kernel_size=3, activation='relu', input_shape=input_shape),
        MaxPooling1D(pool_size=2),
        Dropout(0.3),

        # Flatten the output for the Dense layers
        Flatten(),

        # Dense Layers
        Dense(256, activation='relu'),
        Dropout(0.5),
        Dense(num_classes, activation='sigmoid') # Sigmoid for multi-label classification
    ])

    # Compile the model
    model.compile(optimizer=Adam(learning_rate=0.001),
                  loss=BinaryCrossentropy(),
                  metrics=[BinaryAccuracy(), Precision(), Recall(), AUC()])
    return model


# --- Training and Evaluation ---
def train_and_evaluate_model(data_dir: str, model_save_path: str, scaler_save_path: str,
                             label_map_save_path: str, sr: int = SAMPLE_RATE,
                             segment_length_seconds: float = SEGMENT_LENGTH_SECONDS):
    """
    Trains and evaluates a multi-label drum classification model using a CNN.
    """
    print("-------------------------------------------------------------")
    print("Starting multi-label model training and evaluation process...")

    # 1. Prepare Data
    X, y, scaler, label_map = prepare_dataset(data_dir, sr=sr, segment_length_seconds=segment_length_seconds)

    # 2. Split Data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Train set size: {X_train.shape[0]} samples, Test set size: {X_test.shape[0]} samples.")

    # 3. Create and Compile Model
    # Input shape for Conv1D should be (time_steps, n_mfccs) (2D CNN)
    # input_shape = (X_train.shape[1], X_train.shape[2])  (2D CNN)
    # num_classes = y_train.shape[1] # Number of drum types/labels  (2D CNN)

    # Determine input shape and number of classes from your data
    # X_train.shape[1] is the number of features (should be 43)
    # y_train.shape[1] is the number of drum types
    input_shape = X_train.shape[1]
    num_classes = y_train.shape[1]


    model = create_cnn_model(input_shape, num_classes)
    model.summary()

    # 4. Train Model
    print("\nTraining the CNN model...")
    try:
        history = model.fit(
            X_train, y_train,
            epochs=50, # You can adjust the number of epochs
            batch_size=32, # You can adjust batch size
            validation_split=0.1, # Use a portion of training data for validation during training
            verbose=1 # Show progress bar
        )
    except Exception as e:
        print(f"An error occurred during model training: {e}")
        return # Exit if training fails

    # 5. Evaluate Model
    print("\nEvaluating the model on the test set...")
    loss, accuracy, precision, recall, auc = model.evaluate(X_test, y_test, verbose=0)
    print(f"\nTest Loss: {loss:.4f}")
    print(f"Test Accuracy (Binary): {accuracy:.4f}")
    print(f"Test Precision: {precision:.4f}")
    print(f"Test Recall: {recall:.4f}")
    print(f"Test AUC: {auc:.4f}")

    # For a more detailed report (e.g., per-class metrics if needed, requires predicting on test set)
    # y_pred_probs = model.predict(X_test)
    # y_pred_binary = (y_pred_probs > 0.5).astype(int) # Apply threshold to get binary predictions
    # print("\nClassification Report (threshold=0.5):")
    # print(classification_report(y_test, y_pred_binary, target_names=ALL_DRUM_TYPES, zero_division=0))


    # 6. Save Model, Scaler, and Label Map
    print("\nSaving trained model and components...")
    model.save(model_save_path)
    print(f"Model saved to: {model_save_path}")
    joblib.dump(scaler, scaler_save_path)
    print(f"Scaler saved to: {scaler_save_path}")
    with open(label_map_save_path, 'w') as f:
        json.dump(label_map, f)
    print(f"Label map saved to: {label_map_save_path}")

    print("\nMulti-label model training and evaluation finished.")
    print("\n---------------------------------------------------")


if __name__ == "__main__":
    # Determine project root dynamically
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    print(f'current_script_dir:{current_script_dir}') # TEMP LINE: Included during build for testing
    # Go up one level from drum_classifier/ to DrumScript/
    project_root = os.path.abspath(os.path.join(current_script_dir, os.pardir)) # TEMP LINE: Included during build for testing
    print(f'project_root:{project_root}')

    # Define paths for data and saved models
    data_directory = os.path.join(project_root, "training_data") # Points to 'training_data' which contains 'ENST_processed's
    model_save_directory = os.path.join(project_root, "models")
    
    # Ensure 'models' directory exists
    os.makedirs(model_save_directory, exist_ok=True)

    # File paths for saving
    model_file = os.path.join(model_save_directory, "multi_label_drum_classifier_model.h5") # Changed extension for Keras model
    scaler_file = os.path.join(model_save_directory, "multi_label_scaler.joblib")
    label_map_file = os.path.join(model_save_directory, "multi_label_label_map.json")

    try:
        train_and_evaluate_model(
            data_dir=data_directory,
            model_save_path=model_file,
            scaler_save_path=scaler_file,
            label_map_save_path=label_map_file
        )
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please ensure `process_enst_dataset.py` has been run successfully to create the necessary processed data.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")