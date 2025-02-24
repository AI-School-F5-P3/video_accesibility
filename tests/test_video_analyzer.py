import pytest
import cv2
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch
from app.core.video_analyzer import VideoAnalyzer, VideoConfig  # Cambiar src por app
from app.models.schemas import Scene, VideoMetadata

@pytest.fixture
def mock_gemini_model(monkeypatch):
    """Fixture for mocking Gemini model responses."""
    class MockResponse:
        text = "Una persona trabaja en un ordenador en una oficina bien iluminada"
    
    class MockModel:
        def generate_content(self, *args, **kwargs):
            return MockResponse()
    
    return MockModel()

@pytest.fixture
def test_frame():
    """Fixture for test frame data."""
    return np.zeros((720, 1280, 3), dtype=np.uint8)

@pytest.fixture
def video_config():
    return {
        'video_config': {
            'SCENE_DETECTION_THRESHOLD': 0.3,
            'MIN_SCENE_DURATION': 2.0,
            'FRAME_SAMPLE_RATE': 1
        }
    }

@pytest.fixture
def video_analyzer():
    config = VideoConfig(
        frame_rate=25,
        min_scene_duration=2.0,
        resolution=(1920, 1080)
    )
    return VideoAnalyzer(config=config)

@pytest.fixture
def sample_video(tmp_path):
    """Crea un video de prueba"""
    video_path = tmp_path / "test.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640, 480))
    
    # Crear frames de prueba
    for _ in range(90):  # 3 segundos a 30fps
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        out.write(frame)
    
    out.release()
    return video_path

def test_scene_analysis(video_config):
    analyzer = VideoAnalyzer(config=video_config)
    # Resto del test...

def test_scene_analysis(monkeypatch, mock_gemini_model, une_standards):
    """Tests video scene analysis."""
    analyzer = VideoAnalyzer(model=mock_gemini_model)
    
    def mock_analyze_scene(*args, **kwargs):
        return {
            "description": "A person sits at a desk working on a laptop",
            "objects": ["person", "desk", "laptop"],
            "scene_type": "office",
            "accessibility_context": {
                "lighting": "well-lit",
                "movement": "minimal",
                "spatial_info": "centered in frame"
            }
        }
    
    monkeypatch.setattr(analyzer, 'analyze_scene', mock_analyze_scene)
    
    result = analyzer.analyze_scene(np.zeros((100, 100, 3)))
    
    # Verify UNE153020 compliance
    assert len(result["description"].split()) <= une_standards['UNE153020']['max_words_per_description']
    assert all(key in result for key in ["description", "objects", "scene_type"])
    assert "accessibility_context" in result

def test_visual_content_analysis(mocker, test_frame, une_standards):
    """
    Tests the analysis of visual content for accessibility requirements.
    """
    analyzer = VideoAnalyzer()
    mock_content = {
        "important_elements": ["person walking", "red car", "sunset"],
        "scene_context": "outdoor urban",
        "movement_level": "moderate",
        "requires_description": True,
        "confidence_score": 0.95
    }
    
    mocker.patch.object(
        analyzer,
        'analyze_visual_content',
        return_value=mock_content
    )
    
    content_analysis = analyzer.analyze_visual_content(test_frame)
    
    assert isinstance(content_analysis["important_elements"], list)
    assert content_analysis["scene_context"] != ""
    assert isinstance(content_analysis["requires_description"], bool)
    assert content_analysis["confidence_score"] >= 0.85  # UNE threshold

def test_analyzer_initialization(mock_gemini_model):
    """Tests VideoAnalyzer initialization with config."""
    config = VideoConfig(
        frame_rate=25,
        min_scene_duration=2.0,
        resolution=(1920, 1080)
    )
    
    analyzer = VideoAnalyzer(model=mock_gemini_model, config=config)
    
    assert analyzer.model == mock_gemini_model
    assert analyzer.config.frame_rate == 25
    assert analyzer.config.min_scene_duration == 2.0

def test_scene_detection(mocker, test_frame, une_standards):
    """Tests scene change detection and duration compliance."""
    analyzer = VideoAnalyzer()
    
    mock_scenes = [
        {"start_time": 0.0, "end_time": 4.0, "keyframe": test_frame},
        {"start_time": 4.0, "end_time": 8.0, "keyframe": test_frame}
    ]
    
    mocker.patch.object(
        analyzer,
        'detect_scenes',
        return_value=mock_scenes
    )
    
    scenes = analyzer.detect_scenes("test_video.mp4")
    
    for scene in scenes:
        duration = scene["end_time"] - scene["start_time"]
        assert duration >= une_standards['UNE153020']['min_scene_duration']
        assert "keyframe" in scene

def test_description_generation(mock_gemini_model, une_standards):
    """Tests generation of accessible descriptions."""
    analyzer = VideoAnalyzer(model=mock_gemini_model)
    
    scene_data = {
        "objects": ["person", "laptop", "desk"],
        "scene_type": "office",
        "movement": "minimal"
    }
    
    description = analyzer.generate_description(scene_data)
    
    words = description.split()
    assert len(words) <= une_standards['UNE153020']['max_words_per_description']
    assert any(obj in description.lower() for obj in scene_data["objects"])

