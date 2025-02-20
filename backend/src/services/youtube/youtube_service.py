from pytube import YouTube
from pathlib import Path
import logging
from typing import Dict, Any
import os

class YouTubeService:
    def __init__(self, base_path: str = None):
        self.download_path = Path(base_path or os.getcwd()) / 'temp'
        self._setup_logging()
        self._ensure_directory_exists()
    
    def _setup_logging(self) -> None:
        self.logger = logging.getLogger(__name__)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    def _ensure_directory_exists(self) -> None:
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"Directorio de trabajo: {self.download_path}")

    async def get_video_info(self, url: str) -> Dict[str, Any]:
        try:
            yt = YouTube(url)
            return {
                'title': yt.title,
                'length_seconds': yt.length,
                'author': {'name': yt.author},
                'video_id': yt.video_id
            }
        except Exception as e:
            self.logger.error(f"Error al obtener info: {str(e)}")
            raise

    async def download_video(self, url: str) -> str:
        try:
            yt = YouTube(url, on_progress_callback=self._on_progress)
            stream = (yt.streams
                     .filter(progressive=True, file_extension='mp4')
                     .get_highest_resolution())
            
            if not stream:
                raise ValueError("No se encontró stream válido")

            output_path = stream.download(output_path=str(self.download_path))
            self.logger.info(f"Video descargado: {output_path}")
            return output_path

        except Exception as e:
            self.logger.error(f"Error en descarga: {str(e)}")
            raise

    def _on_progress(self, stream, chunk: bytes, bytes_remaining: int) -> None:
        total = stream.filesize
        downloaded = total - bytes_remaining
        percent = (downloaded / total) * 100
        self.logger.info(f"Descarga: {percent:.1f}%")

    def cleanup(self) -> None:
        try:
            for file in self.download_path.glob('*'):
                file.unlink()
            self.logger.info("Limpieza completada")
        except Exception as e:
            self.logger.error(f"Error en limpieza: {str(e)}")