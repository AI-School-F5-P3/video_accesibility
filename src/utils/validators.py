import cv2
from pathlib import Path
import logging

class VideoValidator:
    def __init__(self, settings):
        self.settings = settings
        
    def validate_video(self, video_path: Path) -> tuple[bool, str]:
        try:
            if not video_path.exists():
                return False, "Video file does not exist"

            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return False, "Cannot open video file"

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            
            cap.release()

            if duration > self.settings.MAX_VIDEO_DURATION:
                return False, "Video is too long. Maximum duration is 10 minutes"

            return True, "Valid video"
            
        except Exception as e:
            return False, f"Error validating video: {str(e)}"