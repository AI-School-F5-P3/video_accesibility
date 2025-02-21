from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict
from enum import Enum
from datetime import datetime

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

class VideoRequest(BaseModel):
    url: HttpUrl
    language: str = Field(default="es", min_length=2, max_length=5)
    quality: VideoQuality = Field(default=VideoQuality.HIGH)
    processing_type: ProcessingType = Field(default=ProcessingType.FULL)
    generate_subtitles: bool = Field(default=True)
    generate_audio_description: bool = Field(default=True)
    accessibility_options: Dict[str, bool] = Field(
        default_factory=lambda: {
            "high_contrast": False,
            "large_text": False,
            "screen_reader_optimized": True
        }
    )

    class Config:
        use_enum_values = True

class ProcessingResponse(BaseModel):
    video_id: str
    status: str
    progress: float = Field(ge=0.0, le=1.0)
    started_at: datetime
    estimated_completion: datetime
    error: Optional[str] = None
    processing_details: Dict[str, any] = Field(default_factory=dict)