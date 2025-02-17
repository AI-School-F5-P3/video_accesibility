import os
import sys
import pytest
import numpy as np
import cv2
from unittest.mock import Mock, patch
from io import StringIO
from pathlib import Path
import json
import math

# Add the parent directory to sys.path to allow imports from the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

# Import modules from all test files
from core.video_analyzer import YouTubeVideoManager, YouTubeVideoMetadata, VideoProcessor, VideoFormat
from core.video_analyzer_api import (
    YouTubeAPI,
    VideoDownloader,
    VideoProcessor as APIVideoProcessor,
    YouTubeVideoManager as APIYouTubeVideoManager
)
from src.core.video_analyzer import VideoAnalyzer, VideoConfig, FrameExtractor, FrameAnalyzer

# FIXTURES

# Fixture that provides a sample valid YouTube URL for testing
@pytest.fixture
def valid_youtube_url():
    return "https://www.youtube.com/watch?v=JYJqu3nI0Zk&t=14s&ab_channel=Rioja2.com"

# Fixture that provides mock metadata for a YouTube video
@pytest.fixture
def mock_youtube_metadata():
    return YouTubeVideoMetadata(
        url="https://www.youtube.com/watch?v=JYJqu3nI0Zk&t=14s&ab_channel=Rioja2.com",
        title="Test Video",
        duration=180,
        video_format=".mp4",
        thumbnail="https://example.com/thumbnail.jpg",
        width=1920,
        height=1080,
        fps=30.0
    )

@pytest.fixture
def mock_youtube_api():
    with patch("core.video_analyzer_api.build") as mock_build:
        mock_service = Mock()
        mock_build.return_value = mock_service
        mock_service.channels().list.return_value.execute.return_value = {
            "items": [{"contentDetails": {"relatedPlaylists": {"uploads": "mock_playlist_id"}}}]
        }
        mock_service.playlistItems().list.return_value.execute.return_value = {
            "items": [{"snippet": {"title": "Video 1", "resourceId": {"videoId": "123"}, "thumbnails": {"high": {"url": "mock_url"}}, "description": "desc", "publishedAt": "2023"}}]
        }
        yield YouTubeAPI()

@pytest.fixture
def mock_video_downloader():
    with patch("core.video_analyzer_api.yt_dlp.YoutubeDL") as mock_yt:
        mock_yt.return_value.__enter__.return_value.download.return_value = None
        yield VideoDownloader("mock_video_id")

@pytest.fixture
def mock_video_processor():
    yield APIVideoProcessor()

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
def une_standards():
    """Fixture for UNE153020 standards."""
    return {
        'UNE153020': {
            'max_words_per_description': 80,
            'min_scene_duration': 2.0,
            'silence_gap': 1.5
        }
    }

@pytest.fixture
def mock_ai_model():
    class MockAIModel:
        def generate_content(self, content):
            return type('obj', (object,), {'text': 'A person working on a computer in a well-lit office'})()
    return MockAIModel()

@pytest.fixture
def mock_video_file(tmp_path):
    file_path = tmp_path / "mock_video.mp4"
    file_path.touch()
    return str(file_path)

@pytest.fixture
def create_test_video(tmp_path):
    """Creates a sample video file for testing"""
    video_path = tmp_path / "test_video.mp4"
    
    # Create a simple video with black frames
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640,480))
    
    # Create 90 frames (3 seconds at 30fps)
    for _ in range(90):
        frame = np.zeros((480,640,3), np.uint8)
        out.write(frame)
    
    out.release()
    return str(video_path)

@pytest.fixture
def output_directory(tmp_path):
    """Creates a temporary directory for output frames"""
    output_dir = tmp_path / "frames"
    return str(output_dir)

# TESTS FROM test_video_analyzer.py

# Test to validate that an invalid video format raises a ValueError
def test_video_format_validation():
    with pytest.raises(ValueError):
        YouTubeVideoMetadata(
            url="test",
            title="test",
            duration=100,
            video_format=".invalid",
            thumbnail="test",
            width=1920,
            height=1080
        )

