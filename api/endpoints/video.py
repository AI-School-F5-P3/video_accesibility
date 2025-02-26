from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional
from src.services.video_service import VideoService
from src.core.audio_processor import AudioProcessor
from src.config.setup import Settings
from src.utils.validators import validate_video_file
from pathlib import Path
import uuid
import logging
import shutil
import os

router = APIRouter()
settings = Settings()
video_service = VideoService(settings)
audio_processor = AudioProcessor(settings)

# Importamos el servicio de subtítulos
try:
    from src.services.subtitle_service import SubtitleService
    subtitle_service = SubtitleService(settings)
except ImportError:
    subtitle_service = None
    logging.warning("SubtitleService no encontrado, funcionalidad de subtítulos limitada")

@router.post("/process")
async def process_video(
    background_tasks: BackgroundTasks,
    video: Optional[UploadFile] = File(None),
    youtube_url: Optional[str] = Form(None),
    generate_audiodesc: Optional[bool] = Form(False),
    generate_subtitles: Optional[bool] = Form(False),
    subtitle_format: Optional[str] = Form("srt"),
    target_language: Optional[str] = Form("es"),
):
    """Process video with specified options"""
    try:
        # Generar un ID único para cada solicitud
        video_id = str(uuid.uuid4())
        
        # Verificar que se proporcionó un video o URL
        if not video and not youtube_url:
            raise HTTPException(
                status_code=400,
                detail="Debe proporcionar un archivo de video o una URL de YouTube"
            )
            
        video_dir = Path(f"data/raw/{video_id}")
        video_dir.mkdir(parents=True, exist_ok=True)
        
        if video:
            logging.info(f"Procesando video cargado: {video.filename}")
            # Guardar archivo subido usando el servicio
            video_path = await video_service.save_uploaded_video(video_id, video)
            logging.info(f"Video guardado en: {video_path}")
        elif youtube_url:
            logging.info(f"Procesando video de YouTube: {youtube_url}")
            # Descargar video 
            video_path = await video_service.download_youtube_video(video_id, youtube_url)
            logging.info(f"Video descargado en: {video_path}")
            
        # Crear directorios para resultados
        os.makedirs("data/transcripts", exist_ok=True)
        os.makedirs("data/audio", exist_ok=True)
        
        # Iniciar procesamiento en segundo plano
        if generate_subtitles and subtitle_service:
            logging.info(f"Generando subtítulos para el video {video_id}")
            background_tasks.add_task(
                subtitle_service.generate_subtitles,
                video_id=video_id,
                video_path=video_path,
                target_language=target_language,
                format=subtitle_format
            )
        
        if generate_audiodesc:
            logging.info(f"Generando audiodescripción para el video {video_id}")
            background_tasks.add_task(
                audio_processor.generate_description,
                video_id=video_id,
                video_path=video_path,
                voice_type=target_language
            )
        
        return {
            "video_id": video_id,
            "message": "Procesamiento iniciado correctamente"
        }
        
    except Exception as e:
        logging.error(f"Error en process_video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{video_id}/status")
async def get_processing_status(video_id: str):
    """Get video processing status"""
    try:
        # Verificar estado de los subtítulos
        subtitle_status = {"status": "not_found", "progress": 0}
        if subtitle_service:
            subtitle_status = await subtitle_service.get_status(video_id)
        
        # Verificar estado de la audiodescripción
        audiodesc_status = await audio_processor.get_status(video_id)
        
        # Determinar el estado general
        if subtitle_status.get("status") == "error" or audiodesc_status.get("status") == "error":
            return {
                "status": "error",
                "progress": 0,
                "current_step": "Error en el procesamiento"
            }
        
        if subtitle_status.get("status") == "completed" and audiodesc_status.get("status") == "completed":
            return {
                "status": "completed",
                "progress": 100,
                "current_step": "Procesamiento completado"
            }
        
        # Si ambos están en proceso, promediamos el progreso
        subtitle_progress = subtitle_status.get("progress", 0)
        audiodesc_progress = audiodesc_status.get("progress", 0)
        
        # Si solo se está procesando uno, usamos ese progreso
        total_progress = 0
        count = 0
        
        if subtitle_status.get("status") != "not_found":
            total_progress += subtitle_progress
            count += 1
            
        if audiodesc_status.get("status") != "not_found":
            total_progress += audiodesc_progress
            count += 1
        
        progress = total_progress // count if count > 0 else 0
        
        return {
            "status": "processing",
            "progress": progress,
            "current_step": f"Procesando... ({progress}%)"
        }
            
    except Exception as e:
        logging.error(f"Error getting processing status: {str(e)}")
        return {
            "status": "error",
            "progress": 0,
            "current_step": f"Error: {str(e)}"
        }

