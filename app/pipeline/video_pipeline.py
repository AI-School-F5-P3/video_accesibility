import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
import time 
import re 

from app.services.video import VideoProcessor
from app.services.ai import AIService, GeminiService
from app.services.youtube.youtube_downloader import YouTubeDownloader
from app.models import VideoMetadata, Scene, Transcript
from app.models.schemas import (
    VideoRequest, 
    ProcessingResponse, 
    VideoConfig,
    ProcessingResult,
    ServiceType,
    ProcessingConfig,
    AIConfig,
    StorageConfig,
    VideoQuality
)
from app.config import Settings
from app.utils.validators import validate_video_format
from app.utils.formatters import format_timestamp
from app.core.error_handler import ProcessingError, ErrorType, ErrorDetails
from ..config.logging_config import setup_logging
from app.core.video_analyzer import VideoAnalyzer
from app.services.audio import AudioProcessor

logger = logging.getLogger(__name__)

class VideoPipeline:
    def __init__(self, config: Dict[str, Any]):
        try:
            logger.info("Inicializando VideoPipeline")
            self.config = VideoConfig.model_validate(config)
            logger.info("Configuración validada exitosamente")
            self._init_components()
        except Exception as e:
            logger.error(f"Error inicializando componentes: {str(e)}")
            raise ProcessingError(
                ErrorType.SYSTEM_ERROR,
                ErrorDetails(
                    component="VideoPipeline",
                    message=f"Error en inicialización: {str(e)}",
                    code="INIT_ERROR"
                )
            )

    def _init_components(self):
        try:
            config_dict = self.config.model_dump()
            self.video_analyzer = VideoAnalyzer(config_dict)
            self.audio_processor = AudioProcessor(config_dict)
            
            # Configuración específica para YouTube
            youtube_config = {
                'download_path': config_dict['download_path'],
                'max_retries': config_dict['max_retries']
            }
            self.youtube_downloader = YouTubeDownloader(youtube_config)
            
            logger.info("Componentes inicializados correctamente")
        except Exception as e:
            logger.error(f"Error inicializando componentes: {str(e)}")
            raise ProcessingError(
                ErrorType.SYSTEM_ERROR,
                ErrorDetails(
                    component="VideoPipeline",
                    message=f"Error en inicialización: {str(e)}",
                    code="INIT_ERROR"
                )
            )

    def _validate_input(self, url: str, service_type: ServiceType) -> None:
        """Valida la entrada antes del procesamiento"""
        if not url:
            raise ProcessingError(
                ErrorType.VALIDATION_ERROR,
                ErrorDetails(
                    component="VideoPipeline",
                    message="URL no puede estar vacía",
                    code="EMPTY_URL"
                )
            )
        
        # Validar formato de URL de YouTube
        youtube_pattern = r'^(https?\:\/\/)?(www\.)?(youtube\.com|youtu\.?be)\/.+$'
        if not re.match(youtube_pattern, url):
            raise ProcessingError(
                ErrorType.VALIDATION_ERROR,
                ErrorDetails(
                    component="VideoPipeline",
                    message="URL debe ser de YouTube",
                    code="INVALID_URL"
                )
            )
        
        # Validar tipo de servicio
        if not isinstance(service_type, ServiceType):
            raise ProcessingError(
                ErrorType.VALIDATION_ERROR,
                ErrorDetails(
                    component="VideoPipeline",
                    message="Tipo de servicio no válido",
                    code="INVALID_SERVICE_TYPE"
                )
            )

    async def process_url(self, url: str, service_type: ServiceType) -> ProcessingResult:
        """Procesa una URL de video"""
        logger.info("Iniciando procesamiento de URL: %s", url)
        start_time = time.time()
        
        try:
            # Validación de entrada
            self._validate_input(url, service_type)
            
            # Procesamiento - Corregido para pasar solo url
            result = await self._process_video(url)
            
            processing_time = time.time() - start_time
            logger.info("Procesamiento completado en %.2f segundos", processing_time)
            
            return result
            
        except Exception as e:
            logger.error("Error procesando URL %s: %s", url, str(e))
            raise

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

    async def _process_video(self, url: str) -> Dict[str, Any]:
        """
        Procesa un video desde una URL
        
        Args:
            url: URL del video a procesar
            
        Returns:
            Dict con resultados del procesamiento
        """
        try:
            logger.info(f"Iniciando procesamiento de video: {url}")
            
            # Descargar video
            video_path = await self.youtube_downloader.download(
                url=url,
                quality=VideoQuality.HIGH  # Ahora VideoQuality está importado correctamente
            )
            
            # Analizar video
            analysis_result = await self.video_analyzer.analyze_video(video_path)
            
            # Procesar audio
            audio_result = await self.audio_processor.process(video_path)
            
            return {
                "video_path": str(video_path),
                "analysis": analysis_result,
                "audio": audio_result
            }
            
        except Exception as e:
            logger.error(f"Error procesando URL {url}: {str(e)}")
            raise ProcessingError(
                ErrorType.PROCESSING_ERROR,
                ErrorDetails(
                    component="VideoPipeline",
                    message=f"Error procesando video: {str(e)}",
                    code="VIDEO_PROCESSING_ERROR"
                )
            )