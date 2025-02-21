import asyncio
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime
import logging

from app.services.video import VideoProcessor
from app.services.ai import AIService, GeminiService
from app.services.youtube import YouTubeDownloader
from app.models import VideoMetadata, Scene, Transcript
from app.models.schemas import VideoRequest, ProcessingResponse
from app.config import Settings
from app.utils.validators import validate_video_format
from app.utils.formatters import format_timestamp

logger = logging.getLogger(__name__)

class VideoPipeline:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.video_processor = VideoProcessor(settings)
        self.ai_service = AIService(settings)
        self.gemini_service = GeminiService(settings)
        self.youtube_downloader = YouTubeDownloader(settings)
        
    async def process_video(self, request: VideoRequest) -> ProcessingResponse:
        """
        Procesa un video completo pasando por todas las etapas del pipeline.
        """
        try:
            # Iniciar tracking del proceso
            processing_id = self._generate_processing_id()
            started_at = datetime.utcnow()
            
            # Descargar video
            video_path = await self.youtube_downloader.download(
                request.url,
                quality=request.quality
            )
            
            # Validar formato del video
            validate_video_format(video_path)
            
            # Extraer metadata
            metadata = await self.video_processor.extract_metadata(video_path)
            
            # Procesar video en paralelo
            scenes, transcript = await asyncio.gather(
                self.video_processor.detect_scenes(video_path),
                self.video_processor.generate_transcript(
                    video_path,
                    language=request.language
                )
            )
            
            # Enriquecer escenas con IA
            enriched_scenes = await self._enrich_scenes_with_ai(scenes)
            
            # Generar video accesible
            output_path = await self._generate_accessible_version(
                video_path,
                metadata,
                enriched_scenes,
                transcript,
                request.accessibility_options
            )
            
            return ProcessingResponse(
                video_id=processing_id,
                status="completed",
                progress=1.0,
                started_at=started_at,
                estimated_completion=datetime.utcnow(),
                processing_details={
                    "output_path": str(output_path),
                    "metadata": metadata,
                    "scenes_count": len(enriched_scenes),
                    "transcript_length": len(transcript)
                }
            )
            
        except Exception as e:
            logger.error(f"Error processing video: {str(e)}", exc_info=True)
            raise
            
    async def _enrich_scenes_with_ai(self, scenes: List[Scene]) -> List[Scene]:
        """
        Enriquece las escenas con análisis de IA adicional.
        """
        enriched_scenes = []
        for scene in scenes:
            description = await self.gemini_service.generate_scene_description(
                scene.frame_data
            )
            emotion = await self.ai_service.analyze_emotion(scene.frame_data)
            scene.description = description
            scene.emotional_context = emotion
            enriched_scenes.append(scene)
        return enriched_scenes
        
    async def _generate_accessible_version(
        self,
        video_path: Path,
        metadata: VideoMetadata,
        scenes: List[Scene],
        transcript: List[Transcript],
        accessibility_options: Dict[str, bool]
    ) -> Path:
        """
        Genera la versión accesible final del video.
        """
        return await self.video_processor.generate_accessible_video(
            video_path=video_path,
            metadata=metadata,
            scenes=scenes,
            transcript=transcript,
            options=accessibility_options
        )
        
    def _generate_processing_id(self) -> str:
        """
        Genera un ID único para el proceso.
        """
        return f"proc_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"