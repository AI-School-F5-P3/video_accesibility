from pathlib import Path
from typing import Optional, Dict, Any
import logging
from pytube import YouTube
from pytube.exceptions import PytubeError
from app.config import Settings
from app.models.schemas import VideoQuality
import re
import time
from urllib.parse import parse_qs, urlparse

logger = logging.getLogger(__name__)

class YouTubeDownloader:
    def __init__(self, config: Dict[str, Any]):
        """
        Args:
            config: Diccionario de configuración
                - download_path: Ruta de descarga
                - max_retries: Número máximo de reintentos
        """
        self.download_path = config['download_path']
        self.max_retries = config.get('max_retries', 3)
        self.output_path = Path(self.download_path)
        self.output_path.mkdir(parents=True, exist_ok=True)
        self.retry_delay = 2  # Aumentado el delay entre intentos
        
    async def download(
        self, 
        url: str, 
        quality: VideoQuality = VideoQuality.HIGH
    ) -> Path:
        """Descarga un video usando múltiples estrategias"""
        video_id = self._extract_video_id(url)
        logger.info(f"Iniciando descarga del video: {video_id}")

        for attempt in range(self.max_retries):
            try:
                # Removidos los argumentos que causaban el error
                yt = YouTube(
                    url,
                    on_progress_callback=self._on_progress
                )

                # Intentar obtener información del video
                logger.debug(f"Obteniendo información del video... (Intento {attempt + 1})")
                
                # Forzar la obtención de streams para validar disponibilidad
                streams = yt.streams.filter(progressive=True, file_extension='mp4')
                logger.debug(f"Streams disponibles: {len(streams)}")

                if not streams:
                    raise ValueError("No se encontraron streams disponibles")

                stream = streams.order_by('resolution').desc().first()
                logger.info(f"Stream seleccionado: {stream.resolution}")

                output_file = self.output_path / f"{video_id}.mp4"
                logger.info(f"Descargando a: {output_file}")
                
                stream.download(
                    output_path=str(self.output_path),
                    filename=f"{video_id}.mp4"
                )

                if output_file.exists():
                    return output_file
                    
            except Exception as e:
                logger.error(f"Error en intento {attempt + 1}: {str(e)}")
                if attempt < self.max_retries - 1:
                    logger.info(f"Esperando {self.retry_delay} segundos...")
                    time.sleep(self.retry_delay)
                continue

        raise ValueError(f"No se pudo descargar el video después de {self.max_retries} intentos")

    def _extract_video_id(self, url: str) -> str:
        """Extrae el ID del video de la URL"""
        if match := re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11}).*', url):
            return match.group(1)
        
        # Alternativa: parsear la URL
        query = parse_qs(urlparse(url).query)
        if 'v' in query:
            return query['v'][0]
            
        raise ValueError("URL de YouTube inválida")

    def _on_progress(self, stream, chunk: bytes, bytes_remaining: int):
        """Callback para el progreso de la descarga"""
        try:
            total_size = stream.filesize
            bytes_downloaded = total_size - bytes_remaining
            percentage = (bytes_downloaded / total_size) * 100
            logger.info(f"Progreso de descarga: {percentage:.1f}%")
        except Exception as e:
            logger.error(f"Error en callback de progreso: {str(e)}")