from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional
from src.services.video_service import VideoService
from src.config.setup import Settings
from src.utils.validators import validate_video_file

router = APIRouter()
settings = Settings()
video_service = VideoService(settings)

@router.post("/process")
async def process_video(
    video: Optional[UploadFile] = File(None),
    youtube_url: Optional[str] = Form(None),
    generate_audiodesc: bool = Form(False),
    generate_subtitles: bool = Form(False),
    voice_type: str = Form("es-ES-F"),
    subtitle_format: str = Form("srt"),
    output_quality: str = Form("high"),
    target_language: str = Form("es"),
    background_tasks: BackgroundTasks = None
):
    """Process video with specified options"""
    try:
        if not video and not youtube_url:
            raise HTTPException(
                status_code=400,
                detail="Debe proporcionar un archivo de video o una URL de YouTube"
            )

        # Initialize processing options
        options = {
            "audioDesc": generate_audiodesc,
            "subtitles": generate_subtitles,
            "voice_type": voice_type,
            "subtitle_format": subtitle_format,
            "quality": output_quality,
            "language": target_language
        }

        # Handle video upload
        if video:
            if not validate_video_file(video):
                raise HTTPException(
                    status_code=400,
                    detail="Formato de video no válido"
                )
            video_id = await video_service.save_video(video)
        else:
            # Handle YouTube URL
            video_id = await video_service.process_youtube_url(youtube_url)

        # Add processing task to background
        background_tasks.add_task(
            video_service.analyze_video,
            video_id=video_id,
            options=options
        )

        return {
            "video_id": video_id,
            "message": "Procesamiento iniciado correctamente"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{video_id}/status")
async def get_processing_status(video_id: str):
    """Get video processing status"""
    try:
        status = await video_service.get_status(video_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{video_id}/result")
async def get_processing_result(video_id: str):
    """Get video processing results"""
    try:
        status = await video_service.get_status(video_id)
        
        if status["status"] != "completed":
            return {
                "status": status["status"],
                "message": "Procesamiento en curso o con errores"
            }
            
        result = {
            "status": "completed",
            "video_id": video_id,
            "outputs": {}
        }
        
        # Get subtitle path if generated
        subtitle_path = await video_service.get_subtitle_path(video_id)
        if subtitle_path:
            result["outputs"]["subtitles"] = str(subtitle_path)
            
        # Get audio description path if generated
        audiodesc_path = await video_service.get_audiodesc_path(video_id)
        if audiodesc_path:
            result["outputs"]["audio_description"] = str(audiodesc_path)
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """Delete video and all associated files"""
    try:
        await video_service.delete_video(video_id)
        return {"message": "Video y archivos asociados eliminados correctamente"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))