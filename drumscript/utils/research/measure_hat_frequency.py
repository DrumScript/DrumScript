# drumscript/utils/research/measure_hat_frequency.py

# To measure the frequency characteristics of open and closed hi-hat drums using librosa,
# you can load the audio, perform a Short-Time Fourier Transform (STFT) to analyze the frequency content over time
# and then examine the spectral features.

"""
Utility script to measure the fundamental frequency of a drum sample.
"""

import librosa
import librosa.display
import numpy as np

# from drumscript.utils.config import SAMPLE_RATE, HOP_LENGTH, N_FFT


def measure_hat_frequency(audio_file_path):
    """
    # To measure the frequency characteristics of open and closed hi-hat drums using librosa, you can load the audio, perform a
    # Short-Time Fourier Transform (STFT) to analyze the frequency content over time, and then examine the spectral features.

    Extracts key frequency metrics for a single audio event.

    :param audio_file_path: Path to audio file.
    :type audio_file_path: str
    :returns event_data_list: list of parameters
    :rtype: list[float]
    """

    # Load with the PROJECT'S standardized sample rate, not the file's native rate


#  y, sr = librosa.load(audio_file_path, sr=SAMPLE_RATE)

# Use the project's FFT settings
# S = librosa.stft(y, n_fft=N_FFT, hop_length=HOP_LENGTH)

# Load the audio file. 'y' is the time series, 'sr' is the sampling rate.
# Set a specific sample rate if needed, e.g., sr=22050

y, sr = librosa.load("your_hi_hat_track.wav", sr=None)

# 2. Perform Time-Frequency Analysis (STFT)
# Use librosa.stft to convert the time-domain signal into a frequency-domain representation (spectrogram).

D = librosa.stft(y)

# Convert the amplitude spectrogram to dB-scaled spectrogram
S_dB = librosa.amplitude_to_db(np.abs(D), ref=np.max)


# 3. [OPTIONAL] Visualise the Spectrogram
# Visualising the spectrogram helps you identify where open and closed hi-hat hits occur in time and frequency.
# plt.figure(figsize=(10, 5))
# librosa.display.specshow(S_dB, sr=sr, x_axis='time', y_axis='hz') # Use 'hz' to view actual frequencies
# plt.colorbar(format='%+2.0f dB')
# plt.title('Spectrogram of Hi-Hats')
# plt.show()

# 4. Analyse and Differentiate Frequencies
## Hi-hats generally have dominant frequencies between 300 Hz and 3000 Hz, with energy extending up to 17 kHz for crispness.
## Closed Hi-hats: Tend to be a tight, snappy sound (a "chick" or "tssk") with a shorter decay, concentrated in the mid-to-high frequency range.
## Open Hi-hats: Have a looser, more sibilant "shhhhhh" or "clash" sound with a longer sustain, which involves a broader spectrum of frequencies,
# particularly the presence range around 2-3 kHz and higher "air" frequencies (5kHz-17kHz).
## You can extract specific time segments corresponding to individual hits (perhaps by using librosa.onset.onset_detect first)
#  and analyze their average spectral features.

# Example of extracting spectral features for a time segment
# Assuming a closed hi-hat is at the start (e.g., first 0.5s) and an open hi-hat later
# This requires knowing the time of hits, potentially via manual inspection or onset detection

# To get the actual frequencies associated with the spectrogram bins:
freqs = librosa.fft_frequencies(sr=sr, n_fft=2048)  # Default n_fft is 2048

# Extract the frequency magnitudes for a specific frame (e.g., frame 10)
frame_index_closed = 10
magnitudes_closed = np.abs(D[:, frame_index_closed])

# You can then analyse the 'magnitudes_closed' array to find the dominant frequencies (peaks)
# For comparison, analyse an 'open' hi-hat frame similarly.

# 5. Use Spectral Features for Differentiation
# For a more automated approach, use features that capture the spectral characteristics, such as:
## Spectral Centroid: Measures the "average" frequency, weighted by magnitude.
# Open hi-hats might have a slightly higher or more varied spectral centroid due to the extra high-frequency "sizzle."
## Spectral Flatness: Quantifies how noise-like the sound is. Open hi-hats typically sound more "noisy" and may have a higher spectral flatness value
# compared to the tighter, more tone-like (though still complex) closed hi-hat sound.
# By comparing these features between segments of closed and open hi-hats, you can observe the differences in their frequency distribution.


if __name__ == "__main__":
    import sys
    # --------------------------------------------------------------------------uncomment during testing
    # from datetime import datetime
    # print("\n# ------------------------------------------------------------------------------------")
    # datetimestamp = datetime.now()
    # print(f'\ndate/time: {datetimestamp}')
    # --------------------------------------------------------------------------------------------------

    if len(sys.argv) < 2:
        print("Usage: uv run drumscript/utils/measure_hat_frequency.py <path_to_audio_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    measure_hat_frequency(input_file)
