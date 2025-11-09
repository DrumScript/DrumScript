This version makes significant changes to handle multi-label classification using a **Convolutional Neural Network (CNN)** with TensorFlow/Keras.

**Key Changes:**

1.  **Imports:** Added `tensorflow` and related Keras modules.
2.  **Data Loading (`load_multi_label_dataset` function):**
      * This new function replaces the previous `prepare_dataset` for multi-label training.
      * It reads `multi_label_events.csv` to get filenames and one-hot encoded labels.
      * It loads each audio file, extracts MFCC features, and normalizes them using `StandardScaler`.
      * It prepares `X` (features) and `y` (multi-hot encoded labels) for CNN training.
3.  **CNN Model Definition (`create_cnn_model` function):**
      * Defines a simple CNN architecture suitable for audio features.
      * The output layer uses `sigmoid` activation and has a number of units equal to the total number of `ALL_DRUM_TYPES`, allowing it to predict the presence of multiple drum types.
4.  **`train_and_evaluate_model` function:**
      * Calls `load_multi_label_dataset` to get the training data.
      * Splits data into training and testing sets.
      * Initializes and compiles the CNN model with `BinaryCrossentropy` loss (appropriate for multi-label) and relevant metrics (`BinaryAccuracy`, `Precision`, `Recall`).
      * Trains the model using `model.fit()`.
      * Evaluates the model on the test set.
      * Saves the trained Keras model in the TensorFlow SavedModel format (`.h5` is also an option but SavedModel is more flexible). The scaler and label map (which is now `ALL_DRUM_TYPES`) are also saved.

**Before you run this:**

  * **Install TensorFlow:** If you haven't already, you'll need to install TensorFlow.
    ```bash
    pip install tensorflow
    ```
  * Ensure all other required libraries (`librosa`, `pretty_midi`, `soundfile`, `pandas`, `numpy`, `scikit-learn`) are installed. You can typically do this with `pip install -r requirements.txt` if your `requirements.txt` is up to date, or by installing them individually.
  * Make sure you have already run the **updated `process_enst_dataset.py`** script to generate the `ENST_processed` directory and the `multi_label_events.csv` file.

Now, replace the entire content of `drum_classifier/model_trainer.py` with the following code:

