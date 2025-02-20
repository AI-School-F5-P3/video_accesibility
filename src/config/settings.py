from pathlib import Path
from typing import Dict, Any
import os
from .une_config import UNE153010Config, UNE153020Config
from .ai_studio_config import AIStudioConfig
from dotenv import load_dotenv

class Settings:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.resources_dir = self.project_root / "resources"
        self.output_dir = self.project_root / "output"
        
        # Crear directorios necesarios
        self.output_dir.mkdir(parents=True, exist_ok=True)
        (self.output_dir / "temp").mkdir(exist_ok=True)
        
        # Añadir nuevas configuraciones
        self.processed_dir = self.output_dir / "processed"
        
        # Asegurar directorios
        for dir_path in [self.output_dir, self.output_dir / "temp", self.processed_dir]:
            dir_path.mkdir(exist_ok=True)
        
    def get_config(self) -> Dict[str, Any]:
        """Retorna la configuración completa"""
        return {
            'youtube_api_key': os.getenv('YOUTUBE_API_KEY'),
            'output_dir': str(self.output_dir),
            'subtitle_config': UNE153010Config(),
            'audio_config': UNE153020Config(),
            'ai_config': AIStudioConfig.get_config(),
            'google_cloud_config': {
                'PROJECT_ID': os.getenv('GOOGLE_CLOUD_PROJECT'),
                'API_KEY': os.getenv('GOOGLE_API_KEY'),
                'CREDENTIALS_PATH': self.project_root / 'credentials' / 'client_secret.json',
                'VISION_AI': {
                    'CONFIDENCE_THRESHOLD': 0.8,
                    'MAX_RESULTS': 50
                },
                'VERTEX_AI': {
                    'REGION': 'us-central1',
                    'MODEL_NAME': 'text-bison@001'
                }
            },
            'processing_config': {
                'MAX_RETRIES': 3,
                'BATCH_SIZE': 10,
                'SUPPORTED_FORMATS': ['mp4', 'mp3', 'srt', 'vtt'],
                'MAX_VIDEO_DURATION': 3600,
                'QUEUE_TIMEOUT': 300
            }
        }