from typing import Dict, Any, Optional, List
from pathlib import Path
import cv2
import numpy as np
from ...config.settings import Settings
from ...core.error_handler import ProcessingError, ErrorType, ErrorDetails
import logging
import torch
import whisper
from stable_whisper import modify_model
from app.models import VideoMetadata, Scene, Transcript
from app.utils.validators import validate_video_format

logger = logging.getLogger(__name__)

class Settings:
    def __init__(self):
        self.SCENE_DETECTION_THRESHOLD = 0.3  # Valor por defecto
        # ...existing code...

    def get_config(self) -> Dict[str, Any]:
        return {
            # ...existing code...
            'video_config': {
                'SCENE_DETECTION_THRESHOLD': self.SCENE_DETECTION_THRESHOLD,
                'MIN_SCENE_DURATION': 2.0,
                'MAX_SCENES': 100
            },
            # ...existing code...
        }

class VideoProcessor:
    """Procesador principal de video para análisis y transcripción"""

    def __init__(self, settings: Dict[str, Any]):
        """
        Inicializa el procesador de video
        
        Args:
            settings: Configuración del procesador
            
        Raises:
            ValueError: Si la configuración es inválida
        """
        if not isinstance(settings, dict):
            raise ValueError("Settings debe ser un diccionario")
        
        self.settings = settings
        self._configure_processing_parameters()
        self._initialize_whisper()
        logger.info("VideoProcessor inicializado correctamente")

    def _configure_processing_parameters(self) -> None:
        """Configura parámetros de procesamiento"""
        video_config = self.settings.get('video_config', {})
        self.scene_threshold = video_config.get('SCENE_DETECTION_THRESHOLD', 0.3)
        self.frame_sample_rate = video_config.get('FRAME_SAMPLE_RATE', 1)
        self.min_scene_duration = video_config.get('MIN_SCENE_DURATION', 2.0)
        self.output_dir = Path(self.settings.get('output_dir', 'output'))
        self.output_dir.mkdir(exist_ok=True)

    def _initialize_whisper(self) -> None:
        """Inicializa el modelo Whisper"""
        try:
            base_model = whisper.load_model("base")
            self.whisper_model = modify_model(base_model)
            logger.info("Modelo Whisper inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando Whisper: {str(e)}")
            raise RuntimeError(f"No se pudo inicializar Whisper: {str(e)}")

    async def process_video(self, video_path: Path) -> VideoMetadata:
        """
        Procesa un video completo
        
        Args:
            video_path: Ruta al archivo de video
            
        Returns:
            VideoMetadata: Metadata del video procesado
        """
        try:
            validate_video_format(video_path)
            metadata = await self._extract_metadata(video_path)
            scenes = await self._detect_scenes(video_path)
            transcription = await self._transcribe_audio(video_path)
            
            return VideoMetadata(
                path=video_path,
                duration=metadata['duration'],
                fps=metadata['fps'],
                resolution=metadata['resolution'],
                scenes=scenes,
                transcription=transcription
            )
        except Exception as e:
            logger.error(f"Error procesando video: {str(e)}")
            raise RuntimeError(f"Error en procesamiento: {str(e)}")

    async def _extract_metadata(self, video_path: Path) -> Dict[str, Any]:
        """Extrae metadata básica del video"""
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError("No se puede abrir el archivo de video")
        
        return {
            'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
            'fps': cap.get(cv2.CAP_PROP_FPS),
            'resolution': (
                int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            )
        }

    async def _detect_scenes(self, video_path: Path) -> List[Scene]:
        """Detecta escenas en el video"""
        scenes = []
        cap = cv2.VideoCapture(str(video_path))
        
        prev_frame = None
        current_scene_start = 0
        frame_count = 0
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % self.frame_sample_rate == 0:
                if prev_frame is not None:
                    diff = self._calculate_frame_difference(prev_frame, frame)
                    if diff > self.scene_threshold:
                        timestamp = frame_count / cap.get(cv2.CAP_PROP_FPS)
                        if timestamp - current_scene_start >= self.min_scene_duration:
                            scenes.append(Scene(
                                start_time=current_scene_start,
                                end_time=timestamp
                            ))
                            current_scene_start = timestamp
                
                prev_frame = frame.copy()
            frame_count += 1
            
        cap.release()
        return scenes

    def _calculate_frame_difference(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """Calcula la diferencia entre dos frames"""
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        diff = cv2.absdiff(gray1, gray2)
        return np.mean(diff) / 255.0

    async def _transcribe_audio(self, video_path: Path) -> str:
        """Transcribe el audio del video"""
        try:
            result = self.whisper_model.transcribe(str(video_path))
            return result.text
        except Exception as e:
            logger.error(f"Error en transcripción: {str(e)}")
            return ""