from pathlib import Path
import logging
import json
import shutil
from typing import Dict, List, Any, Optional

def get_root_directory() -> Path:
    """Get the root directory of the project."""
    return Path(__file__).parent.parent.parent

def setup_directories() -> Dict[str, Path]:
    """
    Create and return all necessary project directories.
    
    Returns:
        Dict[str, Path]: Dictionary containing all project directory paths
    """
    root_dir = get_root_directory()
    
    directories = {
        'data': root_dir / 'data',
        'raw': root_dir / 'data' / 'raw',
        'processed': root_dir / 'data' / 'processed',
        'transcripts': root_dir / 'data' / 'transcripts',
        'audio': root_dir / 'data' / 'audio',
        'temp': root_dir / 'data' / 'temp'
    }
    
    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {dir_path}")
    
    return directories

# --- Nuevas funciones para trabajar con la estructura de directorios por video ID ---

def ensure_video_directories(video_id: str) -> Dict[str, Path]:
    """
    Crea y devuelve las rutas de directorios específicas para un video.
    
    Args:
        video_id: ID único del video (UUID)
        
    Returns:
        Dict[str, Path]: Diccionario con las rutas específicas para este video
    """
    directories = setup_directories()
    
    video_dirs = {
        'raw_video': directories['raw'] / video_id,
        'processed_video': directories['processed'] / video_id,
        'frames': directories['processed'] / video_id,
        'audio_video': directories['audio'] / video_id,
        'transcripts_video': directories['transcripts'] / video_id
    }
    
    for dir_path in video_dirs.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created video directory: {dir_path}")
    
    return video_dirs

def get_video_path(video_id: str) -> Path:
    """
    Obtiene la ruta al archivo de video original.
    
    Args:
        video_id: ID único del video
        
    Returns:
        Path: Ruta al archivo de video
    """
    root_dir = get_root_directory()
    return root_dir / 'data' / 'raw' / video_id / f"{video_id}.mp4"

def get_frame_path(video_id: str, frame_number: int) -> Path:
    """
    Obtiene la ruta a un frame específico.
    
    Args:
        video_id: ID único del video
        frame_number: Número del frame
        
    Returns:
        Path: Ruta al archivo de imagen del frame
    """
    root_dir = get_root_directory()
    return root_dir / 'data' / 'processed' / video_id / f"frame_{frame_number}.jpg"

def get_audio_desc_path(video_id: str, desc_number: int) -> Path:
    """
    Obtiene la ruta a un archivo de audiodescripción.
    
    Args:
        video_id: ID único del video
        desc_number: Número de la descripción
        
    Returns:
        Path: Ruta al archivo de audio
    """
    root_dir = get_root_directory()
    return root_dir / 'data' / 'audio' / f"{video_id}_desc_{desc_number}.mp3"

def get_full_audio_desc_path(video_id: str) -> Path:
    """
    Obtiene la ruta al archivo de audiodescripción completo.
    
    Args:
        video_id: ID único del video
        
    Returns:
        Path: Ruta al archivo de audio completo
    """
    root_dir = get_root_directory()
    return root_dir / 'data' / 'audio' / f"{video_id}_described.mp3"

def get_subtitle_path(video_id: str) -> Path:
    """
    Obtiene la ruta al archivo de subtítulos.
    
    Args:
        video_id: ID único del video
        
    Returns:
        Path: Ruta al archivo SRT
    """
    root_dir = get_root_directory()
    return root_dir / 'data' / 'transcripts' / f"{video_id}_srt.srt"

def get_descriptions_json_path(video_id: str) -> Path:
    """
    Obtiene la ruta al archivo JSON de descripciones.
    
    Args:
        video_id: ID único del video
        
    Returns:
        Path: Ruta al archivo JSON
    """
    root_dir = get_root_directory()
    return root_dir / 'data' / 'processed' / video_id / "descriptions.json"

def save_descriptions_json(video_id: str, descriptions: List[Dict[str, Any]]) -> Path:
    """
    Guarda las descripciones en un archivo JSON.
    
    Args:
        video_id: ID único del video
        descriptions: Lista de descripciones a guardar
        
    Returns:
        Path: Ruta al archivo JSON guardado
    """
    json_path = get_descriptions_json_path(video_id)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(descriptions, f, ensure_ascii=False, indent=2)
    return json_path

def load_descriptions_json(video_id: str) -> List[Dict[str, Any]]:
    """
    Carga las descripciones desde un archivo JSON.
    
    Args:
        video_id: ID único del video
        
    Returns:
        List[Dict[str, Any]]: Lista de descripciones
    """
    json_path = get_descriptions_json_path(video_id)
    if json_path.exists():
        with open(json_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def copy_video_to_raw(source_path: str, video_id: str) -> Path:
    """
    Copia un video al directorio raw con el ID correcto.
    
    Args:
        source_path: Ruta de origen del archivo de video
        video_id: ID único para asignar al video
        
    Returns:
        Path: Ruta de destino del archivo copiado
    """
    directories = setup_directories()
    dest_dir = directories['raw'] / video_id
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    dest_path = dest_dir / f"{video_id}.mp4"
    shutil.copy2(source_path, dest_path)
    
    return dest_path

def get_processed_video_path(video_id: str) -> Path:
    """
    Obtiene la ruta al video procesado con audiodescripción.
    
    Args:
        video_id: ID único del video
        
    Returns:
        Path: Ruta al archivo de video procesado
    """
    root_dir = get_root_directory()
    return root_dir / 'data' / 'processed' / f"{video_id}_with_audiodesc.mp4"