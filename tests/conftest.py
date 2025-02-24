# tests/conftest.py
import pytest
import numpy as np
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from typing import Dict, Any
from vertexai.generative_models import GenerativeModel
from unittest.mock import Mock, MagicMock, patch
from tests.mocks.youtube_mock import YouTubeAPIMock
from app.config import Settings
from app.pipeline.video_pipeline import VideoPipeline
from app.services.ai import VertexAIService
from app.models.schemas import VideoConfig

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root():
    """
    Provides the project root directory for consistent file access across tests.
    This is important for locating test data, credentials, and configuration files.
    """
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """
    Provides access to the test data directory.
    Creates necessary test data directories if they don't exist.
    """
    data_dir = project_root / "tests" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@pytest.fixture
def mock_gemini_response():
    """
    Simulates responses from Google AI Studio's Gemini model.
    This fixture provides standardized mock responses for testing
    video analysis and scene understanding capabilities.
    """
    return {
        "visual_analysis": {
            "description": "A person sits at a desk working on a laptop",
            "scene_elements": ["person", "desk", "laptop"],
            "accessibility_context": {
                "lighting": "well-lit indoor scene",
                "movement": "minimal movement",
                "spatial_info": "centered in frame",
                "important_elements": ["facial expressions", "hand gestures"]
            }
        },
        "confidence_scores": {
            "scene_understanding": 0.95,
            "object_detection": 0.98,
            "action_recognition": 0.92
        }
    }

@pytest.fixture
def mock_audio_segment():
    """
    Creates a synthesized audio segment for testing audio processing.
    Generates a simple waveform that simulates speech patterns.
    """
    sample_rate = 44100  # Standard audio sample rate
    duration = 3.0       # 3 seconds of audio
    t = np.linspace(0, duration, int(sample_rate * duration))
    
    # Create a more complex waveform simulating speech
    frequency = 440  # Base frequency for voice simulation
    amplitude = 0.5
    waveform = amplitude * np.sin(2 * np.pi * frequency * t)
    
    # Add some variation to make it more speech-like
    waveform += 0.3 * np.sin(2 * np.pi * (frequency * 1.5) * t)
    return waveform

@pytest.fixture
def une_standards():
    """Fixture para estándares UNE."""
    return {
        'UNE153010': {
            'max_chars_per_line': 37,
            'max_lines_per_subtitle': 2,
            'min_duration': 1,
            'max_duration': 4
        },
        'UNE153020': {
            'max_words_per_description': 120,
            'min_scene_duration': 4,
            'max_description_length': 500,
            'silence_gap': 2,
            'words_per_minute': 180
        }
    }

@pytest.fixture
def mock_video_frame():
    """
    Creates a test video frame for image analysis testing.
    Generates a frame with basic visual elements for testing
    scene understanding capabilities.
    """
    height, width = 480, 640
    channels = 3
    frame = np.zeros((height, width, channels), dtype=np.uint8)
    
    # Add some basic shapes to simulate content
    frame[100:200, 200:400] = 255  # White rectangle
    return frame

@pytest.fixture
def mock_transcript_data():
    """
    Provides mock transcript data for testing speech processing.
    Includes timing information and speaker identification
    for comprehensive subtitle testing.
    """
    return {
        "transcript": "Welcome to this accessibility presentation",
        "confidence": 0.95,
        "words": [
            {"word": "Welcome", "start": 0.0, "end": 0.5},
            {"word": "to", "start": 0.6, "end": 0.8},
            {"word": "this", "start": 0.9, "end": 1.1},
            {"word": "accessibility", "start": 1.2, "end": 2.0},
            {"word": "presentation", "start": 2.1, "end": 2.8}
        ],
        "speakers": [
            {"id": "speaker_1", "confidence": 0.92}
        ]
    }

@pytest.fixture(autouse=True)
def setup_environment(project_root):
    """
    Automatically sets up the testing environment before each test.
    Ensures all necessary environment variables and configurations
    are properly loaded.
    """
    load_dotenv(project_root / '.env')
    
    # Verify essential environment variables
    required_vars = [
        'GOOGLE_APPLICATION_CREDENTIALS',
        'GOOGLE_CLOUD_PROJECT',
        'VERTEX_LOCATION'
    ]
    
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        pytest.skip(f"Missing required environment variables: {', '.join(missing_vars)}")

@pytest.fixture(autouse=True)
def cleanup_test_files(test_data_dir):
    """Limpia archivos temporales después de cada test"""
    yield
    # Limpiar archivos temporales
    for temp_file in test_data_dir.glob("*.tmp"):
        temp_file.unlink()
    for temp_dir in ["downloads", "output"]:
        temp_path = test_data_dir / temp_dir
        if temp_path.exists():
            for file in temp_path.iterdir():
                file.unlink()
            temp_path.rmdir()

@pytest.fixture
def mock_ai_model():
    """Provide mock AI model for testing."""
    class MockResponse:
        text = "Sample transcription text"
        confidence = 0.95
        
    class MockModel:
        def generate_content(self, *args, **kwargs):
            return MockResponse()
            
    return MockModel()

