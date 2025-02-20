from typing import Dict, Any

class YouTubeAPIMock:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def download_video(self, url: str) -> Dict[str, Any]:
        return {
            'video_path': 'tests/resources/test_video.mp4',
            'metadata': {
                'title': 'Test Video',
                'duration': 10,
                'author': 'Test Author'
            }
        }