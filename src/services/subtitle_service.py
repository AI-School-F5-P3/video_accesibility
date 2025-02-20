from src.config import UNE153010Config
from typing import Dict, Any
import logging

class SubtitleService:
    def __init__(self):
        self.config = UNE153010Config()
        self.logger = logging.getLogger(__name__)

    async def generate_subtitles(self, video_path: str) -> Dict[str, str]:
        """Genera subtítulos según UNE 153010"""
        try:
            # Transcribir audio
            transcription = await self._transcribe_audio(video_path)
            
            # Formatear según UNE 153010
            subtitles = self._format_subtitles(transcription)
            
            # Generar archivos
            vtt_path = self._generate_vtt(subtitles)
            mp4_path = self._embed_subtitles(video_path, vtt_path)
            
            return {
                'video': mp4_path,
                'subtitles': vtt_path
            }
            
        except Exception as e:
            self.logger.error(f"Error generando subtítulos: {str(e)}")
            raise