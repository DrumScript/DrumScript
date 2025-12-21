# local_tests/classification_engine/librosa/test_classification_tool.py
# IMPORTANT: This script assumes that the test_audio to be passed in argument is placed in ./test_audio
import pytest
import librosa
import numpy as np
import os
import sys

# ===============================================
# 1. THE CLASSIFICATION LOGIC (See .csv in folder)
# ===============================================
class DrumClassifier:
    
    @staticmethod
    def kick(y, sr):
        """
        1. Kick Rule:
           - (Mean) Centroid 170-3254 Hz expected for kick drums (ie Highly variable)
           - (Mean) RMS > 0.05 (Significant volume)
           - Dominant Low Freq in 50-170 Hz (Physical kick fundamental)
        """
        # 1. Timbre (Centroid)
        centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
        centroid_val = np.mean(centroids)
        print(f"   [DEBUG] Mean Centroid:     {centroid_val:.2f} Hz")

        # 2. Loudness (RMS)
        rms = librosa.feature.rms(y=y)
        rms_val = np.mean(rms)
        print(f"   [DEBUG] Mean RMS:          {rms_val:.4f}")

        # 3. Fundamental Frequency (Using new STFT masking logic)
        # We look for the peak freq between 50-200Hz
        detected_freq = DrumClassifier._measure_dominant_freq(y, sr, min_freq=50, max_freq=200)
        print(f"   [DEBUG] Dominant Low Freq: {detected_freq:.2f} Hz")

        # 4. Final Classification Logic
        # A kick must be dark, loud, and have a fundamental between 50-100Hz
        is_valid_pitch = (detected_freq >= 50) and (detected_freq <= 170)
        
        return (centroid_val < 4000) and (rms_val > 0.05) and is_valid_pitch # Set centroid_val upper bound VERY HIGH so that rule (for now anyway) catches almost all possible kick events, ie render the centroid defunct (for now)

    @staticmethod
    def snare(y, sr):
        """2. Snare: High Flatness"""
        flatness = librosa.feature.spectral_flatness(y=y)
        val = np.mean(flatness)
        print(f"   [DEBUG] Spectral Flatness: {val:.4f}")
        return val > 0.05  # Adjust threshold based on your specific samples

    @staticmethod
    def low_tom(y, sr):
        """3. Low Tom: Pitch ~60-100 Hz"""
        return DrumClassifier._check_pitch(y, sr, 60, 100)

    @staticmethod
    def mid_tom(y, sr):
        """4. Mid Tom: Pitch ~100-150 Hz"""
        return DrumClassifier._check_pitch(y, sr, 100, 150)

    @staticmethod
    def high_tom(y, sr):
        """5. High Tom: Pitch ~150-250 Hz"""
        return DrumClassifier._check_pitch(y, sr, 150, 250)

    @staticmethod
    def open_hihat(y, sr):
        """6. Open HH: Decay > 200ms"""
        ms = DrumClassifier._get_decay(y, sr)
        print(f"   [DEBUG] Decay Time: {ms:.2f} ms")
        return ms > 200

    @staticmethod
    def closed_hihat(y, sr):
        """7. Closed HH: Decay < 50ms"""
        ms = DrumClassifier._get_decay(y, sr)
        print(f"   [DEBUG] Decay Time: {ms:.2f} ms")
        return ms < 50

    @staticmethod
    def ride_washy(y, sr):
        """8. Ride Washy: Bandwidth > 2500"""
        bw = librosa.feature.spectral_bandwidth(y=y, sr=sr)
        val = np.mean(bw)
        print(f"   [DEBUG] Bandwidth: {val:.2f}")
        return val > 2500

    @staticmethod
    def ride_sharp(y, sr):
        """9. Ride Sharp: High Tonal Content (Chroma)"""
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)
        val = np.mean(chroma)
        print(f"   [DEBUG] Chroma Mean: {val:.4f}")
        return val > 0.35

    @staticmethod
    def crash_washy(y, sr):
        """10. Crash Washy: High Energy > 10kHz"""
        rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr, roll_percent=0.95)
        val = np.mean(rolloff)
        print(f"   [DEBUG] Rolloff (0.95): {val:.2f} Hz")
        return val > 10000

    @staticmethod
    def crash_sharp(y, sr):
        """11. Crash Sharp: High Attack Transient"""
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        val = np.max(onset_env)
        print(f"   [DEBUG] Max Onset Strength: {val:.2f}")
        return val > 5.0

    @staticmethod
    def hihat_foot(y, sr):
        """12. HH Foot: Low RMS"""
        rms = librosa.feature.rms(y=y)
        val = np.mean(rms)
        print(f"   [DEBUG] Mean RMS: {val:.4f}")
        return val < 0.05

    @staticmethod
    def double_bass(y, sr):
        """13. Double Bass: Fast Intervals (<150ms)"""
        onsets = librosa.onset.onset_detect(y=y, sr=sr, units='time')
        if len(onsets) < 2: 
            print("   [DEBUG] Not enough onsets detected.")
            return False
        avg_ioi = np.mean(np.diff(onsets))
        print(f"   [DEBUG] Avg Interval: {avg_ioi:.4f} s")
        return avg_ioi < 0.150

    # ===============================================
    # HELPERS
    # ===============================================

    @staticmethod
    def _measure_dominant_freq(y, sr, min_freq=50, max_freq=200):
        """
        Calculates the dominant frequency within a specific range using STFT masking.
        Adapted from contributor utility code.
        """
        # 1. Compute STFT
        n_fft = 2048 
        hop_length = 512 
        S = librosa.stft(y, n_fft=n_fft, hop_length=hop_length)
        S_db = librosa.amplitude_to_db(np.abs(S), ref=np.max)

        # 2. Find the frame with the maximum energy (the "hit")
        # Summing across freq bins gives energy per frame
        # We assume the loudest frame is the drum hit
        max_energy_frame = np.argmax(np.max(S_db, axis=0))
        
        # 3. Get the spectrum for that specific frame
        kick_spectrum = S_db[:, max_energy_frame]
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

        # 4. Filter for relevant frequencies
        freq_mask = (freqs >= min_freq) & (freqs <= max_freq)
        
        if np.any(freq_mask):
            masked_spectrum = kick_spectrum[freq_mask]
            masked_freqs = freqs[freq_mask]
            
            # 5. Find peak within that range
            peak_index_masked = np.argmax(masked_spectrum)
            peak_frequency = masked_freqs[peak_index_masked]
            return peak_frequency
            
        return 0.0 # Return 0 if no frequency found in range

    @staticmethod
    def _check_pitch(y, sr, low, high):
        pitches, magnitudes = librosa.piptrack(y=y, sr=sr)
        # simplistic dominant pitch estimation
        mag_mean = np.mean(magnitudes, axis=1)
        max_idx = np.argmax(mag_mean)
        freqs = librosa.fft_frequencies(sr=sr)
        detected = freqs[max_idx]
        print(f"   [DEBUG] Dominant Freq: {detected:.2f} Hz")
        return low <= detected <= high

    @staticmethod
    def _get_decay(y, sr):
        onset_env = librosa.onset.onset_strength(y=y, sr=sr)
        times = librosa.times_like(onset_env, sr=sr)
        peak_idx = np.argmax(onset_env)
        # time to drop to 10%
        thresh = 0.1 * onset_env[peak_idx]
        post_peak = onset_env[peak_idx:]
        decay_pts = np.where(post_peak < thresh)[0]
        if len(decay_pts) > 0:
            return (times[peak_idx + decay_pts[0]] - times[peak_idx]) * 1000
        return 1000 # Max out if no decay found