@router.get("/{video_id}/result")
async def get_processing_result(video_id: str):
    """Get video processing results"""
    try:
        # Verificar si existe el archivo de video
        video_path = await video_service.get_video_path(video_id)
        if not video_path:
            raise HTTPException(
                status_code=404,
                detail=f"Video no encontrado: {video_id}"
            )
        
        # Crear objeto de resultados
        outputs = {}
        
        # Verificar resultados de subtítulos
        if subtitle_service:
            try:
                # Verificar primero si existe el archivo
                subtitle_path = Path(f"data/transcripts/{video_id}_srt.srt")
                if subtitle_path.exists():
                    outputs["subtitles"] = f"/api/v1/subtitles/{video_id}?download=true"
                else:
                    # Intentar obtener datos
                    subtitle_result = await subtitle_service.get_subtitles(video_id, "srt")
                    if subtitle_result and subtitle_result.get("path"):
                        outputs["subtitles"] = f"/api/v1/subtitles/{video_id}?download=true"
            except Exception as e:
                logging.warning(f"Error getting subtitles: {str(e)}")
        
        # Verificar resultados de audiodescripción
        try:
            # Verificar primero si existe el archivo
            audio_path = Path(f"data/audio/{video_id}_described.mp3")
            if audio_path.exists():
                outputs["audio_description"] = f"/api/v1/audiodesc/{video_id}?download=true"
            else:
                # Intentar obtener datos
                audiodesc_result = await audio_processor.get_audiodescription(video_id)
                if audiodesc_result and audiodesc_result.get("audio_path"):
                    audio_path = Path(audiodesc_result.get("audio_path"))
                    if audio_path.exists():
                        outputs["audio_description"] = f"/api/v1/audiodesc/{video_id}?download=true"
        except Exception as e:
            logging.warning(f"Error getting audio description: {str(e)}")
        
        # Verificar estado si no hay resultados
        if not outputs:
            audiodesc_status = await audio_processor.get_status(video_id)
            subtitle_status = {"status": "not_found"}
            if subtitle_service:
                subtitle_status = await subtitle_service.get_status(video_id)
                
            if audiodesc_status.get("status") == "processing" or subtitle_status.get("status") == "processing":
                return {
                    "status": "processing",
                    "video_id": video_id,
                    "message": "Procesamiento en progreso"
                }
            
            # Si no hay resultados ni procesamiento en curso
            if audiodesc_status.get("status") == "not_found" and subtitle_status.get("status") == "not_found":
                return {
                    "status": "not_found",
                    "video_id": video_id,
                    "message": "No se encontraron resultados para este video"
                }
        
        return {
            "status": "completed",
            "video_id": video_id,
            "outputs": outputs
        }
        
    except Exception as e:
        logging.error(f"Error en get_processing_result: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """Delete video and all associated files"""
    try:
        success = await video_service.delete_video(video_id)
        if not success:
            raise HTTPException(
                status_code=404,
                detail="Error al eliminar el video o archivos asociados"
            )
        
        return {"message": "Video y archivos asociados eliminados correctamente"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))