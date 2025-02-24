import cv2
from pathlib import Path
import logging
import re
from fastapi import UploadFile

class VideoValidator:
    def __init__(self, settings):
        self.settings = settings
        
    def validate_video(self, video_path: Path) -> tuple[bool, str]:
        try:
            if not video_path.exists():
                return False, "Video file does not exist"

            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return False, "Cannot open video file"

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            
            cap.release()

            if duration > self.settings.MAX_VIDEO_DURATION:
                return False, "Video is too long. Maximum duration is 10 minutes"

            return True, "Valid video"
            
        except Exception as e:
            return False, f"Error validating video: {str(e)}"

def validate_video_file(file: UploadFile) -> bool:
    """
    Valida que el archivo subido sea un video en un formato aceptado
    
    Args:
        file: Archivo subido a través de FastAPI
        
    Returns:
        bool: True si el archivo es válido, False en caso contrario
    """
    # Validar tipo MIME
    valid_mimes = [
        'video/mp4', 
        'video/avi', 
        'video/quicktime', 
        'video/x-msvideo',
        'video/x-matroska',
        'video/webm'
    ]
    
    # Validar extensión
    valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    
    if file.content_type not in valid_mimes:
        logging.warning(f"Tipo MIME no válido: {file.content_type}")
        # Como fallback, validar por extensión
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in valid_extensions:
            logging.error(f"Extensión no válida: {file_ext}")
            return False
    
    return True

def validate_youtube_url(url: str) -> bool:
    """
    Valida que la URL corresponda a un video de YouTube
    
    Args:
        url: URL a validar
        
    Returns:
        bool: True si la URL es válida, False en caso contrario
    """
    youtube_regex = r'^((?:https?:)?\/\/)?((?:www|m)\.)?((?:youtube(-nocookie)?\.com|youtu.be))(\/(?:[\w\-]+\?v=|embed\/|live\/|v\/)?)([\w\-]+)(\S+)?$'
    return bool(re.match(youtube_regex, url))

def validate_silence_intervals(intervals: list) -> bool:
    """
    Valida que los intervalos de silencio sean adecuados para audiodescripción
    
    Args:
        intervals: Lista de intervalos (inicio, fin) en milisegundos
        
    Returns:
        bool: True si hay intervalos válidos, False en caso contrario
    """
    if not intervals:
        return False
    
    # Validar que hay al menos un intervalo lo suficientemente largo
    # (mínimo 1 segundo para una descripción corta)
    min_length_ms = 1000 
    
    for start, end in intervals:
        if (end - start) >= min_length_ms:
            return True
    
    return False