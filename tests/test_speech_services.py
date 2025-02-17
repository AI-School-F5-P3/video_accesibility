# tests/services/test_speech_service.py
from typing import Optional
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from src.services.speech_service import SpeechService
from src.core.audio_processor import VoiceSynthesizer

@pytest.fixture
def speech_service():
    """Create a SpeechService instance for testing."""
    return SpeechService()

@pytest.fixture
def mock_directories(tmp_path):
    """Create mock directories for testing."""
    dirs = {
        'audio': tmp_path / 'audio',
        'temp': tmp_path / 'temp'
    }
    for dir_path in dirs.values():
        dir_path.mkdir(parents=True)
    return dirs

def test_speech_service_initialization():
    """Test that SpeechService initializes correctly."""
    with patch('src.services.speech_service.setup_directories') as mock_setup:
        mock_setup.return_value = {'audio': Path('/mock/audio')}
        service = SpeechService()
        assert service.directories['audio'] == Path('/mock/audio')
        assert isinstance(service.synthesizer, VoiceSynthesizer)

@pytest.mark.parametrize('description,filename,expected_success', [
    ('Valid description', 'test_file', True),
    ('', 'empty_description', False),
])
def test_generate_description_audio(speech_service, mock_directories, description, filename, expected_success):
    """Test description audio generation with various inputs."""
    with patch.dict(speech_service.directories, mock_directories):
        with patch.object(speech_service.synthesizer, 'generate_audio') as mock_generate:
            expected_path = mock_directories['audio'] / f"{filename}.wav"
            if expected_success:
                mock_generate.return_value = expected_path
            else:
                mock_generate.return_value = None
                
            result = speech_service.generate_description_audio(description, filename)
            
            if expected_success:
                assert result == expected_path
                mock_generate.assert_called_once_with(description, expected_path)
            else:
                assert result is None
                mock_generate.assert_called_once_with(description, expected_path)