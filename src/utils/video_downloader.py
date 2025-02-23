import yt_dlp
import logging
from pathlib import Path
from typing import Optional

class VideoDownloader:
    """
    Maneja la descarga de videos desde diferentes fuentes online.
    Soporta URLs de YouTube y otras plataformas compatibles con yt-dlp.
    """
    def __init__(self, download_path: str):
        """
        Inicializa el descargador de videos.
        
        Args:
            download_path: Directorio donde se guardarán los videos descargados
        """
        self.download_path = Path(download_path)
        self.download_path.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)

    def download_video(self, url: str) -> Optional[str]:
        """
        Descarga un video desde una URL.
        
        Args:
            url: URL del video a descargar
            
        Returns:
            str: Ruta al archivo de video descargado, o None si falla
        """
        try:
            # Configuramos las opciones de descarga
            ydl_opts = {
                'format': 'best[ext=mp4]',  # Preferimos formato MP4
                'outtmpl': str(self.download_path / '%(title)s.%(ext)s'),
                'quiet': True,
                'no_warnings': True
            }

            # Descargamos el video
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.logger.info(f"Iniciando descarga desde: {url}")
                info = ydl.extract_info(url, download=True)
                video_path = self.download_path / f"{info['title']}.{info['ext']}"
                
                self.logger.info(f"Video descargado exitosamente: {video_path}")
                return str(video_path)

        except Exception as e:
            self.logger.error(f"Error al descargar el video: {str(e)}")
            return None

    def clean_up(self, video_path: str) -> bool:
        """
        Elimina un video descargado para liberar espacio.
        
        Args:
            video_path: Ruta al archivo de video a eliminar
            
        Returns:
            bool: True si se eliminó correctamente
        """
        try:
            Path(video_path).unlink()
            self.logger.info(f"Video eliminado: {video_path}")
            return True
        except Exception as e:
            self.logger.error(f"Error al eliminar el video: {str(e)}")
            return False