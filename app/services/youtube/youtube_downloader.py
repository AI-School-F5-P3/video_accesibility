from pathlib import Path
from typing import Optional
import logging
from pytube import YouTube
from app.config import Settings
from app.models.schemas import VideoQuality

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.output_path = Path(settings.DOWNLOAD_PATH)
        self.output_path.mkdir(parents=True, exist_ok=True)
        
    async def download(
        self, 
        url: str, 
        quality: VideoQuality = VideoQuality.HIGH
    ) -> Path:
        """Descarga un video de YouTube con la calidad especificada"""
        try:
            yt = YouTube(url)
            # Seleccionar stream según calidad
            stream = self._get_stream_by_quality(yt, quality)
            
            # Descargar video
            logger.info(f"Iniciando descarga de: {yt.title}")
            output_file = stream.download(
                output_path=str(self.output_path),
                filename=f"{yt.video_id}_{quality}.mp4"
            )
            
            logger.info(f"Video descargado: {output_file}")
            return Path(output_file)
            
        except Exception as e:
            logger.error(f"Error downloading video: {str(e)}")
            raise
            
    def _get_stream_by_quality(
        self, 
        yt: YouTube, 
        quality: VideoQuality
    ) -> "pytube.Stream":  # Corrección aquí - tipo específico
        """Selecciona el stream apropiado según la calidad solicitada"""
        quality_map = {
            VideoQuality.LOW: "360p",
            VideoQuality.MEDIUM: "720p",
            VideoQuality.HIGH: "1080p",
            VideoQuality.ULTRA: "2160p"
        }
        
        try:
            streams = yt.streams.filter(
                progressive=True, 
                file_extension='mp4'
            )
            
            if not streams:
                raise ValueError("No se encontraron streams disponibles")

            # Intentar obtener la calidad solicitada
            stream = streams.filter(
                resolution=quality_map[quality]
            ).first()
            
            # Si no está disponible, obtener la mejor calidad disponible
            if not stream:
                self.logger.warning(
                    f"Calidad {quality} no disponible. "
                    "Seleccionando mejor calidad disponible."
                )
                stream = streams.get_highest_resolution()
                
            if not stream:
                raise ValueError("No se pudo encontrar un stream válido")
                
            return stream
            
        except Exception as e:
            self.logger.error(f"Error seleccionando stream: {str(e)}")
            raise