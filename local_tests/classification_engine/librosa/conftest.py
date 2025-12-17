# local_tests/classification_engine/librosa/conftest.py
import pytest

def pytest_addoption(parser):
    parser.addoption("--audio", action="store", help="Filename of the audio in .test_audio/")
    parser.addoption("--drum", action="store", help="Target drum type to test (e.g. kick, snare, open_hat)")

@pytest.fixture
def audio_file(request):
    return request.config.getoption("--audio")

@pytest.fixture
def drum_type(request):
    return request.config.getoption("--drum")