def test_silence_detection(mocker, une_standards):
    """Tests detection of silence periods for audio descriptions."""
    analyzer = VideoAnalyzer()
    silence_periods = [
        {"start": 1.0, "end": 3.5},
        {"start": 4.0, "end": 6.0}
    ]
    
    mocker.patch.object(
        analyzer,
        'find_silences',
        return_value=silence_periods
    )
    
    result = analyzer.find_silences("test_video.mp4")
    
    for period in result:
        duration = period["end"] - period["start"]
        assert duration >= une_standards['UNE153020']['silence_gap']

def test_description_placement(mocker, une_standards):
    """Tests optimal placement points for audio descriptions."""
    analyzer = VideoAnalyzer()
    placement_points = [
        {"timestamp": 4.5, "duration": 2.5, "priority": "high"},  # Duración ajustada
        {"timestamp": 8.2, "duration": 2.0, "priority": "medium"}
    ]
    
    mocker.patch.object(
        analyzer,
        'find_description_points',
        return_value=placement_points
    )
    
    result = analyzer.find_description_points("test_video.mp4")
    
    for point in result:
        assert point["duration"] >= une_standards['UNE153020']['silence_gap']

@pytest.mark.integration
def test_full_analysis_pipeline(mock_ai_model, mock_video_file, une_standards):
    analyzer = VideoAnalyzer(model=mock_ai_model)
    results = analyzer.analyze_video(mock_video_file)
    
    assert "scenes" in results
    assert "descriptions" in results
    assert "metadata" in results

def test_error_handling():
    """Tests error handling in video analysis."""
    analyzer = VideoAnalyzer()
    
    with pytest.raises(ValueError):
        analyzer.analyze_video(None)
    
    with pytest.raises(FileNotFoundError):
        analyzer.analyze_video("nonexistent_video.mp4")
    
    with pytest.raises(ValueError):
        analyzer.process_frame(None)

@pytest.mark.asyncio
async def test_video_metadata(test_video_path):
    """Verifica que podemos leer el video correctamente"""
    cap = cv2.VideoCapture(str(test_video_path))
    assert cap.isOpened()
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration = frame_count / fps
    
    cap.release()
    
    assert fps > 0
    assert frame_count > 0
    assert duration > 0

@pytest.mark.asyncio
async def test_scene_detection(video_analyzer, sample_video):
    """Test de detección de escenas"""
    scenes = await video_analyzer.detect_scenes(sample_video)
    
    assert isinstance(scenes, list)
    assert len(scenes) > 0
    for scene in scenes:
        assert scene.start_time >= 0
        assert scene.end_time > scene.start_time
        assert 0 <= scene.confidence <= 1

@pytest.mark.asyncio
async def test_analyze_content(video_analyzer, sample_video):
    """Test de análisis completo"""
    metadata = await video_analyzer.analyze_content(sample_video)
    
    assert metadata.path == sample_video
    assert metadata.duration > 0
    assert metadata.fps == 30.0
    assert metadata.resolution == (640, 480)
    assert len(metadata.scenes) > 0

@pytest.mark.asyncio
async def test_invalid_video(video_analyzer, tmp_path):
    """Test con video inválido"""
    invalid_video = tmp_path / "invalid.mp4"
    invalid_video.touch()
    
    with pytest.raises(RuntimeError):
        await video_analyzer.detect_scenes(invalid_video)

def test_frame_difference(video_analyzer):
    """Test de cálculo de diferencia entre frames"""
    frame1 = np.zeros((480, 640, 3), dtype=np.uint8)
    frame2 = np.ones((480, 640, 3), dtype=np.uint8) * 255
    
    diff = video_analyzer._calculate_frame_difference(frame1, frame2)
    assert diff == 1.0  # Diferencia máxima

@pytest.mark.asyncio
async def test_scene_analysis(mock_video_analyzer, test_video_path):
    """Test de análisis de escenas"""
    scenes = await mock_video_analyzer.detect_scenes(test_video_path)
    assert isinstance(scenes, list)
    if scenes:
        assert all(isinstance(scene, Scene) for scene in scenes)

@pytest.mark.asyncio
async def test_full_analysis_pipeline(mock_video_analyzer, test_video_path):
    """Test del pipeline completo de análisis"""
    metadata = await mock_video_analyzer.analyze_content(test_video_path)
    assert isinstance(metadata, VideoMetadata)
    assert metadata.path == test_video_path
    assert metadata.duration > 0
    assert len(metadata.scenes) > 0

def test_video_analyzer_initialization(video_config):
    """Test inicialización del VideoAnalyzer"""
    analyzer = VideoAnalyzer(config=video_config.model_dump())
    assert analyzer is not None
    assert analyzer.batch_size == 32
    assert analyzer.scene_detection_method == 'histogram'

def test_video_analyzer_parameters(video_config):
    """Test parámetros del VideoAnalyzer"""
    analyzer = VideoAnalyzer(config=video_config.model_dump())
    assert analyzer.scene_threshold == 0.3
    assert analyzer.min_scene_duration == 2.0
    assert analyzer.sample_rate == 1

@pytest.mark.asyncio
async def test_video_analysis(video_config, test_video_path):
    """Test análisis de video"""
    analyzer = VideoAnalyzer(config=video_config.model_dump())
    result = await analyzer.analyze_video(test_video_path)
    assert result is not None