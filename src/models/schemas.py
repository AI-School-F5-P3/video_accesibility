from pydantic import BaseModel
from typing import Dict, List, Optional, Union

class VideoInfo(BaseModel):
    id: str
    name: str
    duration: Optional[float] = None
    status: str = "new"

class VideoProcessRequest(BaseModel):
    video_id: str
    options: Dict

class VideoProcessResponse(BaseModel):
    video_id: str
    status: str
    message: str

class VideoRenderResponse(BaseModel):
    status: str
    message: str

class VideoRenderStatusResponse(BaseModel):
    status: str
    progress: int
    message: str

class VideoRenderResult(BaseModel):
    status: str
    video_id: str
    file_path: str
    download_url: str

class SubtitleData(BaseModel):
    video_id: str
    content: str
    format: str = "srt"

class AudioDescriptionData(BaseModel):
    video_id: str
    content: str
    audio_url: Optional[str] = None

class ProcessingStatus(BaseModel):
    status: str
    progress: int
    current_step: Optional[str] = None
    error: Optional[str] = None

class ProcessingResult(BaseModel):
    status: str
    video_id: str
    message: Optional[str] = None
    outputs: Optional[Dict[str, str]] = None