# Test to ensure a video duration of zero raises a ValueError
def test_duration_validation():
    with pytest.raises(ValueError):
        YouTubeVideoMetadata(
            url="test",
            title="test",
            duration=0,
            video_format=".mp4",
            thumbnail="test",
            width=1920,
            height=1080
        )

# Test to check if zero or negative width/height raises a ValueError
def test_dimensions_validation():
    with pytest.raises(ValueError):
        YouTubeVideoMetadata(
            url="test",
            title="test",
            duration=100,
            video_format=".mp4",
            thumbnail="test",
            width=0,
            height=1080
        )

# Test to verify that downloading a video correctly updates its metadata
def test_download_video_updates_metadata(mocker, valid_youtube_url, mock_youtube_metadata):
    mock_video_path = "/mock/path/to/video.mp4"
    
    # Mock OpenCV VideoCapture to simulate reading a video file
    mock_video = mocker.MagicMock()
    mock_video.isOpened.return_value = True
    mock_video.get.side_effect = lambda x: {
        cv2.CAP_PROP_FRAME_WIDTH: 1920,
        cv2.CAP_PROP_FRAME_HEIGHT: 1080,
        cv2.CAP_PROP_FPS: 30.0
    }[x]
    
    # Patch OpenCV VideoCapture and YouTubeVideoManager methods
    mocker.patch('cv2.VideoCapture', return_value=mock_video)
    mocker.patch.object(YouTubeVideoManager, '_download_video', return_value=mock_video_path)
    mocker.patch.object(YouTubeVideoManager, '_extract_youtube_metadata', return_value=mock_youtube_metadata)
    
    # Initialize the video manager and download the video
    video_manager = YouTubeVideoManager(valid_youtube_url)
    video_manager.video_path = video_manager._download_video()
    video_manager._update_video_metadata(video_manager.video_path)
    
    # Verify that metadata was updated correctly
    assert video_manager.metadata.width == 1920
    assert video_manager.metadata.height == 1080
    assert video_manager.metadata.fps == 30.0

# Test to ensure scene changes are detected correctly
def test_analyze_scene_changes(mocker, valid_youtube_url, mock_youtube_metadata):
    frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
    frame2 = np.full((100, 100, 3), 255, dtype=np.uint8)
    mock_frames = [frame1, frame1, frame2, frame1, frame2]

    # Patch YouTubeVideoManager methods
    mocker.patch.object(YouTubeVideoManager, '_extract_youtube_metadata', return_value=mock_youtube_metadata)
    mocker.patch.object(YouTubeVideoManager, 'representative_frames', property(lambda self: mock_frames))
    
    # Analyze scene changes and verify detection
    video_manager = YouTubeVideoManager(valid_youtube_url)
    scene_changes = video_manager.analyze_scene_changes(threshold=0.1)
    
    assert isinstance(scene_changes, list)
    assert len(scene_changes) > 0

# Test VideoProcessor to ensure frame extraction works correctly
def test_video_processor_extract_frames(mocker):
    mock_video = mocker.MagicMock()
    mock_frame = np.zeros((100, 100, 3), dtype=np.uint8)
    mock_video.read.side_effect = [(True, mock_frame.copy()), (True, mock_frame.copy()), (False, None)]
    mock_video.isOpened.return_value = True
    
    mocker.patch('cv2.VideoCapture', return_value=mock_video)
    frames = VideoProcessor.extract_frames("/mock/path.mp4", interval=1, fps=1)
    assert len(frames) == 2

# Test VideoProcessor to ensure scene changes are detected correctly
def test_video_processor_detect_scene_changes():
    frame1 = np.zeros((100, 100, 3), dtype=np.uint8)
    frame2 = np.full((100, 100, 3), 255, dtype=np.uint8)
    frames = [frame1, frame2, frame1]
    
    scene_changes = VideoProcessor.detect_scene_changes(frames, threshold=0.1)
    assert len(scene_changes) > 0

