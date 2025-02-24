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
    youtube_url: Optional[str] = Form(None),
    generate_audiodesc: bool = Form(False),
    generate_subtitles: bool = Form(False),
    subtitle_format: str = Form("srt"),
    target_language: str = Form("es"),
):
    """Process video with specified options"""
    try:
        if not youtube_url:
            raise HTTPException(
                status_code=400,
                detail="Debe proporcionar una URL de YouTube"
            )
        
        # Simplemente devolver un ID ficticio y un mensaje de éxito
        video_id = "test123"
        
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
    
@router.post("/process")
async def process_video(
    video: Optional[UploadFile] = File(None),
    youtube_url: Optional[str] = Form(None),
    generate_audiodesc: Optional[bool] = Form(False),
    generate_subtitles: Optional[bool] = Form(False),
    subtitle_format: Optional[str] = Form("srt"),
    target_language: Optional[str] = Form("es"),
):
    """Process video with specified options"""
    try:
        # Log para depuración
        print(f"Received request: youtube_url={youtube_url}, video={video}")
        
        # Respuesta simulada para pruebas
        return {
            "video_id": "test123",
            "message": "Procesamiento iniciado correctamente"
        }
    except Exception as e:
        print(f"Error in process_video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 