```python
# DrumScript/drum_classifier/model_trainer.py

import os
import numpy as np
import joblib
import json
import pandas as pd
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


# --- Configuration ---
SAMPLE_RATE = 22050
SEGMENT_LENGTH_SECONDS = 0.2
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
            # Pad with zeros to the expected length
            pad_length = int(sr * segment_length_seconds) - len(audio)
            audio = np.pad(audio, (0, pad_length), mode='constant')
        elif len(audio) > int(sr * segment_length_seconds):
            # Trim if too long
            audio = audio[:int(sr * segment_length_seconds)]

        # Extract MFCCs
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=40)
        # Flatten MFCCs to a 1D array for initial processing with a Dense layer or simple CNN
        # If using more complex CNN, we might keep it 2D and add a Conv2D layer
        # For simplicity, we'll reshape to (num_mfccs, num_frames, 1) for Conv1D
        mfccs = mfccs.T # Transpose to (time_frames, n_mfccs)
        return mfccs
    except Exception as e:
        print(f"Error extracting features from {audio_path}: {e}")
        return None

# --- Data Loading for Multi-Label ---
def load_multi_label_dataset(data_dir: str, sr: int, segment_length_seconds: float):
    """
    Loads multi-label drum event data from the ENST_processed directory and CSV.
    """
    processed_dir = os.path.join(data_dir, "ENST_processed")
    labels_csv_path = os.path.join(processed_dir, "multi_label_events.csv")

    if not os.path.exists(labels_csv_path):
        raise FileNotFoundError(
            f"ERROR: multi_label_events.csv not found at {labels_csv_path}. "
            "Please run process_enst_dataset.py first."
        )

    print(f"Loading multi-label metadata from: {labels_csv_path}")
    df = pd.read_csv(labels_csv_path)

    features = []
    labels = [] # Will store one-hot encoded labels

    print(f"Extracting features from {len(df)} audio segments...")
    for index, row in tqdm(df.iterrows(), total=len(df), desc="Extracting features"):
        filename = row['filename']
        audio_path = os.path.join(processed_dir, filename)

        if not os.path.exists(audio_path):
            print(f"Warning: Audio file not found for {filename}. Skipping.")
            continue
        
        mfccs = _extract_features(audio_path, sr, segment_length_seconds)
        if mfccs is not None:
            features.append(mfccs)
            # Extract multi-hot encoded labels directly from DataFrame row
            # Exclude 'filename' column
            current_labels = row[ALL_DRUM_TYPES].values.astype(np.float32)
            labels.append(current_labels)

    if not features:
        raise ValueError("No features were extracted. Check your data paths and audio files.")

    # Convert lists to numpy arrays
    X = np.array(features)
    y = np.array(labels)

    # Apply StandardScaler
    # Reshape X for StandardScaler: (num_samples, num_time_frames * num_mfccs)
    original_shape = X.shape
    X_reshaped_for_scaler = X.reshape(original_shape[0], -1) # Flatten each sample's features

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_reshaped_for_scaler)
    
    # Reshape back to (num_samples, num_time_frames, num_mfccs) for CNN input
    X_final = X_scaled.reshape(original_shape)

    print(f"Loaded {len(X_final)} samples. Features shape: {X_final.shape}, Labels shape: {y.shape}")
    
    # The label_map for multi-label is simply the list of all_drum_types
    label_map = {drum_type: idx for idx, drum_type in enumerate(ALL_DRUM_TYPES)}

    return X_final, y, scaler, label_map

# --- CNN Model Definition ---
def create_cnn_model(input_shape, num_classes):
    """
    Creates a simple Convolutional Neural Network (CNN) model for multi-label classification.
    """
    model = Sequential([
        # Input layer expects (time_frames, n_mfcc, 1) or (num_mfcc, time_frames, 1)
        # Our _extract_features returns (time_frames, n_mfcc)
        # Keras Conv1D expects (batch, timesteps, features)
        # So we use X.reshape(X.shape[0], X.shape[1], X.shape[2], 1) if MFCCs are 2D
        # For our (time_frames, n_mfcc) 2D input from MFCCs, we'll add an extra dim.
        Conv1D(filters=64, kernel_size=5, activation='relu', input_shape=input_shape),
        MaxPooling1D(pool_size=2),
        Dropout(0.3),

        Conv1D(filters=128, kernel_size=3, activation='relu'),
        MaxPooling1D(pool_size=2),
        Dropout(0.3),

        Flatten(), # Flatten the output for the Dense layers
        Dense(256, activation='relu'),
        Dropout(0.5),
        Dense(num_classes, activation='sigmoid') # Sigmoid for multi-label classification
    ])

    # Adam optimizer is a good default
    optimizer = Adam(learning_rate=0.001)
    
    # BinaryCrossentropy for multi-label classification
    # Metrics for multi-label evaluation
    model.compile(optimizer=optimizer,
                  loss=BinaryCrossentropy(),
                  metrics=[BinaryAccuracy(), Precision(), Recall(), AUC(multi_label=True)])
    
    model.summary()
    return model


# --- Main Training Function ---
def train_and_evaluate_model(data_dir: str, model_save_path: str, scaler_save_path: str,
                             label_map_save_path: str, sr: int = SAMPLE_RATE,
                             segment_length_seconds: float = SEGMENT_LENGTH_SECONDS):
    """
    Trains and evaluates a drum classification model using multi-label data.
    """
    print("Starting multi-label model training and evaluation process...")

    # 1. Prepare Data
    try:
        X, y, scaler, label_map = load_multi_label_dataset(data_dir, sr=sr, segment_length_seconds=segment_length_seconds)
    except (FileNotFoundError, ValueError) as e:
        print(f"Error preparing dataset: {e}")
        return

    # Check data dimensions
    if X.ndim != 3: # Expected (num_samples, time_frames, n_mfcc)
         print(f"Warning: X has {X.ndim} dimensions. Expected 3. Reshaping for CNN.")
         # If MFCCs are flattened to 1D, reshape back to (samples, 1, features)
         # For Conv1D, input needs to be (batch, timesteps, features).
         # If _extract_features returns (num_time_frames, n_mfcc), then X.shape is (num_samples, num_time_frames, n_mfcc)
         # This is the correct shape for Conv1D. No extra reshaping needed here.
         pass # No reshaping needed if _extract_features returns (time_frames, n_mfcc)

    # 2. Split Data
    # Use stratify if possible (for single label), but for multi-label, it's more complex.
    # Simple split is often sufficient for large datasets.
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"Train set size: {len(X_train)} samples, Test set size: {len(X_test)} samples.")

    # 3. Create and Compile Model
    # Input shape for CNN: (time_frames, n_mfcc)
    input_shape = (X_train.shape[1], X_train.shape[2])
    num_classes = y_train.shape[1] # Number of distinct drum types
    
    model = create_cnn_model(input_shape, num_classes)

    # 4. Train Model
    print("\nTraining the CNN model...")
    history = model.fit(
        X_train, y_train,
        epochs=50, # You might need to adjust this (more or less) based on convergence
        batch_size=32,
        validation_split=0.1, # Use a small part of training data for validation during training
        verbose=1
    )

    # 5. Evaluate Model
    print("\nEvaluating the model on the test set...")
    loss, binary_accuracy, precision, recall, auc = model.evaluate(X_test, y_test, verbose=0)
    
    print(f"\n--- Test Set Evaluation ---")
    print(f"Loss: {loss:.4f}")
    print(f"Binary Accuracy: {binary_accuracy:.4f}")
    print(f"Precision (macro avg): {precision:.4f}")
    print(f"Recall (macro avg): {recall:.4f}")
    print(f"AUC (macro avg): {auc:.4f}")

    # For a more detailed report, you can predict and use sklearn's classification_report
    y_pred_proba = model.predict(X_test)
    y_pred = (y_pred_proba > 0.5).astype(int) # Convert probabilities to binary predictions

    print("\nClassification Report (threshold 0.5):")
    # For multi-label, classification_report needs specific handling, often per-class.
    # Or, it needs to be adapted. F1-score for multi-label is often micro or macro averaged.
    # For simplicity, print overall F1, precision, recall using weighted average
    
    # Flatten y_test and y_pred for sklearn metrics for a single report
    # This might not be ideal for per-label insight but gives overall
    
    # Option 1: Per-class metrics
    report = classification_report(y_test, y_pred, target_names=ALL_DRUM_TYPES, zero_division=0)
    print(report)

    # Option 2: Aggregated metrics
    f1_micro = f1_score(y_test, y_pred, average='micro', zero_division=0)
    f1_macro = f1_score(y_test, y_pred, average='macro', zero_division=0)
    print(f"Micro-averaged F1 Score: {f1_micro:.4f}")
    print(f"Macro-averaged F1 Score: {f1_macro:.4f}")


    # 6. Save Model, Scaler, and Label Map
    print("\nSaving trained model, scaler, and label map...")
    
    # Save TensorFlow Keras model
    model.save(model_save_path)
    print(f"CNN model saved to: {model_save_path}")

    # Save StandardScaler
    joblib.dump(scaler, scaler_save_path)
    print(f"StandardScaler saved to: {scaler_save_path}")

    # Save label map (which is ALL_DRUM_TYPES list)
    with open(label_map_save_path, 'w') as f:
        json.dump(label_map, f) # label_map is now {drum_type: index}
    print(f"Label map saved to: {label_map_save_path}")

    print("\nMulti-label model training and evaluation finished.")


if __name__ == "__main__":
    # Determine project root dynamically
    current_script_dir = os.path.dirname(os.path.abspath(__file__))
    # Go up one level from drum_classifier/ to DrumScript/
    project_root = os.path.abspath(os.path.join(current_script_dir, os.pardir))

    # Define paths for data and saved models
    data_directory = os.path.join(project_root, "training_data") # Points to 'training_data' which contains 'ENST_processed'
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
            label_map_save_path=label_map_file,
            sr=SAMPLE_RATE,
            segment_length_seconds=SEGMENT_LENGTH_SECONDS
        )
    except Exception as e:
        print(f"An error occurred during model training: {e}")
        import traceback
        traceback.print_exc()

```