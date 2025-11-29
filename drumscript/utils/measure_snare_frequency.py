# drumscript/utils/measure_snare_frequency.py

import librosa
import numpy as np
import matplotlib.pyplot as plt
import librosa.display

"""
This script measures the frequency of a snare drum using librosa, and applies the Short-Time Fourier Transform (STFT) to analyze its frequency content over time. The primary frequencies will appear as peaks in the resulting spectrogram (optional).  The code loads an audio file, separates the percussive components (useful for isolating the snare in a full mix), computes the STFT, and finds the dominant frequency. You need to have librosa and numpy installed.
"""


def measure_snare_frequency(audio_file_path):
    # 1. Load the audio file
    y, sr = librosa.load(audio_file_path, sr=None) # Use original sampling rate

    # 2. Separate harmonic and percussive components (optional, but helps isolate the snare)
    y_harmonic, y_percussive = librosa.effects.hpss(y)

    # Use the percussive signal for frequency analysis
    y_snare = y_percussive

    # 3. Compute the Short-Time Fourier Transform (STFT)
    # n_fft determines the frequency resolution (higher = finer freq detail, lower = finer time detail)
    n_fft = 2048
    hop_length = 512
    S = librosa.stft(y_snare, n_fft=n_fft, hop_length=hop_length)
    S_db = librosa.amplitude_to_db(abs(S), ref=np.max)

    # 4. Find the dominant frequency (e.g., using spectral centroid or peak analysis)
    # Spectral centroid gives the "center of mass" of the frequencies
    cent = librosa.feature.spectral_centroid(y=y_snare, sr=sr, S=abs(S))
    
    # Calculate the mean spectral centroid as an average frequency estimate
    # The snare drum is an impulse, so its frequency content is broad. 
    # A single "frequency" might not be representative, but a range is.
    mean_frequency = np.mean(cent)
    print(f"Mean spectral centroid (frequency estimate): {mean_frequency:.2f} Hz")

    # [OPTIONAL]
    # 5. Visualize the Spectrogram (to see frequency distribution)
    # plt.figure(figsize=(10, 4))
    # librosa.display.specshow(S_db, sr=sr, hop_length=hop_length, x_axis='time', y_axis='hz')
    # plt.colorbar(format='%+2.0f dB')
    # plt.title('Snare Drum Spectrogram (Frequency vs. Time)')
    #.plt.show()

    # 6. Analyze the frequency bins for specific peaks
    # The actual frequency values corresponding to the STFT bins
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
    
    # Find the frequency bin with the maximum amplitude across time (simple peak finding)
    max_magnitude = np.max(abs(S), axis=1)
    peak_frequency_index = np.argmax(max_magnitude)
    peak_frequency = freqs[peak_frequency_index]
    
    print(f"Overall peak frequency: {peak_frequency:.2f} Hz")

    return mean_frequency, peak_frequency

# Example usage:
# Replace 'path/to/your/snare_drum_sample.wav' with your actual file path
# If you don't have a file, you can try using a built-in librosa example (though not a specific snare hit)
# For a real snare, ensure a clear, isolated audio sample works best.

# Example with a generic file (you will need your own snare sample for meaningful results):
# mean_freq, peak_freq = measure_snare_frequency('path/to/your/snare_drum_sample.wav') 
