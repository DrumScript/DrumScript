"""
Shared pytest fixtures for DrumScript tests.

This file is auto-discovered by pytest. Any fixture defined here is available
to every test in the ``tests/`` tree without explicit import. Keep
fixtures here that are reusable across multiple test files.

Conventions used in this project
--------------------------------
- Synthesised audio (sine waves, click tracks, etc.) is preferred over
  checked-in WAV files. It keeps the repo small and the fixtures
  reproducible.
- All audio fixtures return ``(audio_data, sample_rate)`` tuples to match
  the conventions used by ``librosa.load`` and ``soundfile.read``.
- Fixtures that write files use the built-in ``tmp_path`` fixture so cleanup
  is automatic and tests cannot pollute each other.
"""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

# Path to checked-in audio fixtures, if/when you add any.
# Currently empty — we synthesise everything in-process.
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "audio"


# =============================================================================
# Synthesised audio fixtures
# =============================================================================


@pytest.fixture
def sine_wave():
    """
    A 1-second 440 Hz sine wave at 22050 Hz, mono float32.

    Useful for: testing audio loading round-trips, normalisation, anything
    where you need a predictable non-trivial waveform.
    """
    sr = 22050
    duration_s = 1.0
    freq = 440
    t = np.linspace(0, duration_s, int(sr * duration_s), endpoint=False)
    audio = (np.sin(2 * np.pi * freq * t) * 0.5).astype(np.float32)
    return audio, sr


@pytest.fixture
def silent_audio():
    """5 seconds of silence at 22050 Hz."""
    sr = 22050
    return np.zeros(sr * 5, dtype=np.float32), sr


@pytest.fixture
def click_track_120bpm():
    """
    A 4-second click track at exactly 120 BPM (i.e. 8 clicks).

    Useful for: testing tempo detection and onset detection. Each click is a
    50 ms burst of full-amplitude noise, which gives librosa a clear onset
    to lock onto.
    """
    sr = 22050
    bpm = 120
    duration_s = 4.0

    samples = np.zeros(int(sr * duration_s), dtype=np.float32)
    interval_samples = int(sr * 60 / bpm)  # samples between clicks
    click_len = int(sr * 0.05)  # 50 ms click

    # Use a fixed seed so the click "noise" is identical run to run.
    rng = np.random.default_rng(seed=42)

    for i in range(0, len(samples), interval_samples):
        end = min(i + click_len, len(samples))
        # White-noise burst gives a sharper onset than a square tone.
        samples[i:end] = rng.uniform(-0.8, 0.8, end - i)

    return samples, sr


@pytest.fixture
def stereo_constant_audio():
    """
    1 second of constant-amplitude stereo audio at 22050 Hz.

    Channel 0 is at 0.1 amplitude, channel 1 is at 0.2 amplitude.
    Useful for: verifying mixing logic preserves channel structure and that
    stems are summed correctly (not just one stem retained).
    """
    sr = 22050
    n_samples = sr  # 1 second
    audio = np.zeros((n_samples, 2), dtype=np.float32)
    audio[:, 0] = 0.1
    audio[:, 1] = 0.2
    return audio, sr


# =============================================================================
# File-based fixtures (write to tmp_path)
# =============================================================================


@pytest.fixture
def small_wav_file(tmp_path, sine_wave):
    """
    Write the ``sine_wave`` fixture to a temporary WAV file and return the path.

    Use this when a test needs an *actual file on disk* rather than a numpy
    array (e.g. testing ``load_audio`` or anything that takes a file path).
    """
    audio, sr = sine_wave
    path = tmp_path / "test.wav"
    sf.write(str(path), audio, sr)
    return path


@pytest.fixture
def stem_files(tmp_path):
    """
    Create three small WAV files representing 'drum-like' stems on disk.

    Returns a dict mapping stem name to ``Path``. Each stem is a 1-second
    stereo file with a different, distinct constant amplitude so that mixing
    logic is verifiable: if all stems contribute, the mixed mean amplitude
    will be the sum of the three; if only one stem is used, you'll see only
    that one's amplitude.

    Stem amplitudes:
        drums:  0.1
        bass:   0.2
        vocals: 0.3
    Sum (if mixed correctly): 0.6
    """
    sr = 22050
    n_samples = sr  # 1 second
    n_channels = 2

    stems = {
        "drums": 0.1,
        "bass": 0.2,
        "vocals": 0.3,
    }

    paths = {}
    for name, amplitude in stems.items():
        audio = np.full((n_samples, n_channels), amplitude, dtype=np.float32)
        path = tmp_path / f"{name}.wav"
        sf.write(str(path), audio, sr)
        paths[name] = path

    return paths
