import os
import sys
import pytest
from unittest.mock import Mock, patch
from io import StringIO
import cv2
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from core.video_analyzer_api import (
    YouTubeAPI,
    VideoDownloader,
    VideoProcessor,
    YouTubeVideoManager
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
    yield VideoProcessor()

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
def test_video_processor_extract_frames(mock_cv2, mock_exists, mock_video_processor):
    mock_video = Mock()
    mock_video.isOpened.return_value = True
    mock_video.get.return_value = 30  # Mock FPS value
    mock_video.read.side_effect = [(True, np.zeros((480, 640, 3), dtype=np.uint8))] * 10 + [(False, None)]
    mock_cv2.return_value = mock_video

    frames = mock_video_processor.extract_frames("mock_video.mp4", interval=5)
    assert isinstance(frames, list)
    assert len(frames) > 0

@patch("cv2.absdiff", return_value=Mock())
def test_video_processor_detect_scene_changes(mock_absdiff, mock_video_processor):
    frames = [np.zeros((480, 640, 3), dtype=np.uint8) for _ in range(3)]
    scenes = mock_video_processor.detect_scene_changes(frames, threshold=0.1)
    assert isinstance(scenes, list)

@patch("builtins.input", side_effect=["1"])
@patch("sys.stdout", new_callable=StringIO)
def test_youtube_video_manager(mock_stdout, mock_input):
    manager = YouTubeVideoManager()
    manager.youtube_api.get_uploaded_videos = Mock(return_value=[
        {"title": "Test Video", "video_id": "123", "published_at": "2023", "description": "desc"}
    ])
    
    with patch("builtins.print"), patch("builtins.input", return_value="1"):
        selected_video = manager.select_video("mock_channel_id")
    
    assert selected_video is not None, "No se seleccionó ningún video"
    assert selected_video["video_id"] == "123"

