from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List
from src.core.audio_processor import AudioProcessor
from src.services.video_service import VideoService
from src.utils.formatters import format_audiodesc_response
from src.utils.validators import validate_silence_intervals

router = APIRouter()
audio_processor = AudioProcessor()
video_service = VideoService()

@router.post("/{video_id}/generate")
async def generate_audiodescription(
    video_id: str,
    background_tasks: BackgroundTasks
):
    """Generate audio description for a video"""
    try:
        # Get video scenes and silence intervals
        scenes = await video_service.get_scenes(video_id)
        silence_intervals = await audio_processor.detect_silence(video_id)
        
        if not validate_silence_intervals(silence_intervals):
            raise HTTPException(
                status_code=400,
                detail="No suitable silence intervals found"
            )

        # Generate descriptions
        background_tasks.add_task(
            audio_processor.generate_descriptions,
            video_id=video_id,
            scenes=scenes,
            silence_intervals=silence_intervals
        )

        return {"message": "Audio description generation started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{video_id}")
async def get_audiodescription(video_id: str, format: str = "json"):
    """Get audio description for a video"""
    try:
        audiodesc = await audio_processor.get_audiodescription(video_id)
        
        if format == "srt":
            return format_audiodesc_response(audiodesc, "srt")
        elif format == "json":
            return format_audiodesc_response(audiodesc, "json")
        else:
            raise HTTPException(
                status_code=400,
                detail="Unsupported format. Use 'srt' or 'json'"
            )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{video_id}/synthesize")
async def synthesize_audiodescription(
    video_id: str,
    background_tasks: BackgroundTasks
):
    """Synthesize audio for the generated descriptions"""
    try:
        background_tasks.add_task(
            audio_processor.synthesize_audio,
            video_id=video_id
        )
        
        return {"message": "Audio synthesis started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{video_id}/status")
async def get_audiodesc_status(video_id: str):
    """Get the status of audio description generation"""
    try:
        status = await audio_processor.get_status(video_id)
        return {"status": status}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))