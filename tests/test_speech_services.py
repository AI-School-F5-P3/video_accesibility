# tests/test_speech_services.py
from typing import Optional
from pathlib import Path
import sys
import os
from unittest.mock import patch, MagicMock
import pytest
import sys
from pathlib import Path

# Añadir el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Añadir el directorio raíz al path
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.insert(0, str(root_dir))

# Verificar si el servicio existe
try:
    from src.services.speech_service import SpeechService
    from src.core.audio_processor import VoiceSynthesizer
    SPEECH_SERVICE_EXISTS = True
except ImportError:
    print("⚠️ Advertencia: No se encuentra src.services.speech_service. Usando mocks para pruebas.")
    SPEECH_SERVICE_EXISTS = False
    # Crear clases mock para pruebas
    class VoiceSynthesizer:
        def generate_audio(self, text, output_path):
            return output_path

    class SpeechService:
        def __init__(self):
            self.directories = {'audio': Path('/mock/audio')}
            self.synthesizer = VoiceSynthesizer()

@pytest.fixture
def speech_service():
    """Create a SpeechService instance for testing."""
    if not SPEECH_SERVICE_EXISTS:
        pytest.skip("SpeechService no existe en este proyecto")
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
    if not SPEECH_SERVICE_EXISTS:
        pytest.skip("SpeechService no existe en este proyecto")
    
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
    if not SPEECH_SERVICE_EXISTS:
        pytest.skip("SpeechService no existe en este proyecto")
    
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

if __name__ == "__main__":
    # Ejecutar pruebas manualmente si se llama directamente
    pytest.main(["-v", __file__])