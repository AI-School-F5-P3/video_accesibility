import os
import json
import logging
import tempfile
import io
import cv2
import numpy as np
import ffmpeg
import yt_dlp
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from google.cloud import vision
from vertexai.generative_models import GenerativeModel
from pydantic import BaseModel, field_validator

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Video según UNE153020
@dataclass
class VideoConfig:
    frame_rate: int = 25
    min_scene_duration: float = 2.0
    resolution: Tuple[int, int] = (1920, 1080)
    quality_threshold: float = 0.85

# Metadatos de Video
class YouTubeVideoMetadata(BaseModel):
    url: str
    title: str
    duration: int
    video_format: str
    thumbnail: str
    width: int
    height: int
    fps: Optional[float] = None
    uploader: Optional[str] = None

    @field_validator('video_format')
    @classmethod
    def validate_video_format(cls, v):
        allowed_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        if v not in allowed_formats:
            raise ValueError(f'Formato no válido: {allowed_formats}')
        return v

# Analizador de Video
class VideoAnalyzer:
    def __init__(self, model: Optional[GenerativeModel] = None, config: Optional[VideoConfig] = None):
        self.model = model
        self.config = config or VideoConfig()
        self.silence_threshold = -35
        self.min_silence_duration = 1.0

    def detect_scenes(self, video_path: str) -> List[Dict[str, Any]]:
        return [{'start_time': 0, 'end_time': 5, 'description': 'Escena inicial'}]

    def detect_silence(self, video_path: str) -> Optional[Dict[str, float]]:
        try:
            cmd = [
                'ffmpeg', '-i', str(video_path), '-af', f'silencedetect=noise={self.silence_threshold}dB:d={self.min_silence_duration}', '-f', 'null', '-'
            ]
            output = subprocess.run(cmd, capture_output=True, text=True).stderr
            silences = []
            for line in output.split('\n'):
                if 'silence_start:' in line:
                    start = float(line.split('silence_start:')[1].strip())
                    silences.append({'start': start})
            return silences[0] if silences else None
        except Exception as e:
            logger.error(f"Error detectando silencios: {str(e)}")
            return None

# Extractor de Frames
class FrameExtractor:
    def __init__(self, video_path: str, output_dir: str, interval: int = 3):
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.interval = interval
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

    def extract_frames(self) -> List[Tuple[float, str]]:
        frames_info = []
        frame_interval = int(self.fps * self.interval)
        current_frame = 0
        while True:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = self.cap.read()
            if not ret:
                break
            timestamp = current_frame / self.fps
            frame_path = self.output_dir / f"frame_{timestamp:.2f}.jpg"
            cv2.imwrite(str(frame_path), frame)
            frames_info.append((timestamp, str(frame_path)))
            current_frame += frame_interval
        self.cap.release()
        return frames_info

# Analizador de Frames con Google Vision
class FrameAnalyzer:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def analyze_frame(self, frame_path: str) -> Dict:
        try:
            with io.open(frame_path, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            response = self.client.annotate_image({'image': image, 'features': [{'type_': vision.Feature.Type.OBJECT_LOCALIZATION}]})
            return {'objects': [{'name': obj.name} for obj in response.localized_object_annotations]}
        except Exception as e:
            logger.error(f"Error analizando frame {frame_path}: {str(e)}")
            return {'error': str(e)}

# Gestor Principal
class YouTubeVideoManager:
    def __init__(self, youtube_url: str):
        self.youtube_url = youtube_url
        self.metadata = self._extract_youtube_metadata()
        self.video_path = None

    def _extract_youtube_metadata(self) -> YouTubeVideoMetadata:
        ydl_opts = {'quiet': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(self.youtube_url, download=False)
            return YouTubeVideoMetadata(
                url=self.youtube_url, title=info_dict.get('title', 'Unknown'), duration=info_dict.get('duration', 0),
                video_format='.mp4', thumbnail=info_dict.get('thumbnail', ''), width=1920, height=1080
            )

    def download_video(self) -> str:
        ydl_opts = {'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]', 'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s')}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(self.youtube_url, download=True)
            return ydl.prepare_filename(info_dict)

    def analyze_video(self):
        self.video_path = self.download_video()
        extractor = FrameExtractor(self.video_path, "./frames")
        frames = extractor.extract_frames()
        analyzer = FrameAnalyzer()
        results = [analyzer.analyze_frame(frame[1]) for frame in frames]
        with open("video_analysis.json", "w") as f:
            json.dump(results, f, indent=2)
        os.remove(self.video_path)

# Ejecución
if __name__ == "__main__":
    youtube_url = input("Ingresa la URL del video de YouTube: ")
    manager = YouTubeVideoManager(youtube_url)
    manager.analyze_video()
    print("Análisis completado.")