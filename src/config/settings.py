from pydantic_settings import BaseSettings
from typing import Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    # API settings
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Video Accessibility API"
    VERSION: str = "1.0.0"
    
    # File settings
    UPLOAD_DIR: str = str(Path("data/uploads").absolute())
    OUTPUT_DIR: str = str(Path("data/output").absolute())
    MAX_UPLOAD_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_VIDEO_EXTENSIONS: set = {".mp4", ".avi", ".mov", ".mkv"}
    
    # Video processing settings
    FRAME_INTERVAL: int = 3  # seconds between frames for analysis
    SILENCE_THRESHOLD: float = -40.0  # dB
    MIN_SILENCE_DURATION: float = 1.0  # seconds
    
    # API Keys and external services
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")
    AZURE_SPEECH_KEY: Optional[str] = os.getenv("AZURE_SPEECH_KEY")
    AZURE_SPEECH_REGION: Optional[str] = os.getenv("AZURE_SPEECH_REGION")
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Create upload and output directories if they don't exist
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.OUTPUT_DIR, exist_ok=True)

settings = Settings()