from pathlib import Path
from pydantic import BaseModel, Field, HttpUrl, ConfigDict, validator, field_validator, model_validator
from typing import List, Optional, Dict, Any, Tuple, Union
from enum import Enum
from datetime import datetime
from pydantic.dataclasses import dataclass
import re

class VideoQuality(str, Enum):
    LOW = "360p"
    MEDIUM = "720p"
    HIGH = "1080p"
    ULTRA = "4K"

class ProcessingType(str, Enum):
    FULL = "full"
    SUBTITLES_ONLY = "subtitles"
    AUDIO_DESCRIPTION = "audio_description"
    TRANSCRIPTION = "transcription"

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class Scene(BaseModel):
    """Representación de una escena del video"""
    start_time: float = Field(ge=0.0)
    end_time: float = Field(ge=0.0)
    description: Optional[str] = None
    key_frames: List[int] = Field(default_factory=list)
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    tags: List[str] = Field(default_factory=list)
    objects_detected: List[str] = Field(default_factory=list)
    accessibility_score: float = Field(default=0.0, ge=0.0, le=1.0)

    @field_validator('end_time')
    @classmethod
    def validate_end_time(cls, v, values):
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError("end_time debe ser mayor que start_time")
        return v

class VideoMetadata(BaseModel):
    """Metadata del video procesado"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        json_encoders={
            Path: str  # Permite serialización de Path a JSON
        }
    )
    
    path: Union[Path, str]  # Soporta tanto Path como str para flexibilidad
    title: Optional[str] = None
    duration: float = Field(gt=0.0)  # Duración debe ser positiva
    resolution: Tuple[int, int] = Field(..., description="(width, height)")
    fps: float = Field(gt=0.0)  # FPS debe ser positivo
    scenes: List[Scene] = Field(default_factory=list)
    size_mb: Optional[float] = Field(None, gt=0.0)
    codec: Optional[str] = None
    audio_channels: Optional[int] = Field(None, ge=0)
    audio_sample_rate: Optional[int] = Field(None, gt=0)
    bitrate: Optional[int] = Field(None, gt=0)

    @property
    def duration_formatted(self) -> str:
        """Retorna la duración en formato HH:MM:SS"""
        hours = int(self.duration // 3600)
        minutes = int((self.duration % 3600) // 60)
        seconds = int(self.duration % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @property
    def resolution_str(self) -> str:
        """Retorna la resolución en formato WxH"""
        return f"{self.resolution[0]}x{self.resolution[1]}"

class SubtitleConfig(BaseModel):
    """Configuración de subtítulos según norma UNE"""
    model_config = ConfigDict(use_enum_values=True)
    
    font_size: int = Field(default=32)
    max_chars_per_line: int = Field(default=37)
    max_lines: int = Field(default=2)
    display_time_ms: int = Field(default=3500)
    background_opacity: float = Field(default=0.7, ge=0.0, le=1.0)

class VideoRequest(BaseModel):
    """Solicitud de procesamiento de video"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    url: HttpUrl
    language: str = Field(default="es", min_length=2, max_length=5)
    quality: VideoQuality = Field(default=VideoQuality.HIGH)
    processing_type: ProcessingType = Field(default=ProcessingType.FULL)
    generate_subtitles: bool = Field(default=True)
    generate_audio_description: bool = Field(default=True)
    subtitle_config: Optional[SubtitleConfig] = None
    accessibility_options: Dict[str, bool] = Field(
        default_factory=lambda: {
            "high_contrast": False,
            "large_text": False,
            "screen_reader_optimized": True
        }
    )

class ProcessingDetails(BaseModel):
    """Detalles del procesamiento del video"""
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    output_path: str
    duration: float
    frame_count: int
    resolution: Tuple[int, int]
    format: str
    metadata: VideoMetadata
    processing_time: float
    output_size_mb: float
    accessibility_score: float = Field(ge=0.0, le=100.0)

class ProcessingResponse(BaseModel):
    """Respuesta del procesamiento del video"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        use_enum_values=True
    )
    
    video_id: str
    status: ProcessingStatus
    progress: float = Field(ge=0.0, le=1.0)
    started_at: datetime
    estimated_completion: datetime
    error: Optional[str] = None
    details: Optional[ProcessingDetails] = None
    warnings: List[str] = Field(default_factory=list)
    accessibility_report: Optional[Dict[str, Any]] = None

# Modelos adicionales para respuestas específicas
class TranscriptionResult(BaseModel):
    """Resultado de la transcripción"""
    text: str
    confidence: float
    start_time: float
    end_time: float
    speaker: Optional[str] = None

class AudioDescriptionResult(BaseModel):
    """Resultado de la descripción de audio"""
    description: str
    start_time: float
    end_time: float
    priority: int = Field(ge=1, le=5)

class ServiceType(Enum):
    AUDIODESCRIPCION = "AUDIODESCRIPCION"
    SUBTITULADO = "SUBTITULADO"

@dataclass
class ProcessingConfig:
    batch_size: int = 32
    max_retries: int = 3
    max_concurrent_tasks: int = 3
    max_memory_percent: int = 80

@dataclass
class AIConfig:
    temperature: float = 0.7
    max_tokens: int = 1024
    language: str = "es"

@dataclass
class StorageConfig:
    storage_bucket: str = "video-accessibility-bucket"
    temp_storage_path: str = "./temp"
    output_storage_path: str = "./output/processed"
    cache_dir: str = "./cache"

class VideoConfig(BaseModel):
    """Configuración del procesamiento de video"""
    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        extra='allow'
    )
    
    # Campos directos
    batch_size: int = 32
    max_retries: int = 3
    max_concurrent_tasks: int = 3
    max_memory_percent: int = 80
    temperature: float = 0.7
    max_tokens: int = 1024
    language: str = "es"
    storage_bucket: str = "video-accessibility-bucket"
    temp_storage_path: str = "./temp"
    output_storage_path: str = "./output/processed"
    cache_dir: str = "./cache"
    max_video_duration: int = 3600
    scene_detection_threshold: float = 0.3
    min_scene_duration: float = 2.0

class AIResponse(BaseModel):
    text: str
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    metadata: Optional[Dict[str, Any]] = None

class GenerationParameters(BaseModel):
    temperature: float = Field(default=0.7, ge=0.0, le=1.0)
    max_tokens: int = Field(default=1024, ge=1)
    top_p: float = Field(default=0.8, ge=0.0, le=1.0)
    frequency_penalty: float = Field(default=0.0, ge=0.0, le=2.0)

class ProcessingResult(BaseModel):
    """Resultado del procesamiento de video"""
    task_id: str
    status: str
    progress: float = 0.0
    started_at: datetime
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    class Config:
        arbitrary_types_allowed = True