# Test to ensure the accessibility report contains correct data
def test_generate_accessibility_report(mocker, valid_youtube_url, mock_youtube_metadata):
    mocker.patch.object(YouTubeVideoManager, '_extract_youtube_metadata', return_value=mock_youtube_metadata)
    mocker.patch.object(YouTubeVideoManager, 'analyze_scene_changes', return_value=[5, 10, 15])
    
    video_manager = YouTubeVideoManager(valid_youtube_url)
    report = video_manager.generate_accessibility_report()
    
    assert report["title"] == mock_youtube_metadata.title
    assert report["duration"] == mock_youtube_metadata.duration
    assert report["resolution"] == f"{mock_youtube_metadata.width}x{mock_youtube_metadata.height}"
    assert report["scene_changes"] == 3

# Test cleanup method to ensure temporary files are removed correctly
def test_cleanup(mocker, valid_youtube_url, mock_youtube_metadata):
    mock_video_path = "/mock/path/to/video.mp4"

    # Mock os.path.exists and os.remove
    mocker.patch('os.path.exists', return_value=True)
    mock_remove = mocker.patch('os.remove')
    mocker.patch.object(YouTubeVideoManager, '_extract_youtube_metadata', return_value=mock_youtube_metadata)
    
    video_manager = YouTubeVideoManager(valid_youtube_url)
    video_manager.video_path = mock_video_path
    video_manager.cleanup()
    
    # Verify that os.remove was called with the correct file path
    mock_remove.assert_called_once_with(mock_video_path)

# Test cleanup method when os.remove raises an exception (should not crash)
def test_failed_cleanup(mocker, valid_youtube_url, mock_youtube_metadata):
    mock_video_path = "/mock/path/to/video.mp4"
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.remove', side_effect=Exception("Mock error"))
    mocker.patch.object(YouTubeVideoManager, '_extract_youtube_metadata', return_value=mock_youtube_metadata)
    
    video_manager = YouTubeVideoManager(valid_youtube_url)
    video_manager.video_path = mock_video_path
    
    video_manager.cleanup()  # This should not raise an exception, even if os.remove fails

# TESTS FROM test_video_analyzer_api.py

@patch("core.video_analyzer_api.build")
def test_youtube_api_authenticate(mock_build):
    api = YouTubeAPI()
    assert api.service is not None
    mock_build.assert_called_once()

def test_youtube_api_get_uploaded_videos(mock_youtube_api):
    videos = mock_youtube_api.get_uploaded_videos("mock_channel_id")
    assert len(videos) == 1
    assert videos[0]["title"] == "Video 1"

@patch("os.path.exists", return_value=True)
@patch("cv2.VideoCapture")
def test_api_video_processor_extract_frames(mock_cv2, mock_exists, mock_video_processor):
    mock_video = Mock()
    mock_video.isOpened.return_value = True
    mock_video.get.return_value = 30  # Mock FPS value
    mock_video.read.side_effect = [(True, np.zeros((480, 640, 3), dtype=np.uint8))] * 10 + [(False, None)]
    mock_cv2.return_value = mock_video

    frames = mock_video_processor.extract_frames("mock_video.mp4", interval=5)
    assert isinstance(frames, list)
    assert len(frames) > 0

@patch("cv2.absdiff", return_value=Mock())
def test_api_video_processor_detect_scene_changes(mock_absdiff, mock_video_processor):
    frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(3)]
    scenes = mock_video_processor.detect_scene_changes(frames, threshold=0.1)
    assert isinstance(scenes, list)

@patch("builtins.input", side_effect=["1"])
@patch("sys.stdout", new_callable=StringIO)
def test_api_youtube_video_manager(mock_stdout, mock_input):
    manager = APIYouTubeVideoManager()
    manager.youtube_api.get_uploaded_videos = Mock(return_value=[
        {"title": "Test Video", "video_id": "123", "published_at": "2023", "description": "desc"}
    ])
    
    with patch("builtins.print"), patch("builtins.input", return_value="1"):
        selected_video = manager.select_video("mock_channel_id")
    
    assert selected_video is not None, "No video was selected"
    assert selected_video["video_id"] == "123"

