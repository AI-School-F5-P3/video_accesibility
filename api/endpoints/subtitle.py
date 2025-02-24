from fastapi import APIRouter, HTTPException
from typing import List
from src.services.subtitle_service import SubtitleService
from src.core.speech_processor import SpeechProcessor
from src.utils.formatters import format_subtitle_response

router = APIRouter()
subtitle_service = SubtitleService()
speech_processor = SpeechProcessor()

@router.post("/{video_id}/generate")
async def generate_subtitles(video_id: str):
    """Generate subtitles for a video"""
    try:
        # Process speech to text
        transcript = await speech_processor.transcribe_video(video_id)
        
        # Generate and save subtitles
        subtitle_id = await subtitle_service.create_subtitles(
            video_id=video_id,
            transcript=transcript
        )
        
        return {
            "subtitle_id": subtitle_id,
            "message": "Subtitles generated successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{video_id}")
async def get_subtitles(video_id: str, format: str = "srt"):
    """Get subtitles for a video in specified format"""
    try:
        subtitles = await subtitle_service.get_subtitles(video_id)
        
        if format == "srt":
            return format_subtitle_response(subtitles, "srt")
        elif format == "json":
            return format_subtitle_response(subtitles, "json")
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported format. Use 'srt' or 'json'"
            )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{video_id}/subtitles/{subtitle_id}")
async def update_subtitle(
    video_id: str,
    subtitle_id: str,
    subtitle_data: dict
):
    """Update a specific subtitle"""
    try:
        updated_subtitle = await subtitle_service.update_subtitle(
            video_id,
            subtitle_id,
            subtitle_data
        )
        return updated_subtitle
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))