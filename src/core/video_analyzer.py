import cv2
import os
from PIL import Image
from pathlib import Path
import logging

class VideoAnalyzer:
    def __init__(self, settings):
        self.settings = settings
        
    def extract_frame(self, video_path: Path, timestamp_ms: int) -> Image.Image:
        try:
            cap = cv2.VideoCapture(str(video_path))
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
            ret, frame = cap.read()
            cap.release()

            if not ret:
                return None

            return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
        except Exception as e:
            logging.error(f"Error extracting frame: {str(e)}")
            return None