# ==========================================
# 2. THE DYNAMIC TEST RUNNER
# ==========================================

def test_dynamic_drum_check(audio_file, drum_type):
    """
    Reads command line args, loads audio, runs specific check.
    """
    # 1. Validation
    if not audio_file or not drum_type:
        pytest.skip("Skipping: Provide --audio and --drum to run this tool.")

    # 2. Path Resolution (3 directories up from this script location)
    # logic: local_tests/classification_engine/librosa -> ../../../ -> test_audio/
    base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../test_audio")) # could amend this in future so it, instead, goes directly to root and then the path can be provided as user input arg
    file_path = os.path.join(base_path, audio_file)

    if not os.path.exists(file_path):
        pytest.fail(f"Audio file not found at: {file_path}")

    # 3. Load Audio
    print(f"\n\n   >>> LOADING: {audio_file}")
    try:
        y, sr = librosa.load(file_path, sr=None)
    except Exception as e:
        pytest.fail(f"Librosa could not load file: {e}")

    # 4. Map 'drum_type' string to function
    # Normalise input (e.g. "Low Tom" -> "low_tom")
    method_name = drum_type.lower().replace(" ", "_")
    
    if not hasattr(DrumClassifier, method_name):
        valid_methods = [m for m in dir(DrumClassifier) if not m.startswith("_")]
        pytest.fail(f"Unknown drum type '{drum_type}'. Available: {valid_methods}")

    classifier_func = getattr(DrumClassifier, method_name)

    # 5. Execute & Print
    print(f"   >>> TESTING FOR: {drum_type.upper()}")
    print("   ----------------------------------------")
    
    is_match = classifier_func(y, sr)
    
    print("   ----------------------------------------")
    if is_match:
        print(f"   >>> RESULT: THIS IS A {drum_type.upper()}")
    else:
        print(f"   >>> RESULT: NOT A {drum_type.upper()}")
    print("   ----------------------------------------\n")