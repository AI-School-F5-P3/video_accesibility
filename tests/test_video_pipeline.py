import pytest
import os
from unittest.mock import Mock, patch
from dotenv import load_dotenv
from app.pipeline.video_pipeline import VideoPipeline
from app.config.settings import Settings
from vertexai.language_models import TextGenerationModel
from dataclasses import dataclass, field
from app.services.youtube import YouTubeAPI
import vertexai
import json
from pathlib import Path
from app.models.schemas import ServiceType, ProcessingResult

load_dotenv()

@dataclass
class UNE153010Config:
    COLORS: dict = field(default_factory=dict)

@pytest.fixture
def youtube_api():
    """Fixture para YouTube API"""
    api_key = os.getenv('YOUTUBE_API_KEY')
    if not api_key:
        pytest.skip("YouTube API KEY no encontrada en .env")
    return YouTubeAPI(api_key)

@pytest.fixture(autouse=True)
def setup_vertexai():
    """Configuración de VertexAI para tests"""
    with patch('vertexai.init') as mock_init:
        vertexai.init(
            project=os.getenv('GOOGLE_CLOUD_PROJECT'),
            location=os.getenv('VERTEX_LOCATION')
        )
        yield mock_init

@pytest.fixture
def mock_text_model():
    """Mock para TextGenerationModel"""
    mock = Mock(spec=TextGenerationModel)
    mock.predict.return_value = Mock(text="Texto generado de prueba")
    return mock

@pytest.fixture(autouse=True)
def mock_env_and_credentials(monkeypatch):
    """Mock para variables de entorno y credenciales"""
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
def mock_video_file(tmp_path):
    """Crea un archivo de video de prueba"""
    video_path = tmp_path / "test.mp4"
    # Crear un archivo de video dummy
    with open(video_path, 'wb') as f:
        f.write(b'dummy video content')
    return video_path

@pytest.fixture
def pipeline(monkeypatch, mock_text_model, mock_env_and_credentials):
    """Fixture para VideoPipeline con mocks"""
    config = Settings().get_config()
    with patch('app.services.ai.ai_service.AIService.__init__') as mock_ai_init:
        mock_ai_init.return_value = None
        return VideoPipeline(config)

@pytest.fixture
def mock_youtube_api():
    return Mock(spec=YouTubeAPI)

@pytest.mark.skip(reason="YouTube API requiere autenticación")
def test_youtube_api_connection(youtube_api):
    """Verifica la conexión con YouTube API"""
    try:
        test_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw"
        result = youtube_api.download_video(test_url)
        
        assert result is not None
        assert 'video_path' in result
        assert 'metadata' in result
        
    except Exception as e:
        pytest.fail(f"Error en conexión con YouTube API: {str(e)}")

@pytest.mark.asyncio
async def test_process_url(mock_video_analyzer):
    """Test de procesamiento de URL"""
    pipeline = VideoPipeline(config={'test': True})
    result = await pipeline.process_url(
        "https://www.youtube.com/watch?v=test",
        ServiceType.AUDIODESCRIPCION
    )
    assert isinstance(result, ProcessingResult)
    assert result.status in ['completed', 'error']

@pytest.mark.asyncio
async def test_process_url(pipeline):
    """Test procesamiento de URL"""
    with patch('app.pipeline.video_pipeline.VideoPipeline.download_video') as mock_download:
        mock_download.return_value = {
            'video_path': 'test.mp4',
            'metadata': {'title': 'Test Video'}
        }
        
        test_url = "https://www.youtube.com/watch?v=test123"
        result = await pipeline.process_url(test_url, "SUBTITULADO")
        assert result is not None
        assert 'subtitles' in result

@pytest.mark.asyncio
async def test_youtube_api_connection(mock_youtube_api):
    """Test de conexión a YouTube API con mock"""
    video_id = "JYJqu3nI0Zk"
    mock_youtube_api.get_video_info.return_value = {
        "id": video_id,
        "title": "Test Video",
        "duration": "PT2M30S"
    }
    
    result = await mock_youtube_api.get_video_info(video_id)
    assert result["id"] == video_id
    assert "title" in result

@pytest.mark.asyncio
@pytest.mark.parametrize("service_type", [
    ServiceType.AUDIODESCRIPCION,
    ServiceType.SUBTITULADO
])
async def test_service_types(mock_video_analyzer, service_type):
    """Test de diferentes tipos de servicio"""
    pipeline = VideoPipeline(config={'test': True})
    result = await pipeline.process_url(
        "https://www.youtube.com/watch?v=test",
        service_type
    )
    assert isinstance(result, ProcessingResult)

@pytest.mark.asyncio
@pytest.mark.parametrize("service_type", ["AUDIODESCRIPCION", "SUBTITULADO"])
async def test_service_types(pipeline, service_type):
    """Test diferentes tipos de servicio"""
    with patch('app.pipeline.video_pipeline.VideoPipeline.download_video') as mock_download:
        mock_download.return_value = {
            'video_path': 'test.mp4',
            'metadata': {'title': 'Test Video'}
        }
        
        test_url = "https://www.youtube.com/watch?v=test123"
        result = await pipeline.process_url(test_url, service_type)
        assert result is not None

def test_invalid_service_type(pipeline):
    """Verifica el manejo de tipo de servicio inválido"""
    with pytest.raises(ValueError):
        pipeline.process_url("https://youtube.com", "SERVICIO_INVALIDO")

@pytest.fixture(autouse=True)
def cleanup():
    """Limpia archivos temporales después de cada test"""
    yield
    # Limpiar archivos temporales
    temp_dir = "output/temp"
    if os.path.exists(temp_dir):
        for file in os.listdir(temp_dir):
            os.remove(os.path.join(temp_dir, file))