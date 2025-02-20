from src.config import UNE153020Config
from stable_ts import Pipeline
import logging

class AudioDescriptionService:
    def __init__(self):
        self.config = UNE153020Config()
        self.pipeline = Pipeline()
        self.logger = logging.getLogger(__name__)

    async def process_video(self, video_path: str) -> Dict[str, str]:
        """Procesa video para audiodescripción según UNE 153020"""
        try:
            # Analizar video con stable-ts
            result = self.pipeline.transcribe(
                video_path,
                vad_filter=True,
                word_timestamps=True
            )

            # Detectar escenas importantes
            scenes = self._detect_scenes(result)
            
            if scenes:
                # Usar Vertex AI
                return await self._process_with_vertex(video_path, scenes)
            else:
                # Usar Google AI Studio
                return await self._process_with_ai_studio(video_path)
                
        except Exception as e:
            self.logger.error(f"Error en audiodescripción: {str(e)}")
            raise