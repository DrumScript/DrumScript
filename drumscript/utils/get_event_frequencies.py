# drumscript/utils/get_event_frequencies.py
"""
Utility script to measure the fundamental frequency of a kick drum sample.
Uses hardcoded file path to test (see TEST_AUDIO ~line101)
"""

import json

import librosa
import numpy as np

# Import your existing modules (adjust imports based on your exact structure)
# Assuming running from the root as 'uv run -m drumscript.generate_event_frequencies'
from drumscript.audio_processor import audio_loader, onset_detector


def extract_frequency_data(y_segment, sr):
    """
    Extracts key frequency metrics for a single audio event.

    :param y_segment: Audio segment array.
    :type y_segment: np.ndarray
    :param sr: Sampling rate.
    :type sr: int
    :return: Dictionary of frequency metrics.
    :rtype: dict
    """
    # 1. Compute Short-Time Fourier Transform (STFT)
    D = np.abs(librosa.stft(y_segment))

    # 2. Calculate Spectral Centroid (The "Center of Mass" / Brightness)
    # This is excellent for distinguishing Kicks (low) vs Hi-Hats (high)
    centroid = librosa.feature.spectral_centroid(S=D, sr=sr)
    mean_centroid = float(np.mean(centroid))

    # 3. Calculate Dominant Frequency (The loudest frequency bin)
    # Useful for finding the specific "tone" of a snare or tom
    frequencies = librosa.fft_frequencies(sr=sr)
    # Sum energy across time to get an aggregate spectrum for the event
    spectrum_sum = np.sum(D, axis=1)
    dominant_bin = np.argmax(spectrum_sum)
    dominant_freq = float(frequencies[dominant_bin])

    return {
        "spectral_centroid_mean": round(mean_centroid, 2),
        "dominant_frequency": round(dominant_freq, 2),
        "duration_samples": len(y_segment),
    }


def process_audio_to_frequency_json(audio_path, output_path="event_frequencies.json"):
    print(f"Loading audio: {audio_path}")

    """
    Processes an audio file to extract frequency data for each detected event and saves it to JSON.

    :param audio_path: Path to the audio file.
    :type audio_path: str
    :param output_path: Path for the output JSON file, defaults to "event_frequencies.json".
    :type output_path: str, optional
    :return: List of event data dictionaries.
    :rtype: list
    """
    # 1. Load Audio
    # Using your existing loader to ensure consistency
    y, sr = audio_loader.load_audio(audio_path)

    # 2. Detect Onsets (Events)
    print("Detecting events...")
    # Adjust arguments if your detector requires them (e.g. hop_length)
    onsets = onset_detector.detect_onsets(y, sr)

    event_data_list = []

    print(f"Found {len(onsets)} events. Extracting frequencies...")

    # 3. Iterate through events and extract frequency data
    for i, onset_sample in enumerate(onsets):
        # Define a window for the event (e.g., 200ms or until next onset)
        start_sample = onset_sample

        # Determine end sample (either next onset or fixed window)
        if i < len(onsets) - 1:
            end_sample = onsets[i + 1]
        else:
            # For the last event, take 200ms or end of file
            end_sample = min(len(y), start_sample + int(0.2 * sr))

        # Slice the audio
        y_event = y[start_sample:end_sample]

        # Skip extremely short glitches
        if len(y_event) < 512:
            continue

        # Extract frequencies
        freq_metrics = extract_frequency_data(y_event, sr)

        # Build the event object
        event_obj = {
            "event_id": i,
            "start_time": round(float(start_sample) / sr, 3),
            "frequencies": freq_metrics,
        }
        event_data_list.append(event_obj)

    # 4. Save to JSON
    print(f"Saving data for {len(event_data_list)} events to {output_path}")
    with open(output_path, "w") as f:
        json.dump(event_data_list, f, indent=4)

    return event_data_list

    # Example usage
    # You can point this to a test file in your directory
    # TEST_AUDIO = "test_audio/test.wav"

    # if Path(TEST_AUDIO).exists():
    #  process_audio_to_frequency_json(TEST_AUDIO)
    # else:
    #   print(f"Please provide a valid audio path. (File not found: {TEST_AUDIO})")


if __name__ == "__main__":
    import argparse

    # Setup Command Line Arguments
    parser = argparse.ArgumentParser(
        description="Extract frequency data from drum audio events to JSON."
    )

    parser.add_argument("input_audio", help="Path to the audio file (.wav, .mp3, etc.)")

    parser.add_argument(
        "-o", "--output", help="Path for the output JSON file (optional)", default=None
    )

    args = parser.parse_args()

    # Run the processor
    process_audio_to_frequency_json(args.input_audio, args.output)
