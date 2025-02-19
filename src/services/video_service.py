import os
from typing import List, Dict, Optional
from fastapi import UploadFile
from src.config.settings import settings
from src.models.scene import Scene
from src.core.video_analyzer import VideoAnalyzer
from src.utils.time_utils import format_timestamp
import shutil
import uuid
from datetime import datetime, timezone

class VideoService:
    def __init__(self):
        self.video_analyzer = VideoAnalyzer()
        self.processing_status = {}  # Store processing status for each video

    async def save_video(self, file: UploadFile) -> str:
        """
        Save uploaded video file and return video_id
        """
        try:
            # Generate unique video ID
            video_id = str(uuid.uuid4())
            
            # Create video directory
            video_dir = os.path.join(settings.UPLOAD_DIR, video_id)
            os.makedirs(video_dir, exist_ok=True)
            
            # Save video file
            file_path = os.path.join(video_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Initialize processing status
            self.processing_status[video_id] = {
                "status": "uploaded",
                "file_path": file_path,
                "scenes": [],
                "created_at": datetime.now(timezone.utc)
            }
            
            return video_id
            
        except Exception as e:
            raise Exception(f"Error saving video: {str(e)}")

    async def get_scenes(self, video_id: str) -> List[Scene]:
        """
        Get analyzed scenes for a video
        """
        if video_id not in self.processing_status:
            raise Exception("Video not found")
            
        return self.processing_status[video_id].get("scenes", [])

    async def get_status(self, video_id: str) -> Dict:
        """
        Get processing status for a video
        """
        if video_id not in self.processing_status:
            raise Exception("Video not found")
            
        return self.processing_status[video_id]

    async def delete_video(self, video_id: str):
        """
        Delete video and its associated data
        """
        try:
            video_dir = os.path.join(settings.UPLOAD_DIR, video_id)
            if os.path.exists(video_dir):
                shutil.rmtree(video_dir)
            
            if video_id in self.processing_status:
                del self.processing_status[video_id]
                
        except Exception as e:
            raise Exception(f"Error deleting video: {str(e)}")

    async def process_video(self, video_id: str):
        """
        Process video for scene analysis
        """
        try:
            if video_id not in self.processing_status:
                raise Exception("Video not found")
                
            self.processing_status[video_id]["status"] = "processing"
            
            # Get video file path
            file_path = self.processing_status[video_id]["file_path"]
            
            # Analyze video using VideoAnalyzer
            scenes = await self.video_analyzer.analyze_video(file_path)
            
            # Update processing status
            self.processing_status[video_id].update({
                "status": "completed",
                "scenes": scenes,
                "processed_at": datetime.now(timezone.utc)
            })
            
            return scenes
            
        except Exception as e:
            self.processing_status[video_id]["status"] = "error"
            self.processing_status[video_id]["error"] = str(e)
            self.processing_status[video_id]["error_at"] = datetime.now(timezone.utc)
            raise Exception(f"Error processing video: {str(e)}")

    def _get_video_path(self, video_id: str) -> Optional[str]:
        """
        Get video file path from video_id
        """
        if video_id in self.processing_status:
            return self.processing_status[video_id].get("file_path")
        return None