from typing import Dict, List, Optional, Any, Tuple, AsyncGenerator
import numpy as np
from vertexai.generative_models import GenerativeModel
from dataclasses import dataclass
from pathlib import Path
import os
import logging
import ffmpeg
import asyncio
import cv2
import time
from app.models import Scene, VideoMetadata
from app.utils.validators import validate_video_format
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
from ..core.memory_manager import MemoryManager
from ..core.error_handler import ProcessingError
from ..utils.cache import ResultCache
from .frame_processor import FrameProcessor
from .queue_manager import VideoQueue
from collections.abc import Generator 
from ..config.logging_config import setup_logging
import json
from app.core.error_handler import ProcessingError, ErrorType, ErrorDetails

logger = setup_logging()

@dataclass
class VideoConfig:
    """Video analysis configuration following UNE standards."""
    frame_rate: int = 25
    min_scene_duration: float = 2.0  # UNE153020 requirement
    resolution: Tuple[int, int] = (1920, 1080)
    quality_threshold: float = 0.85

class VideoAnalyzer:
    """Analizador de video para detección de escenas y contenido"""

    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el analizador
        
        Args:
            config: Configuración del analizador
        """
        try:
            self.config = config  # Usar directamente el diccionario
            self._init_components()
            self._init_parameters()
            logger.info("Inicializando VideoAnalyzer con configuración: %s", 
                       json.dumps(config, indent=2))
            self.frame_processor = FrameProcessor(
                batch_size=config.get('batch_size', 32)
            )
            self.queue = VideoQueue(
                max_concurrent=config.get('max_concurrent_tasks', 3)
            )
            self.memory_manager = MemoryManager(
                max_memory_percent=config.get('max_memory_percent', 80.0)
            )
            self.cache = ResultCache()
            self.batch_queue = Queue(maxsize=config.get('batch_size', 10))
            self.frame_buffer_size = 30
            self.scene_detection_method = 'histogram'
            logger.info("VideoAnalyzer inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando VideoAnalyzer: {str(e)}")
            raise

    def _init_parameters(self) -> None:
        """Inicializa parámetros de análisis"""
        video_config = self.config
        self.scene_threshold = video_config.get('SCENE_DETECTION_THRESHOLD', 0.3)
        self.min_scene_duration = video_config.get('MIN_SCENE_DURATION', 2.0)
        self.sample_rate = video_config.get('FRAME_SAMPLE_RATE', 1)

    def _init_components(self):
        self.batch_size = 32
        self.max_retries = 3

    async def detect_scenes(self, video_path: Path) -> List[Scene]:
        """
        Detecta escenas en el video de forma asíncrona
        
        Args:
            video_path: Ruta al archivo de video
            
        Returns:
            List[Scene]: Lista de escenas detectadas
        """
        try:
            validate_video_format(video_path)
            return await self._analyze_scenes(video_path)
        except Exception as e:
            logger.error(f"Error en detección de escenas: {str(e)}")
            raise RuntimeError(f"Error detectando escenas: {str(e)}")

    async def _analyze_scenes(self, video_path: Path) -> List[Scene]:
        """Analiza el video para detectar escenas con optimizaciones"""
        scenes = []
        cap = cv2.VideoCapture(str(video_path))
        
        if not cap.isOpened():
            raise ValueError("No se puede abrir el video")

        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            frame_batches = self._create_frame_batches(cap, total_frames)
            
            async for batch_scenes in self._process_frame_batches(frame_batches, fps):
                scenes.extend(batch_scenes)
                
            # Post-procesamiento de escenas
            scenes = self._merge_short_scenes(scenes)
            scenes = self._validate_scene_durations(scenes)
            
            return scenes
            
        finally:
            cap.release()

    def _create_frame_batches(self, cap: cv2.VideoCapture, total_frames: int) -> Generator:
        """Genera lotes de frames optimizando memoria"""
        batch = []
        frame_count = 0
        
        while frame_count < total_frames:
            if not self.memory_manager.check_memory():
                logger.warning("Memoria baja detectada, esperando...")
                time.sleep(1)
                continue
                
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % self.sample_rate == 0:
                batch.append((frame_count, frame))
                
            if len(batch) >= self.batch_size:
                yield batch
                batch = []
                
            frame_count += 1
            
        if batch:
            yield batch

    async def _process_frame_batches(self, 
                                   frame_batches: Generator, 
                                   fps: float) -> AsyncGenerator[List[Scene], None]:
        """Procesa lotes de frames en paralelo"""
        for batch in frame_batches:
            if not self.memory_manager.check_memory():
                await asyncio.sleep(1)
                continue
                
            batch_results = await self._analyze_batch(batch, fps)
            yield self._create_scenes_from_batch(batch_results, fps)

    async def _analyze_batch(self, 
                           batch: List[Tuple[int, np.ndarray]], 
                           fps: float) -> List[Dict[str, Any]]:
        """Analiza un lote de frames en paralelo"""
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            futures = [
                loop.run_in_executor(
                    executor,
                    self._analyze_frame_pair,
                    batch[i][1],
                    batch[i+1][1] if i+1 < len(batch) else None,
                    batch[i][0] / fps
                )
                for i in range(len(batch))
            ]
            return await asyncio.gather(*futures)

    def _analyze_frame_pair(self, 
                          current_frame: np.ndarray, 
                          next_frame: Optional[np.ndarray],
                          timestamp: float) -> Dict[str, Any]:
        """Analiza un par de frames para detectar cambios de escena"""
        if next_frame is None:
            return {'timestamp': timestamp, 'is_scene_change': False, 'confidence': 1.0}
            
        if self.scene_detection_method == 'histogram':
            diff = self._compare_histograms(current_frame, next_frame)
        else:
            diff = self._calculate_frame_difference(current_frame, next_frame)
            
        return {
            'timestamp': timestamp,
            'is_scene_change': diff > self.scene_threshold,
            'confidence': 1.0 - diff
        }

    def _compare_histograms(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """Compara histogramas de frames para detección más precisa"""
        hist1 = cv2.calcHist([frame1], [0], None, [256], [0, 256])
        hist2 = cv2.calcHist([frame2], [0], None, [256], [0, 256])
        
        return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

    def _merge_short_scenes(self, scenes: List[Scene]) -> List[Scene]:
        """Fusiona escenas demasiado cortas"""
        if not scenes:
            return scenes
            
        merged = []
        current_scene = scenes[0]
        
        for next_scene in scenes[1:]:
            if (next_scene.start_time - current_scene.end_time) < self.min_scene_duration:
                current_scene.end_time = next_scene.end_time
                current_scene.confidence = min(current_scene.confidence, next_scene.confidence)
            else:
                merged.append(current_scene)
                current_scene = next_scene
                
        merged.append(current_scene)
        return merged

    def _validate_scene_durations(self, scenes: List[Scene]) -> List[Scene]:
        """Valida y ajusta duraciones de escenas según estándares UNE"""
        return [
            scene for scene in scenes 
            if (scene.end_time - scene.start_time) >= self.min_scene_duration
        ]

    def _calculate_frame_difference(self, frame1: np.ndarray, frame2: np.ndarray) -> float:
        """
        Calcula la diferencia entre dos frames
        
        Returns:
            float: Valor de diferencia normalizado (0-1)
        """
        gray1 = cv2.cvtColor(frame1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2, cv2.COLOR_BGR2GRAY)
        
        diff = cv2.absdiff(gray1, gray2)
        return np.mean(diff) / 255.0

    async def process_frames_batch(self, frames: List[np.ndarray]) -> List[Dict[str, Any]]:
        """Procesa un lote de frames en paralelo"""
        if not self.memory_manager.check_memory():
            raise ProcessingError("MEMORY_ERROR", "Memoria insuficiente")

        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            tasks = [
                loop.run_in_executor(executor, self._analyze_frame, frame)
                for frame in frames
            ]
            return await asyncio.gather(*tasks)

    async def analyze_content(self, video_path: Path) -> VideoMetadata:
        """Analiza el contenido del video"""
        logger.info("Iniciando análisis de video: %s", video_path)
        try:
            scenes = await self.detect_scenes(video_path)
            logger.debug("Detectadas %d escenas", len(scenes))
            
            metadata = await self._extract_metadata(video_path)
            logger.debug("Metadata extraída: %s", json.dumps(metadata, indent=2))
            
            return VideoMetadata(
                path=video_path,
                duration=metadata['duration'],
                fps=metadata['fps'],
                resolution=metadata['resolution'],
                scenes=scenes
            )
        except Exception as e:
            logger.error("Error analizando video %s: %s", video_path, str(e))
            raise ProcessingError(
                ErrorType.VIDEO_PROCESSING_ERROR,
                ErrorDetails(
                    component="VideoAnalyzer",
                    message=f"Error en análisis: {str(e)}",
                    code="ANALYSIS_ERROR"
                )
            )

    async def _extract_metadata(self, video_path: Path) -> Dict[str, Any]:
        """Extrae metadata básica del video"""
        if not self.memory_manager.check_memory():
            raise ProcessingError(
                ErrorType.RESOURCE_ERROR,
                ErrorDetails(
                    component="VideoAnalyzer",
                    message="Memoria insuficiente para extraer metadata",
                    code="LOW_MEMORY"
                )
            )
        
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError("No se puede abrir el video")
        
        try:
            return {
                'duration': cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
                'fps': cap.get(cv2.CAP_PROP_FPS),
                'resolution': (
                    int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                )
            }
        finally:
            cap.release()

    async def process_video(self, video_path: Path) -> str:
        """Añade un video a la cola de procesamiento"""
        return await self.queue.add_task(video_path, self.config)

    async def get_processing_status(self, task_id: str) -> Dict[str, Any]:
        """Obtiene el estado del procesamiento"""
        return self.queue.get_task_status(task_id)

    def _create_scenes_from_batch(self, batch_results: List[Dict[str, Any]], fps: float) -> List[Scene]:
        """
        Crea objetos Scene a partir de los resultados del análisis de batch
        
        Args:
            batch_results: Resultados del análisis de frames
            fps: Frames por segundo del video
        
        Returns:
            List[Scene]: Lista de escenas detectadas
        """
        scenes = []
        current_scene = None
        
        for result in batch_results:
            if result['is_scene_change'] and current_scene is not None:
                current_scene.end_time = result['timestamp']
                scenes.append(current_scene)
                current_scene = Scene(
                    start_time=result['timestamp'],
                    end_time=result['timestamp'],
                    confidence=result['confidence']
                )
            elif current_scene is None:
                current_scene = Scene(
                    start_time=result['timestamp'],
                    end_time=result['timestamp'],
                    confidence=result['confidence']
                )
        
        if current_scene is not None:
            scenes.append(current_scene)
        
        return scenes

    def _analyze_frame(self, frame: np.ndarray) -> Dict[str, Any]:
        """Analiza un frame individual"""
        try:
            # Convertir a escala de grises para análisis básico
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Detectar características básicas
            features = {
                'brightness': np.mean(gray),
                'contrast': np.std(gray),
                'edges': len(cv2.Canny(gray, 100, 200).nonzero()[0])
            }
            
            return {
                'features': features,
                'requires_description': features['edges'] > 1000  # Umbral arbitrario
            }
        except Exception as e:
            logger.error(f"Error analizando frame: {str(e)}")
            return {
                'error': str(e),
                'requires_description': True  # Por defecto, requerir descripción
            }