@pytest.fixture
def mock_video_file(tmp_path):
    """Crea un archivo de video mock para testing."""
    video_path = tmp_path / "test_video.mp4"
    video_path.write_bytes(b'mock video content')
    return str(video_path)

@pytest.fixture
def mock_processor_config():
    return {
        "model_settings": {
            "temperature": 0.7,
            "max_output_tokens": 1024
        }
    }

@pytest.fixture
def youtube_api():
    """Proporciona un mock de YouTube API para tests"""
    return YouTubeAPIMock("test_api_key")

@pytest.fixture
def mock_video_pipeline(monkeypatch):
    """Mock del pipeline completo"""
    monkeypatch.setenv('YOUTUBE_API_KEY', 'test_api_key')
    monkeypatch.setenv('GOOGLE_APPLICATION_CREDENTIALS', './tests/resources/mock_credentials.json')

@pytest.fixture
def pipeline(monkeypatch):
    """Proporciona una instancia de VideoPipeline con mocks"""
    monkeypatch.setenv('YOUTUBE_API_KEY', 'test_api_key')
    config = Settings().get_config()
    return VideoPipeline(config)

@pytest.fixture
def settings():
    """Fixture para configuración global"""
    return Settings()

@pytest.fixture
def video_pipeline(settings):
    """Fixture para el pipeline de video"""
    return VideoPipeline(settings)

@pytest.fixture
def test_video_path():
    """Fixture para path de video de prueba"""
    return Path(__file__).parent / "fixtures" / "test_video.mp4"

@pytest.fixture(scope="session")
def video_duration():
    """Duración conocida del video de prueba"""
    return 180.0  # Ajusta este valor a la duración real de tu video

@pytest.fixture
def mock_vertex_ai():
    """Mock completo para Vertex AI"""
    with patch('vertexai.init') as mock_init, \
         patch('google.oauth2.service_account.Credentials.from_service_account_file') as mock_creds:
        mock_creds.return_value = Mock(
            project_id='test-project',
            service_account_email='test@test.iam.gserviceaccount.com'
        )
        yield mock_init

@pytest.fixture
def mock_generative_model():
    """Mock del modelo generativo"""
    return Mock(spec=GenerativeModel)

def pytest_sessionstart(session):
    """Cargar variables de entorno de prueba"""
    env_file = Path(__file__).parent / '.env.test'
    load_dotenv(env_file)

import json
from unittest.mock import Mock, patch

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Mock de variables de entorno"""
    mock_creds = {
        "type": "service_account",
        "project_id": "test-project",
        "private_key_id": "test-key-id",
        "private_key": "test-private-key",
        "client_email": "test@test.iam.gserviceaccount.com",
        "client_id": "test-client-id",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/test"
    }
    
    monkeypatch.setenv('GOOGLE_APPLICATION_CREDENTIALS', json.dumps(mock_creds))
    monkeypatch.setenv('GOOGLE_CLOUD_PROJECT', 'test-project')
    monkeypatch.setenv('VERTEX_LOCATION', 'us-central1')
    monkeypatch.setenv('YOUTUBE_API_KEY', 'test-key')

@pytest.fixture
def mock_gemini_model():
    """Mock de Gemini Model"""
    mock_model = Mock()
    mock_model.generate_content.return_value = Mock(
        text="Descripción de prueba",
        candidates=[Mock(likelihood=0.9)],
        safety_ratings=[Mock(category="HARM", probability="LOW")]
    )
    return mock_model

@pytest.fixture
def mock_video_analyzer(mock_gemini_model):
    """Mock de VideoAnalyzer"""
    from app.core.video_analyzer import VideoAnalyzer
    config = {
        'batch_size': 32,
        'max_retries': 3,
        'temperature': 0.7,
        'max_tokens': 1024
    }
    return VideoAnalyzer(config=config)

@pytest.fixture(scope="session")
def test_config():
    return VideoConfig(
        frame_rate=25,
        min_scene_duration=2.0,
        resolution=(1920, 1080)
    )

@pytest.fixture
def test_config():
    """Fixture para configuración de pruebas"""
    return {
        "batch_size": 32,
        "max_retries": 3,
        "max_concurrent_tasks": 3,
        "max_memory_percent": 80,
        "temperature": 0.7,
        "max_tokens": 1024,
        "language": "es",
        "storage_bucket": "test-bucket",
        "temp_storage_path": "./temp",
        "output_storage_path": "./output/test",
        "cache_dir": "./cache",
        "max_video_duration": 3600,
        "scene_detection_threshold": 0.3,
        "min_scene_duration": 2.0
    }

@pytest.fixture
def video_config(test_config):
    """Fixture para VideoConfig"""
    return VideoConfig(**test_config)

@pytest.fixture
def test_video_path():
    """Fixture para ruta de video de prueba"""
    return Path("tests/fixtures/test_video.mp4")