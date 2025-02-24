from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from typing import List
from src.services.video_service import VideoService
from src.core.video_analyzer import VideoAnalyzer
from src.models.scene import Scene
from src.utils.validators import validate_video_file
from src.utils.formatters import format_video_response

router = APIRouter()
video_service = VideoService()
video_analyzer = VideoAnalyzer()

@router.post("/upload/")
async def upload_video(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None
):
    """Upload a video file for processing"""
    try:
        # Validate video file
        if not validate_video_file(file):
            raise HTTPException(status_code=400, detail="Invalid video file")

        # Process video
        video_id = await video_service.save_video(file)
        
        # Add background task for video analysis
        background_tasks.add_task(
            video_analyzer.analyze_video,
            video_id=video_id
        )

        return {"video_id": video_id, "message": "Video uploaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{video_id}/scenes")
async def get_video_scenes(video_id: str) -> List[Scene]:
    """Get analyzed scenes from a video"""
    try:
        scenes = await video_service.get_scenes(video_id)
        return format_video_response(scenes)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{video_id}/status")
async def get_processing_status(video_id: str):
    """Get the processing status of a video"""
    try:
        status = await video_service.get_status(video_id)
        return {"status": status}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """Delete a video and its associated data"""
    try:
        await video_service.delete_video(video_id)
        return {"message": "Video deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))