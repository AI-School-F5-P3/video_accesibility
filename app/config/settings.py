from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Any, Optional
import logging
from pathlib import Path
import os
from dotenv import load_dotenv
import json

load_dotenv()

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Configuración global de la aplicación"""
    # Google Cloud Settings
    GOOGLE_APPLICATION_CREDENTIALS: str
    GOOGLE_CLOUD_PROJECT: str = "videoaccesibility"
    VERTEX_LOCATION: str = "us-central1"
    
    # YouTube Settings
    YOUTUBE_API_KEY: str
    YOUTUBE_OAUTH_CLIENT_ID: Optional[str] = None
    YOUTUBE_OAUTH_CLIENT_SECRET: Optional[str] = None
    YOUTUBE_OAUTH_REDIRECT_URI: Optional[str] = None
    
    # Storage Settings
    STORAGE_BUCKET: str = "video-accessibility-bucket"
    TEMP_STORAGE_PATH: Path = Path("./temp")
    OUTPUT_STORAGE_PATH: Path = Path("./output/processed")
    CACHE_DIR: Path = Path("./cache")
    DOWNLOAD_PATH: Path = Path("./downloads")
    
    # Processing Settings
    MAX_VIDEO_DURATION: int = 3600
    SUPPORTED_FORMATS: str = "mp4,mp3,srt,vtt"
    MAX_RETRIES: int = 3
    MAX_MEMORY_PERCENT: int = 80
    MAX_CONCURRENT_TASKS: int = 3
    
    # Video Analysis Settings
    SCENE_DETECTION_THRESHOLD: float = 0.3
    MIN_SCENE_DURATION: float = 2.0
    MIN_SILENCE_LEN: int = 1000
    SILENCE_THRESH: int = -40
    
    # Testing Settings
    TEST_VIDEO_PATH: Optional[Path] = Path("tests/resources/test_video.mp4")
    
    # AI Settings
    BATCH_SIZE: int = 32
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1024
    DEFAULT_LANGUAGE: str = "es"
    
    # Logging Settings
    LOG_PATH: Path = Path("./logs")
    LOG_LEVEL: str = "INFO"
    
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        use_enum_values=True,
        extra='ignore'  # Permite campos extra en el .env
    )
    
    def get_credentials_dict(self) -> Dict[str, Any]:
        """Obtiene las credenciales como diccionario"""
        creds_path = Path(self.GOOGLE_APPLICATION_CREDENTIALS)
        if not creds_path.exists():
            raise FileNotFoundError(f"Archivo de credenciales no encontrado: {creds_path}")
            
        with open(creds_path) as f:
            return json.load(f)

    def get_config(self) -> Dict[str, Any]:
        """
        Obtiene la configuración como diccionario para el pipeline
        """
        return {
            "batch_size": self.BATCH_SIZE,
            "max_retries": self.MAX_RETRIES,
            "max_concurrent_tasks": self.MAX_CONCURRENT_TASKS,
            "max_memory_percent": self.MAX_MEMORY_PERCENT,
            "temperature": self.TEMPERATURE,
            "max_tokens": self.MAX_TOKENS,
            "language": self.DEFAULT_LANGUAGE,
            "storage_bucket": self.STORAGE_BUCKET,
            "temp_storage_path": str(self.TEMP_STORAGE_PATH),
            "output_storage_path": str(self.OUTPUT_STORAGE_PATH),
            "cache_dir": str(self.CACHE_DIR),
            "max_video_duration": self.MAX_VIDEO_DURATION,
            "scene_detection_threshold": float(self.SCENE_DETECTION_THRESHOLD),
            "min_scene_duration": float(self.MIN_SCENE_DURATION),
            "download_path": str(self.DOWNLOAD_PATH),
            "youtube_api_key": self.YOUTUBE_API_KEY,
            "youtube_oauth_client_id": self.YOUTUBE_OAUTH_CLIENT_ID,
            "youtube_oauth_client_secret": self.YOUTUBE_OAUTH_CLIENT_SECRET,
        }

    def get_youtube_config(self) -> Dict[str, Any]:
        """Obtiene la configuración específica de YouTube"""
        return {
            "api_key": self.YOUTUBE_API_KEY,
            "download_path": str(self.DOWNLOAD_PATH),
            "max_retries": self.MAX_RETRIES
        }

settings = Settings()