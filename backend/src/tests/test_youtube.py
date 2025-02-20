import pytest
from pathlib import Path
from ..services.youtube.youtube_service import YouTubeService

@pytest.fixture
def youtube_service():
    service = YouTubeService()
    yield service
    service.cleanup()

async def test_get_video_info(youtube_service):
    url = 'https://www.youtube.com/watch?v=JYJqu3nI0Zk'
    info = await youtube_service.get_video_info(url)
    
    assert info['title']
    assert info['length_seconds'] > 0
    assert info['author']['name']
    assert info['video_id']

async def test_download_video(youtube_service):
    url = 'https://www.youtube.com/watch?v=JYJqu3nI0Zk'
    file_path = await youtube_service.download_video(url)
    
    assert Path(file_path).exists()
    assert Path(file_path).stat().st_size > 0