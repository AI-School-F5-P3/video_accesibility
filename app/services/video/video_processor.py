import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import logging
from app.models import VideoMetadata, Scene, Transcript
from app.config import Settings
from app.utils.formatters import format_timestamp
import whisper
from stable_whisper import modify_model
import torch

logger = logging.getLogger(__name__)

class VideoProcessor:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.scene_threshold = settings.SCENE_DETECTION_THRESHOLD
        self.frame_sample_rate = settings.FRAME_SAMPLE_RATE
        self.min_scene_duration = settings.MIN_SCENE_DURATION
        self._initialize_whisper()
        
    def _initialize_whisper(self):
        """Inicializa el modelo de Whisper para transcripción"""
        try:
            base_model = whisper.load_model("large-v3")
            self.whisper_model = modify_model(base_model)
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"Whisper modelo inicializado en {self.device}")
        except Exception as e:
            logger.error(f"Error inicializando Whisper: {str(e)}")
            raise
        
    async def extract_metadata(self, video_path: Path) -> VideoMetadata:
        """Extrae metadatos del video"""
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise ValueError(f"No se pudo abrir el video: {video_path}")
                
            metadata = VideoMetadata(
                id=str(video_path.stem),
                title=video_path.stem,
                duration=cap.get(cv2.CAP_PROP_FRAME_COUNT) / cap.get(cv2.CAP_PROP_FPS),
                resolution=(
                    int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                    int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                ),
                fps=cap.get(cv2.CAP_PROP_FPS),
                format=video_path.suffix,
                created_at=video_path.stat().st_ctime,
                file_size=video_path.stat().st_size,
                bitrate=self._calculate_bitrate(cap),
                audio_channels=int(cap.get(cv2.CAP_PROP_AUDIOCHANNELS)),
                audio_sample_rate=int(cap.get(cv2.CAP_PROP_AUDIOSAMPLERATEMHZ))
            )
            cap.release()
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            raise

    async def detect_scenes(self, video_path: Path) -> List[Scene]:
        """Detecta cambios de escena en el video"""
        scenes = []
        try:
            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                raise ValueError(f"No se pudo abrir el video: {video_path}")
                
            prev_frame = None
            current_scene_start = 0
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                    
                if frame_count % self.frame_sample_rate == 0:
                    if prev_frame is not None:
                        diff = self._calculate_frame_difference(prev_frame, frame)
                        if diff > self.scene_threshold:
                            current_time = frame_count / cap.get(cv2.CAP_PROP_FPS)
                            if current_time - current_scene_start >= self.min_scene_duration:
                                scenes.append(Scene(
                                    id=f"scene_{len(scenes)}",
                                    video_id=video_path.stem,
                                    start_time=current_scene_start,
                                    end_time=current_time,
                                    description="",  # Se llenará con AI
                                    confidence=float(diff),
                                    key_objects=[],
                                    emotional_context="",
                                    movement_type=self._detect_movement_type(frame),
                                    lighting_condition=self._analyze_lighting(frame),
                                    scene_type=self._determine_scene_type(frame)
                                ))
                                current_scene_start = current_time
                    prev_frame = frame.copy()
                frame_count += 1
                
            cap.release()
            return scenes
            
        except Exception as e:
            logger.error(f"Error detecting scenes: {str(e)}")
            raise

    async def generate_transcript(self, video_path: Path) -> List[Transcript]:
        """Genera transcripción usando Stable-Whisper"""
        try:
            result = self.whisper_model.transcribe(
                str(video_path),
                language="es",
                word_timestamps=True,
                verbose=False
            )
            
            transcripts = []
            for segment in result.segments:
                transcript = Transcript(
                    id=f"trans_{len(transcripts)}",
                    video_id=video_path.stem,
                    text=segment.text,
                    start_time=segment.start,
                    end_time=segment.end,
                    speaker=None,  # Se puede implementar diarización
                    confidence=segment.confidence,
                    language="es",
                    emotions=None,
                    is_filtered=False
                )
                transcripts.append(transcript)
                
            return transcripts
            
        except Exception as e:
            logger.error(f"Error generando transcripción: {str(e)}")
            raise