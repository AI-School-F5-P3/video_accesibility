import pytest
from app.services.youtube.youtube_downloader import YouTubeDownloader

@pytest.mark.asyncio
async def test_youtube_download():
    config = {
        "download_path": "./downloads",
        "max_retries": 3
    }
    downloader = YouTubeDownloader(config)
    
    # URL de prueba (video público)
    url = "https://www.youtube.com/watch?v=JYJqu3nI0Zk"
    
    result = await downloader.download(url)
    assert result.exists()