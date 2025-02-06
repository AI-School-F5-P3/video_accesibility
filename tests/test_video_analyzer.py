import os
import sys
import pytest
import numpy as np
import cv2

# Add the parent directory to sys.path to allow imports from the "core" module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.video_analyzer import YouTubeVideoManager, YouTubeVideoMetadata, VideoProcessor, VideoFormat


# Fixture that provides a sample valid YouTube URL for testing
@pytest.fixture
def valid_youtube_url():
    return "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


# Fixture that provides mock metadata for a YouTube video
@pytest.fixture
def mock_youtube_metadata():
    return YouTubeVideoMetadata(
        url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        title="Test Video",
        duration=180,
        video_format=".mp4",
        thumbnail="https://example.com/thumbnail.jpg",
        width=1920,
        height=1080,
        fps=30.0
    )


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
def test_download_video_updates_metadata(mocker, valid_youtube_url, mock_youtube_metadata):  # Añadido mock_youtube_metadata como parámetro
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
def test_analyze_scene_changes(mocker, valid_youtube_url, mock_youtube_metadata):  # Añadido mock_youtube_metadata como parámetro
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
def test_generate_accessibility_report(mocker, valid_youtube_url, mock_youtube_metadata):  # Añadido mock_youtube_metadata como parámetro
    mocker.patch.object(YouTubeVideoManager, '_extract_youtube_metadata', return_value=mock_youtube_metadata)
    mocker.patch.object(YouTubeVideoManager, 'analyze_scene_changes', return_value=[5, 10, 15])
    
    video_manager = YouTubeVideoManager(valid_youtube_url)
    report = video_manager.generate_accessibility_report()
    
    assert report["title"] == mock_youtube_metadata.title
    assert report["duration"] == mock_youtube_metadata.duration
    assert report["resolution"] == f"{mock_youtube_metadata.width}x{mock_youtube_metadata.height}"
    assert report["scene_changes"] == 3


# Test cleanup method to ensure temporary files are removed correctly
def test_cleanup(mocker, valid_youtube_url, mock_youtube_metadata):  # Añadido mock_youtube_metadata como parámetro
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
def test_failed_cleanup(mocker, valid_youtube_url, mock_youtube_metadata):  # Añadido mock_youtube_metadata como parámetro
    mock_video_path = "/mock/path/to/video.mp4"
    mocker.patch('os.path.exists', return_value=True)
    mocker.patch('os.remove', side_effect=Exception("Mock error"))
    mocker.patch.object(YouTubeVideoManager, '_extract_youtube_metadata', return_value=mock_youtube_metadata)
    
    video_manager = YouTubeVideoManager(valid_youtube_url)
    video_manager.video_path = mock_video_path
    
    video_manager.cleanup() # This should not raise an exception, even if os.remove fails
