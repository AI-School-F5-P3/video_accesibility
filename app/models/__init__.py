from dataclasses import dataclass
from typing import List, Optional, Tuple
from datetime import datetime

@dataclass
class VideoMetadata:
    id: str
    title: str
    duration: float
    resolution: Tuple[int, int]
    fps: float
    format: str
    created_at: datetime
    file_size: int
    bitrate: int
    audio_channels: int
    audio_sample_rate: int

@dataclass
class Scene:
    id: str
    video_id: str
    start_time: float
    end_time: float
    description: str
    confidence: float
    key_objects: List[str]
    emotional_context: str
    movement_type: str
    lighting_condition: str
    scene_type: str

@dataclass
class Transcript:
    id: str
    video_id: str
    text: str
    start_time: float
    end_time: float
    speaker: Optional[str]
    confidence: float
    language: str
    emotions: Optional[str]
    is_filtered: bool