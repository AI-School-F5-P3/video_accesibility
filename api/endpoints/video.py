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
from src.models import schemas

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

# Importamos el servicio de audiodescripción
try:
    from src.services.audiodesc_service import AudiodescService
    audiodesc_service = AudiodescService(settings)
except ImportError:
    audiodesc_service = None
    logging.warning("AudiodescService no encontrado, funcionalidad de audiodescripción limitada")

@router.post("/process")
async def process_video(
    background_tasks: BackgroundTasks,
    video: Optional[UploadFile] = File(None),
    youtube_url: Optional[str] = Form(None),
    generate_audiodesc: Optional[bool] = Form(False),
    generate_subtitles: Optional[bool] = Form(False),
    subtitle_format: Optional[str] = Form("srt"),
    target_language: Optional[str] = Form("es"),
    integrate_audiodesc: Optional[bool] = Form(False),
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
        os.makedirs("data/processed", exist_ok=True)
        
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
            
            # Si se solicita integrar audiodescripciones, programar la tarea para cuando
            # termine la generación de audiodescripciones
            if integrate_audiodesc:
                logging.info(f"Se renderizará el video con audiodescripciones integradas cuando estén listas")
                background_tasks.add_task(
                    video_service.wait_and_render_with_audiodesc,
                    video_id=video_id
                )
        
        return {
            "video_id": video_id,
            "message": "Procesamiento iniciado correctamente",
            "status": "processing"
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
        
        # Verificar estado del renderizado
        render_status = await video_service.get_status(video_id)
        
        # Determinar el estado general
        if render_status.get("status") == "error" or subtitle_status.get("status") == "error" or audiodesc_status.get("status") == "error":
            return {
                "status": "error",
                "progress": 0,
                "current_step": "Error en el procesamiento"
            }
        
        # Si el renderizado está activo, ese es el estado principal
        if render_status.get("status") == "processing":
            return {
                "status": "processing",
                "progress": render_status.get("progress", 0),
                "current_step": render_status.get("current_step", "Renderizando video...")
            }
        
        if render_status.get("status") == "completed":
            return {
                "status": "completed",
                "progress": 100,
                "current_step": "Video con audiodescripciones listo"
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
        
        # Verificar resultados de video con audiodescripciones integradas
        try:
            rendered_video_path = Path(f"data/processed/{video_id}_with_audiodesc.mp4")
            if rendered_video_path.exists():
                outputs["integrated_video"] = f"/api/v1/videos/{video_id}/integrated?download=true"
        except Exception as e:
            logging.warning(f"Error getting integrated video: {str(e)}")
        
        # Verificar estado si no hay resultados
        if not outputs:
            audiodesc_status = await audio_processor.get_status(video_id)
            subtitle_status = {"status": "not_found"}
            render_status = await video_service.get_status(video_id)
            
            if subtitle_service:
                subtitle_status = await subtitle_service.get_status(video_id)
                
            if (audiodesc_status.get("status") == "processing" or 
                subtitle_status.get("status") == "processing" or
                render_status.get("status") == "processing"):
                return {
                    "status": "processing",
                    "video_id": video_id,
                    "message": "Procesamiento en progreso"
                }
            
            # Si no hay resultados ni procesamiento en curso
            if (audiodesc_status.get("status") == "not_found" and 
                subtitle_status.get("status") == "not_found" and
                render_status.get("status") == "not_found"):
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

@router.post("/{video_id}/render", response_model=schemas.VideoRenderResponse)
async def render_video_with_audiodesc(video_id: str, background_tasks: BackgroundTasks):
    """
    Genera un nuevo video que integra el original con las audiodescripciones generadas.
    """
    try:
        # Verificar que el video existe
        video_path = await video_service.get_video_path(video_id)
        if not video_path:
            raise HTTPException(status_code=404, detail="Video no encontrado")
        
        # Verificar que las audiodescripciones existen
        audio_desc_path = Path(f"data/audio/{video_id}_described.mp3")
        if not audio_desc_path.exists():
            # Verificar si están en proceso
            audiodesc_status = await audio_processor.get_status(video_id)
            if audiodesc_status.get("status") == "processing":
                # Las audiodescripciones están en proceso, programar renderizado para después
                background_tasks.add_task(
                    video_service.wait_and_render_with_audiodesc,
                    video_id=video_id
                )
                return {"status": "queued", "message": "Video se renderizará cuando las audiodescripciones estén listas"}
            else:
                raise HTTPException(status_code=404, 
                                  detail="No se encontraron audiodescripciones para este video. Generelas primero.")
        
        # Iniciar proceso de renderizado en segundo plano
        background_tasks.add_task(
            video_service.render_with_audiodesc,
            video_id=video_id
        )
        
        return {"status": "processing", "message": "Renderizado de video iniciado"}
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error al renderizar video: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error al renderizar video: {str(e)}")

@router.get("/{video_id}/integrated")
async def get_integrated_video(video_id: str, download: bool = False):
    """
    Obtiene el video con audiodescripciones integradas
    """
    try:
        # Verificar que el video renderizado existe
        rendered_path = Path(f"data/processed/{video_id}_with_audiodesc.mp4")
        if not rendered_path.exists():
            # Verificar si está en proceso
            render_status = await video_service.get_status(video_id)
            if render_status.get("status") == "processing":
                return {"status": "processing", "message": "El video está siendo renderizado"}
            else:
                raise HTTPException(status_code=404, 
                                  detail="No se encontró el video con audiodescripciones integradas")
        
        # Si se solicita descarga, devolver el archivo
        if download:
            from fastapi.responses import FileResponse
            return FileResponse(
                path=rendered_path,
                filename=f"video_with_audiodesc_{video_id}.mp4",
                media_type="video/mp4"
            )
        
        # De lo contrario, devolver información sobre el video
        file_size = rendered_path.stat().st_size / (1024 * 1024)  # Tamaño en MB
        
        return {
            "status": "completed",
            "video_id": video_id,
            "path": str(rendered_path),
            "file_size_mb": round(file_size, 2),
            "download_url": f"/api/v1/videos/{video_id}/integrated?download=true"
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        logging.error(f"Error al obtener video integrado: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@router.post("/cleanup")
async def cleanup_temp_files():
    """
    Limpia archivos temporales y carpetas vacías
    """
    try:
        deleted_files = []
        deleted_dirs = []
        
        # Limpiar carpetas vacías en data/raw
        raw_dir = Path("data/raw")
        if raw_dir.exists():
            for subdir in raw_dir.iterdir():
                if subdir.is_dir():
                    # Verificar si está vacía
                    files = list(subdir.glob("*"))
                    if not files:
                        try:
                            subdir.rmdir()
                            deleted_dirs.append(str(subdir))
                        except:
                            pass
        
        # Limpiar carpeta test123
        test_dir = Path("data/raw/test123")
        if test_dir.exists():
            import shutil
            try:
                shutil.rmtree(test_dir)
                deleted_dirs.append(str(test_dir))
            except:
                pass
                
        test_dir = Path("data/processed/test123")
        if test_dir.exists():
            import shutil
            try:
                shutil.rmtree(test_dir)
                deleted_dirs.append(str(test_dir))
            except:
                pass
        
        return {
            "status": "success",
            "message": "Limpieza completada",
            "deleted_files": deleted_files,
            "deleted_dirs": deleted_dirs
        }
        
    except Exception as e:
        logging.error(f"Error en cleanup_temp_files: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))