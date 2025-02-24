from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional
from src.services.subtitle_service import SubtitleService
from src.config.setup import Settings
from pathlib import Path

router = APIRouter()
settings = Settings()
subtitle_service = SubtitleService(settings)

@router.get("/{video_id}")
async def get_subtitles(
    video_id: str,
    format: str = "srt",
    download: bool = False
):
    """Get subtitles for a video"""
    try:
        subtitle_data = await subtitle_service.get_subtitles(video_id, format)
        
        if download:
            subtitle_path = Path(subtitle_data["path"])
            if not subtitle_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail="Archivo de subtítulos no encontrado"
                )
            
            return FileResponse(
                subtitle_path,
                media_type="application/x-subrip",
                filename=f"{video_id}_subtitles.{format}"
            )
            
        return subtitle_data
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{video_id}/segments/{segment_id}")
async def update_subtitle_segment(
    video_id: str,
    segment_id: str,
    text: str
):
    """Update a specific subtitle segment"""
    try:
        updated = await subtitle_service.update_subtitle(
            video_id,
            segment_id,
            {"text": text}
        )
        return updated
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{video_id}/preview")
async def preview_subtitles(video_id: str, format: str = "srt"):
    """Get subtitle preview (first few segments)"""
    try:
        subtitle_data = await subtitle_service.get_subtitles(video_id, format)
        
        # Get first 5 segments
        preview_data = {
            "video_id": video_id,
            "format": format,
            "segments": subtitle_data["segments"][:5]
        }
        
        return preview_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{video_id}/realign")
async def realign_subtitles(
    video_id: str,
    offset_ms: int,
    background_tasks: BackgroundTasks
):
    """Realign subtitles by adding/subtracting milliseconds"""
    try:
        background_tasks.add_task(
            subtitle_service.realign_subtitles,
            video_id=video_id,
            offset_ms=offset_ms
        )
        
        return {
            "message": "Realineación de subtítulos iniciada",
            "video_id": video_id,
            "offset_ms": offset_ms
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))