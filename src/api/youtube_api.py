from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from pytube import YouTube
from typing import Dict, Any
import logging
import os

class YouTubeAPI:
    """Clase para manejar interacciones con YouTube API V3"""
    def __init__(self, api_key: str):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=api_key)

    def download_video(self, url: str) -> Dict[str, Any]:
        """Descarga video de YouTube"""
        try:
            yt = YouTube(url)
            output_path = os.path.join('temp')
            os.makedirs(output_path, exist_ok=True)
            
            video = yt.streams.filter(
                progressive=True, 
                file_extension='mp4'
            ).order_by('resolution').desc().first()
            
            if not video:
                raise ValueError("No se encontró un stream de video válido")
                
            video_path = video.download(output_path=output_path)
            
            return {
                'video_path': video_path,
                'metadata': {
                    'title': yt.title,
                    'duration': yt.length,
                    'author': yt.author
                }
            }
        except Exception as e:
            self.logger.error(f"Error downloading video: {str(e)}")
            raise

    def _extract_video_id(self, url: str) -> str:
        """Extrae el ID del video de la URL"""
        if "watch?v=" in url:
            return url.split("watch?v=")[1].split("&")[0]
        raise ValueError("URL de YouTube no válida")

def test_youtube_api():
    try:
        youtube = build('youtube', 'v3', 
                       developerKey=os.getenv('YOUTUBE_API_KEY'))
        request = youtube.videos().list(
            part="snippet",
            id="M7lc1UVf-VE"  # ID de video de prueba
        )
        response = request.execute()
        print("✅ YouTube API configurada correctamente")
        return True
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    test_youtube_api()