from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Optional
from src.services.video_service import VideoService
from src.config.setup import Settings
from src.utils.validators import validate_video_file

router = APIRouter()
settings = Settings()
video_service = VideoService(settings)

# Modelo para las opciones de procesamiento (para videos subidos)
class ProcessOptions(BaseModel):
    generate_audiodesc: bool = False
    generate_subtitles: bool = False
    voice_type: str = "es-ES-F"
    subtitle_format: str = "srt"
    output_quality: str = "high"
    target_language: str = "es"

# Endpoint para subir un video (archivo)
@router.post("/upload")
async def upload_video(video: UploadFile = File(...)):
    if not validate_video_file(video):
        raise HTTPException(status_code=400, detail="Formato de video no válido")
    video_id = await video_service.save_video(video)
    return {"video_id": video_id, "message": "Video subido correctamente"}

# Endpoint para procesar video a partir de URL (por ejemplo, de YouTube)
@router.post("/url")
async def process_video_url(
    youtube_url: str = Form(...),
    generate_audiodesc: bool = Form(False),
    generate_subtitles: bool = Form(False),
    voice_type: str = Form("es-ES-F"),
    subtitle_format: str = Form("srt"),
    output_quality: str = Form("high"),
    target_language: str = Form("es"),
    background_tasks: BackgroundTasks = None
):
    if not youtube_url:
        raise HTTPException(status_code=400, detail="Debe proporcionar una URL de YouTube")
    
    # Se asume que video_service tiene implementado este método para procesar URLs
    video_id = await video_service.process_youtube_url(youtube_url)
    
    options = {
        "generate_audiodesc": generate_audiodesc,
        "generate_subtitles": generate_subtitles,
        "voice_type": voice_type,
        "subtitle_format": subtitle_format,
        "quality": output_quality,
        "language": target_language
    }
    
    background_tasks.add_task(
        video_service.analyze_video,
        video_id=video_id,
        options=options
    )
    
    return {"video_id": video_id, "message": "Procesamiento iniciado correctamente"}

# Endpoint para procesar un video ya subido (recibiendo opciones en JSON)
@router.post("/{video_id}/process")
async def process_video(
    video_id: str,
    options: ProcessOptions,
    background_tasks: BackgroundTasks
):
    background_tasks.add_task(
        video_service.analyze_video,
        video_id=video_id,
        options=options.dict()
    )
    return {"video_id": video_id, "message": "Procesamiento iniciado correctamente"}

@router.get("/{video_id}/status")
async def get_processing_status(video_id: str):
    try:
        status = await video_service.get_status(video_id)
        return status
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/{video_id}/result")
async def get_processing_result(video_id: str):
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
        
        subtitle_path = await video_service.get_subtitle_path(video_id)
        if subtitle_path:
            result["outputs"]["subtitles"] = str(subtitle_path)
            
        audiodesc_path = await video_service.get_audiodesc_path(video_id)
        if audiodesc_path:
            result["outputs"]["audio_description"] = str(audiodesc_path)
            
        processed_video_url = await video_service.get_processed_video_url(video_id)
        if processed_video_url:
            result["outputs"]["processed_video_url"] = str(processed_video_url)
            
        return result
        
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{video_id}")
async def delete_video(video_id: str):
    try:
        await video_service.delete_video(video_id)
        return {"message": "Video y archivos asociados eliminados correctamente"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))
