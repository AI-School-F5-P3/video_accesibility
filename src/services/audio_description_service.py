from src.config import UNE153020Config
from stable_ts import Pipeline
import logging

class AudioDescriptionService:
    """Servicio para generar audiodescripciones según UNE 153020"""
    def __init__(self):
        self.config = UNE153020Config()
        self.pipeline = Pipeline()
        self.logger = logging.getLogger(__name__)

    async def process_video(self, video_path: str) -> Dict[str, str]:
        try:
            result = await self._analyze_video(video_path)
            return await self._generate_audio_description(result)
        except Exception as e:
            self.logger.error(f"Error en audiodescripción: {str(e)}")
            raise