from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import Optional
from src.services.video_service import VideoService
from src.config.setup import Settings
from src.utils.validators import validate_video_file
from pathlib import Path

router = APIRouter()
settings = Settings()
video_service = VideoService(settings)

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
        print(f"Procesando: video={video is not None}, youtube_url={youtube_url}")
        
        # Permitir cualquiera de las dos opciones pero al menos una
        if not video and not youtube_url:
            raise HTTPException(
                status_code=400,
                detail="Debe proporcionar un archivo de video o una URL de YouTube"
            )
        
        # Simulación de ID para pruebas
        video_id = "test123"
        
        # Crear archivos simulados para pruebas (solo si se solicitan subtítulos)
        if generate_subtitles:
            subtitle_dir = Path("data/transcripts")
            subtitle_dir.mkdir(parents=True, exist_ok=True)
            
            with open(f"data/transcripts/{video_id}_srt.srt", "w") as f:
                f.write("1\n00:00:01,000 --> 00:00:05,000\nEste es un subtítulo de prueba\n\n")
                f.write("2\n00:00:06,000 --> 00:00:10,000\nGenerado para probar la funcionalidad\n\n")
        
        return {
            "video_id": video_id,
            "message": "Procesamiento iniciado correctamente"
        }
        
    except Exception as e:
        print(f"Error en process_video: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{video_id}/status")
async def get_processing_status(video_id: str):
    """Get video processing status"""
    # Simulación para pruebas - Devuelve completed después de unos segundos
    import time
    from datetime import datetime
    
    timestamp = int(datetime.now().timestamp())
    
    # Simula que se completa después de 5 segundos
    if timestamp % 10 >= 5:
        return {
            "status": "completed",
            "progress": 100,
            "current_step": "Procesamiento completado"
        }
    else:
        progress = min(90, (timestamp % 10) * 10)  # Progreso entre 0 y 90%
        return {
            "status": "processing",
            "progress": progress,
            "current_step": f"Procesando video ({progress}%)..."
        }

@router.get("/{video_id}/result")
async def get_processing_result(video_id: str):
    """Get video processing results"""
    try:
        # Verificar si existe el archivo de subtítulos simulado
        subtitle_path = Path(f"data/transcripts/{video_id}_srt.srt")
        
        outputs = {}
        if subtitle_path.exists():
            outputs["subtitles"] = f"/api/v1/subtitles/{video_id}?download=true"
        
        # Simular audiodescripción (para pruebas)
        outputs["audio_description"] = f"/api/v1/audiodesc/{video_id}?download=true"
        
        return {
            "status": "completed",
            "video_id": video_id,
            "outputs": outputs
        }
        
    except Exception as e:
        print(f"Error en get_processing_result: {str(e)}")
        raise HTTPException(status_code=404, detail=str(e))

@router.delete("/{video_id}")
async def delete_video(video_id: str):
    """Delete video and all associated files"""
    try:
        # En versión simulada, solo eliminamos el archivo de subtítulos si existe
        subtitle_path = Path(f"data/transcripts/{video_id}_srt.srt")
        if subtitle_path.exists():
            subtitle_path.unlink()
        
        return {"message": "Video y archivos asociados eliminados correctamente"}
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))