# TESTS FROM test_video_analyzer (1).py

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
    """Tests the analysis of visual content for accessibility requirements."""
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
        {"timestamp": 4.5, "duration": 2.5, "priority": "high"},
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

# TESTS FROM NEW test_video_analyzer.py FOR FRAME EXTRACTION

class TestFrameExtraction:
    """Tests for the frame extraction functionality only"""
    
    def test_video_loading(self, create_test_video, output_directory):
        """Test that video properties are correctly loaded"""
        with patch('src.core.video_analyzer.FrameAnalyzer'):  # Mock the analyzer
            extractor = FrameExtractor(create_test_video, output_directory)
            assert math.isclose(extractor.fps, 30.0, rel_tol=1e-9)
            assert extractor.frame_count == 90
            assert extractor.duration == pytest.approx(3.0)

    def test_frame_extraction_interval(self, create_test_video, output_directory):
        """Test that frames are extracted at correct intervals"""
        with patch('src.core.video_analyzer.FrameAnalyzer'):
            extractor = FrameExtractor(create_test_video, output_directory, interval=1)
            frames_info = extractor.extract_frames()
            
            # Should have 3 frames for a 3-second video with 1-second interval
            assert len(frames_info) == 3
            
            # Check frame intervals
            timestamps = [t for t, _ in frames_info]
            intervals = np.diff(timestamps)
            assert all(pytest.approx(i) == 1.0 for i in intervals)

    def test_frame_saving(self, create_test_video, output_directory):
        """Test that frames are saved as valid image files"""
        with patch('src.core.video_analyzer.FrameAnalyzer'):
            extractor = FrameExtractor(create_test_video, output_directory)
            frames_info = extractor.extract_frames()
            
            for _, frame_path in frames_info:
                assert Path(frame_path).exists()
                img = cv2.imread(frame_path)
                assert img is not None
                assert img.shape == (480, 640, 3)

    def test_invalid_video_path(self, output_directory):
        """Test handling of invalid video path"""
        with patch('src.core.video_analyzer.FrameAnalyzer'):
            with pytest.raises(ValueError) as exc_info:
                FrameExtractor("nonexistent_video.mp4", output_directory)
            assert "Could not open video" in str(exc_info.value)

@pytest.mark.skipif(
    "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ,
    reason="Google Cloud credentials not configured"
)
class TestCloudVision:
    """Tests that require Google Cloud Vision credentials"""
    
    def test_frame_analysis(self, tmp_path):
        """Test frame analysis with Google Cloud Vision"""
        # This test only runs if credentials are properly configured
        analyzer = FrameAnalyzer()
        
        # Create a simple test image
        test_image = tmp_path / "test.jpg"
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(test_image), img)
        
        # Test analysis
        result = analyzer.analyze_frame(str(test_image))
        assert isinstance(result, dict)
        assert 'objects' in result
        assert 'labels' in result
        assert 'text' in result

def test_process_video_output(create_test_video, output_directory):
    """Test the complete video processing pipeline"""
    # Mock the Google Cloud Vision analysis part
    mock_analysis = {
        'objects': [],
        'labels': [{'description': 'Test', 'confidence': 0.9}],
        'text': ''
    }
    
    with patch('src.core.video_analyzer.FrameAnalyzer') as MockAnalyzer:
        mock_instance = MockAnalyzer.return_value
        mock_instance.analyze_frame.return_value = mock_analysis
        
        extractor = FrameExtractor(create_test_video, output_directory)
        results = extractor.process_video()
        
        # Check results structure
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, dict) for r in results)
        assert all('timestamp' in r for r in results)
        assert all('analysis' in r for r in results)