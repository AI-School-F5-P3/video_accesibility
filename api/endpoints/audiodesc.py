from fastapi import APIRouter, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from typing import Optional, List
from src.core.audio_processor import AudioProcessor
from src.services.video_service import VideoService
from src.config.setup import Settings
from pathlib import Path

router = APIRouter()
settings = Settings()
audio_processor = AudioProcessor(settings)
video_service = VideoService(settings)

@router.get("/{video_id}")
async def get_audiodescription(
    video_id: str,
    format: str = "json",
    download: bool = False
):
    """Get audio description for a video"""
    try:
        audiodesc = await audio_processor.get_audiodescription(video_id)
        
        if download:
            # Verificar si hay una ruta de audio
            if not audiodesc.get("audio_path"):
                raise HTTPException(
                    status_code=404,
                    detail="Audiodescripción no disponible para descarga"
                )
                
            audio_path = Path(audiodesc["audio_path"])
            if not audio_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail="Archivo de audio no encontrado"
                )
            
            # Determinar el tipo MIME según la extensión
            media_type = "audio/wav" if audio_path.suffix == ".wav" else "audio/mpeg"
            
            return FileResponse(
                audio_path,
                media_type=media_type,
                filename=f"{video_id}_described{audio_path.suffix}"
            )
            
        return audiodesc
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.post("/{video_id}/generate")
async def generate_audiodescription(
    video_id: str,
    voice_type: str = "es-ES-F",
    background_tasks: BackgroundTasks = None
):
    """Generate audio description for a video"""
    try:
        # Get video path
        video_path = await video_service.get_video_path(video_id)
        if not video_path:
            raise HTTPException(
                status_code=404,
                detail="Video no encontrado"
            )
            
        # Start generation in background
        if background_tasks:
            background_tasks.add_task(
                audio_processor.generate_description,
                video_id=video_id,
                video_path=video_path,
                voice_type=voice_type
            )
        else:
            # Si no hay tareas en segundo plano, iniciar directamente
            await audio_processor.generate_description(
                video_id=video_id,
                video_path=video_path,
                voice_type=voice_type
            )

        return {
            "message": "Generación de audiodescripción iniciada",
            "video_id": video_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{video_id}/status")
async def get_generation_status(video_id: str):
    """Get the status of audio description generation"""
    try:
        status = await audio_processor.get_status(video_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{video_id}/descriptions/{desc_id}")
async def update_description(
    video_id: str,
    desc_id: str,
    text: str,
    background_tasks: BackgroundTasks = None
):
    """Update a specific description and regenerate its audio"""
    try:
        updated = await audio_processor.update_description(
            video_id=video_id,
            desc_id=desc_id,
            new_text=text
        )
        
        # Regenerate audio in background
        if background_tasks:
            background_tasks.add_task(
                audio_processor.regenerate_audio,
                video_id=video_id,
                desc_id=desc_id
            )
        
        return {
            "message": "Actualización de descripción iniciada",
            "description": updated
        }
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{video_id}/preview")
async def preview_descriptions(video_id: str):
    """Get audio description preview (first few descriptions)"""
    try:
        audiodesc = await audio_processor.get_audiodescription(video_id)
        
        # Get first 5 descriptions
        preview_data = {
            "video_id": video_id,
            "descriptions": audiodesc["descriptions"][:5] if audiodesc.get("descriptions") else []
        }
        
        return preview_data
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))