import os
from pathlib import Path
from dotenv import load_dotenv

class Settings:
    def __init__(self):
        load_dotenv()
        
        # Base directories
        self.BASE_DIR = Path(__file__).resolve().parent.parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.OUTPUT_DIR = self.BASE_DIR / "output"
        
        # Data subdirectories
        self.RAW_DIR = self.DATA_DIR / "raw"
        self.PROCESSED_DIR = self.DATA_DIR / "processed"
        self.TRANSCRIPTS_DIR = self.DATA_DIR / "transcripts"
        self.AUDIO_DIR = self.DATA_DIR / "audio"
        
        # Create all directories
        for directory in [self.RAW_DIR, self.PROCESSED_DIR, 
                         self.TRANSCRIPTS_DIR, self.AUDIO_DIR, 
                         self.OUTPUT_DIR]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # API keys and configurations
        self.GOOGLE_AI_STUDIO_API_KEY = os.getenv('GOOGLE_AI_STUDIO_API_KEY')
        self.LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'es-ES')
        self.VOICE_NAME = os.getenv('VOICE_NAME', 'es-ES-Wavenet-C')
        
        # Model configurations
        self.WHISPER_MODEL = "medium"
        self.MIN_SILENCE_LENGTH = 3000  # milliseconds
        self.MAX_VIDEO_DURATION = 600  # seconds