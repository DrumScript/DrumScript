import librosa
import numpy as np
import matplotlib.pyplot as plt
import argparse
# from datetime import datetime

# Uncomment to use for logging/tests

# print("\n# ------------------------------------------------------------------------------------")
# datetimestamp = datetime.now()
# print(f'\ndatetimestamp: {datetimestamp}')


# from drumscript.utils.config import SAMPLE_RATE, HOP_LENGTH, N_FFT

# def measure_kick_frequency(audio_file_path):
    # Load with the PROJECT'S standardized sample rate, not the file's native rate
  #  y, sr = librosa.load(audio_file_path, sr=SAMPLE_RATE) 
    
    # Use the project's FFT settings
   # S = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)

    # """
    # Example code for calculating the frequency of a drum part
    # To measure the frequency of a kick drum using Librosa, you can apply a Short-Time Fourier Transform (STFT) to convert the audio into the time-frequency domain and then identify the dominant frequency within the typical kick drum range (around 50-100 Hz). 
    # This script uses librosa and numpy to find the `fundamental` frequency of a kick drum sample. This analysis can then be used to tweak/fine-tune the classification model used in DrumScript.
    # It assumes that a specific isolated audio snippet of the part being tested is supplied as user input, ie. you need to give it an audio file to analyse.
    # Extracts key frequency metrics for a single audio event. 

    #:param audio_file_path: Path to audio file.
    #:type audio_file_path: str
    #:returns event_data_list: list of parameters
    #:rtype: list[float]

    # """

def measure_kick_frequency(audio_file_path):

    """ 
    # Example code for calculating the frequency of a drum part
        # To measure the frequency of a kick drum using Librosa, you can apply a Short-Time Fourier Transform (STFT) to convert the audio into the time-frequency domain and then identify the dominant frequency within the typical kick drum range (around 50-100 Hz). 
        # This script uses librosa and numpy to find the `fundamental` frequency of a kick drum sample. This analysis can then be used to tweak/fine-tune the classification model used in DrumScript.
        # It assumes that a specific isolated audio snippet of the part being tested is supplied as user input, ie. you need to give it an audio file to analyse.
        # Extracts key frequency metrics for a single audio event. 

        #:param audio_file_path: Path to audio file.
        #:type audio_file_path: str
        #:returns event_data_list: list of parameters
        #:rtype: list[float]
    """
    # 1. Load the audio file
    y, sr = librosa.load(audio_file_path, sr=None) # Use native sample rate
    
    # Optional: Isolate a single kick drum hit for analysis if the file has a full beat

    # 2. Compute the Short-Time Fourier Transform (STFT)
    # n_fft=2048 is standard, good for general music. For low frequencies, a larger n_fft might give better frequency resolution.
    n_fft = 2048 
    hop_length = 512 # Default hop_length
    S = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
    S_db = librosa.amplitude_to_db(abs(S), ref=np.max) # Convert amplitude to decibels

    # 3. Get the frequency bins
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    # 4. Find the frame corresponding to the kick drum's peak energy (you might need to manually adjust the time index)
    # This example assumes the kick drum has a strong onset near the beginning or you know its time
    # For a simple single sample file, we can just look at the maximum energy frame
    max_energy_frame = np.argmax(np.max(S_db, axis=0))
    kick_spectrum = S_db[:, max_energy_frame]
    
    # To analyze the *entire* track's general kick frequency, you might average across all relevant low-freq peaks, 
    # but the single frame method finds the prominent frequency at that specific moment.

    # 5. Find the frequency with the maximum magnitude in the kick drum range (e.g., 50-200 Hz)
    min_freq = 50
    max_freq = 200
    
    # Filter frequencies to the relevant range for kick drums
    freq_mask = (freqs >= min_freq) & (freqs <= max_freq)
    
    if np.any(freq_mask):
        masked_spectrum = kick_spectrum[freq_mask]
        masked_freqs = freqs[freq_mask]
        
        # Find the index of the maximum magnitude in the masked spectrum
        peak_index_masked = np.argmax(masked_spectrum)
        peak_frequency = masked_freqs[peak_index_masked]
        
        print(f"Estimated peak kick drum frequency: {peak_frequency:.2f} Hz")
        
        # 6. Optional: Visualization
        # plt.figure(figsize=(10, 6))
        # librosa.display.specshow(S_db, sr=sr, hop_length=hop_length, x_axis='time', y_axis='log')
        # plt.title('Spectrogram of the audio file')
        # plt.vlines(librosa.frames_to_time(max_energy_frame, sr=sr, hop_length=hop_length), 0, sr/2, color='white', linestyle='--', label='Analyzed Frame')
        # plt.legend()
        # plt.show()
        
    else:
        print("Could not find a prominent frequency in the 50-200 Hz range.")

# Usage example (replace 'your_kick_drum_sample.wav' with your file path):
# measure_kick_frequency('your_kick_drum_sample.wav')

if __name__ == "__main__":
    # This allows you to run it from the command line with an argument
    import sys
    if len(sys.argv) < 2:
        print("Usage: uv run drumscript/utils/measure_kick_frequency.py <path_to_audio_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    measure_kick_frequency(input_file)