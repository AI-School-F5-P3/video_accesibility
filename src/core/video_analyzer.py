import os
import tempfile
from typing import List, Optional, Dict, Any
import cv2
import numpy as np
import yt_dlp
from pydantic import BaseModel, field_validator

class VideoFormat:
    VIDEO_FORMATS = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
    AUDIO_FORMATS = ['.wav', '.mp3', '.m4a', '.flac', '.webm']

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
        if v not in VideoFormat.VIDEO_FORMATS:
            raise ValueError(f'Invalid format, must be one of {VideoFormat.VIDEO_FORMATS}')
        return v

    @field_validator('duration', 'width', 'height')
    @classmethod
    def validate_positive_values(cls, v):
        if v <= 0:
            raise ValueError('Value must be positive')
        return v

class VideoProcessor:
    @staticmethod
    def extract_frames(video_path: str, interval: int, fps: float) -> List[np.ndarray]:
        frames = []
        frame_count = 0
        
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            raise ValueError("Could not open the video file.")
        
        while True:
            ret, frame = video.read()
            if not ret:
                break
            if frame_count % int(fps * interval) == 0:
                frames.append(frame.copy())
            frame_count += 1
        
        video.release()
        return frames

    @staticmethod
    def detect_scene_changes(frames: List[np.ndarray], threshold: float = 0.1) -> List[int]:
        scene_changes = []
        prev_frame = None
        
        for i, frame in enumerate(frames):
            if prev_frame is not None:
                prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                curr_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                diff = cv2.absdiff(prev_gray, curr_gray)
                mean_diff = np.mean(diff)
                
                if mean_diff > (threshold * 255):
                    scene_changes.append(i)
            
            prev_frame = frame
            
        return scene_changes    

class YouTubeVideoManager:
    def __init__(self, youtube_url: str):
        self.youtube_url = youtube_url
        self.metadata = self._extract_youtube_metadata()
        self.video_path = None
        self._representative_frames = None

    def analyze_scene_changes(self, threshold: float = 0.1) -> List[int]:
        frames = self.representative_frames
        return VideoProcessor.detect_scene_changes(frames, threshold)

    def _extract_youtube_metadata(self) -> YouTubeVideoMetadata:
        ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.youtube_url, download=False)
                return YouTubeVideoMetadata(
                    url=self.youtube_url,
                    title=info_dict.get('title', 'Unknown Title'),
                    duration=info_dict.get('duration', 0),
                    video_format='.mp4',
                    thumbnail=info_dict.get('thumbnail', ''),
                    width=1920,
                    height=1080,
                    uploader=info_dict.get('uploader', '')
                )
        except Exception as e:
            raise ValueError(f"Error extracting metadata: {str(e)}")

    def _download_video(self) -> str:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]',
            'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s'),
            'nooverwrites': True,
            'quiet': True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(self.youtube_url, download=True)
                video_path = ydl.prepare_filename(info_dict)
                return video_path
        except Exception as e:
            raise ValueError(f"Error downloading video: {str(e)}")

    def _update_video_metadata(self, video_path: str) -> None:
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            raise ValueError("Could not open the video file.")

        self.metadata.width = int(video.get(cv2.CAP_PROP_FRAME_WIDTH)) or 1920
        self.metadata.height = int(video.get(cv2.CAP_PROP_FRAME_HEIGHT)) or 1080
        self.metadata.fps = float(video.get(cv2.CAP_PROP_FPS)) or 30.0
        video.release()

    @property
    def representative_frames(self) -> List[np.ndarray]:
        if self._representative_frames is None:
            if not self.video_path:
                self.video_path = self._download_video()
                self._update_video_metadata(self.video_path)
            self._representative_frames = VideoProcessor.extract_frames(
                self.video_path, interval=5, fps=self.metadata.fps or 30
            )
        return self._representative_frames

    def generate_accessibility_report(self) -> Dict[str, Any]:
        return {
            "title": self.metadata.title,
            "url": self.metadata.url,
            "duration": self.metadata.duration,
            "resolution": f"{self.metadata.width}x{self.metadata.height}",
            "fps": self.metadata.fps,
            "uploader": self.metadata.uploader,
            "thumbnail": self.metadata.thumbnail,
            "scene_changes": len(self.analyze_scene_changes()),
        }

    def cleanup(self):
        try:
            if self.video_path and os.path.exists(self.video_path):
                os.remove(self.video_path)
        except Exception as e:
            print(f"Error cleaning temporary files: {e}")