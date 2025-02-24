from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Any
import logging
from pathlib import Path
from ..models.schemas import ProcessingConfig, AIConfig, StorageConfig, VideoConfig
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """Configuración global de la aplicación"""
    # Formatos soportados
    SUPPORTED_FORMATS: str = "mp4,mp3,srt,vtt"
    
    # Atributos de configuración
    GOOGLE_APPLICATION_CREDENTIALS: str
    GOOGLE_CLOUD_PROJECT: str
    VERTEX_LOCATION: str = "us-central1"
    YOUTUBE_API_KEY: str

    BATCH_SIZE: int = 32
    MAX_RETRIES: int = 3
    MAX_CONCURRENT_TASKS: int = 3
    MAX_MEMORY_PERCENT: int = 80
    TEMPERATURE: float = 0.7
    MAX_TOKENS: int = 1024
    DEFAULT_LANGUAGE: str = "es"
    STORAGE_BUCKET: str = "video-accessibility-bucket"
    TEMP_STORAGE_PATH: str = "./temp"
    OUTPUT_STORAGE_PATH: str = "./output/processed"
    CACHE_DIR: str = "./cache"
    MAX_VIDEO_DURATION: int = 3600
    SCENE_DETECTION_THRESHOLD: float = 0.3
    MIN_SCENE_DURATION: float = 2.0

    # Audio Processing
    MIN_SILENCE_LEN: int = 1000
    SILENCE_THRESH: int = -40

    # Testing
    TEST_VIDEO_PATH: str = "tests/resources/test_video.mp4"

    # Logging
    LOG_LEVEL: str = "info"
    LOG_PATH: str = "./logs"

    def get_config(self) -> Dict[str, Any]:
        """Obtiene la configuración en formato diccionario"""
        return {
            'batch_size': self.BATCH_SIZE,
            'max_retries': self.MAX_RETRIES,
            'max_concurrent_tasks': self.MAX_CONCURRENT_TASKS,
            'max_memory_percent': self.MAX_MEMORY_PERCENT,
            'temperature': self.TEMPERATURE,
            'max_tokens': self.MAX_TOKENS,
            'language': self.DEFAULT_LANGUAGE,
            'storage_bucket': self.STORAGE_BUCKET,
            'temp_storage_path': self.TEMP_STORAGE_PATH,
            'output_storage_path': self.OUTPUT_STORAGE_PATH,
            'cache_dir': self.CACHE_DIR,
            'max_video_duration': self.MAX_VIDEO_DURATION,
            'scene_detection_threshold': self.SCENE_DETECTION_THRESHOLD,
            'min_scene_duration': self.MIN_SCENE_DURATION
        }

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='allow'
    )