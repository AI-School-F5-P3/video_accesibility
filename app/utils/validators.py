from typing import Optional, Dict, Any, List
from pathlib import Path
import cv2
from app.config import Settings

def validate_video_format(video_path: Path) -> bool:
    """Valida formato de video"""
    allowed_extensions = ['.mp4', '.avi', '.mkv']
    
    if video_path.suffix.lower() not in allowed_extensions:
        raise ValueError(f"Formato de video no soportado. Permitidos: {allowed_extensions}")
    
    if not video_path.exists():
        raise ValueError(f"El archivo no existe: {video_path}")
    
    try:
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError("No se puede abrir el archivo de video")
        cap.release()
        return True
    except Exception as e:
        raise ValueError(f"Error validando video: {str(e)}")

def validate_subtitle_text(text: str, max_chars: int = 37) -> bool:
    """Valida el texto del subtítulo según norma UNE"""
    if not text or len(text) > max_chars:
        return False
    return True

def validate_audio_description(
    description: str,
    duration: float,
    settings: Optional[Settings] = None
) -> bool:
    """
    Valida una descripción de audio según normas UNE
    """
    if not settings:
        settings = Settings()
        
    # Palabras por minuto según norma UNE
    MAX_WPM = 180
    words = len(description.split())
    minutes = duration / 60
    
    wpm = words / minutes if minutes > 0 else float('inf')
    return wpm <= MAX_WPM

def validate_pipeline_config(config: Dict[str, Any]) -> bool:
    """Valida la configuración del pipeline"""
    required_keys = [
        'input_path',
        'output_path',
        'language',
        'generate_subtitles',
        'generate_audio_description'
    ]
    
    return all(key in config for key in required_keys)