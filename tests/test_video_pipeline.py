import pytest
import os
from unittest.mock import Mock, patch
from dotenv import load_dotenv
from src.pipeline.video_pipeline import VideoPipeline
from src.config import Settings
from vertexai.language_models import TextGenerationModel

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

@pytest.fixture
def pipeline(monkeypatch, mock_text_model):
    """Fixture para VideoPipeline con mocks"""
    monkeypatch.setenv('YOUTUBE_API_KEY', os.getenv('YOUTUBE_API_KEY'))
    monkeypatch.setattr(
        'vertexai.language_models.TextGenerationModel', 
        lambda *args, **kwargs: mock_text_model
    )
    config = Settings().get_config()
    return VideoPipeline(config)

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
async def test_process_url(pipeline):
    """Test procesamiento de URL"""
    with patch('src.pipeline.video_pipeline.VideoPipeline.download_video') as mock_download:
        mock_download.return_value = {
            'video_path': 'test.mp4',
            'metadata': {'title': 'Test Video'}
        }
        
        test_url = "https://www.youtube.com/watch?v=test123"
        result = await pipeline.process_url(test_url, "SUBTITULADO")
        assert result is not None
        assert 'subtitles' in result

@pytest.mark.asyncio
@pytest.mark.parametrize("service_type", ["AUDIODESCRIPCION", "SUBTITULADO"])
async def test_service_types(pipeline, service_type):
    """Test diferentes tipos de servicio"""
    with patch('src.pipeline.video_pipeline.VideoPipeline.download_video') as mock_download:
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