import asyncio
from pathlib import Path
import yt_dlp
from src.config.setup import Settings
from src.services.subtitle_service import SubtitleService
from src.core.speech_processor import SpeechProcessor

async def download_video(url: str, output_path: Path) -> bool:
    """Download video from YouTube"""
    try:
        ydl_opts = {
            'format': 'best[height<=720]',  # Limitar a 720p para pruebas
            'outtmpl': str(output_path),
            'quiet': True,
            'no_warnings': True
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return True
    except Exception as e:
        print(f"Error descargando el video: {str(e)}")
        return False

async def test_subtitle_generation(video_url: str):
    try:
        # Initialize settings
        settings = Settings()
        
        # Initialize services
        speech_processor = SpeechProcessor(settings)
        subtitle_service = SubtitleService(settings)
        
        # Preparar path para el video
        video_path = settings.RAW_DIR / "test_video.mp4"
        
        print("1. Descargando video de prueba...")
        success = await download_video(video_url, video_path)
        
        if not success:
            print("Error: No se pudo descargar el video")
            return
            
        print("2. Iniciando transcripción del video...")
        transcript = await speech_processor.transcribe_video(video_path)
        
        print(f"3. Transcripción completada. Número de segmentos: {len(transcript.segments)}")
        
        print("4. Generando subtítulos en formato SRT...")
        subtitle_id = await subtitle_service.create_subtitles(
            video_id="test",
            transcript=transcript,
            format="srt"
        )
        
        print(f"5. Subtítulos generados. ID: {subtitle_id}")
        
        print("6. Recuperando subtítulos generados...")
        subtitle_data = await subtitle_service.get_subtitles("test", format="srt")
        
        print("\nPrimeros 3 segmentos de subtítulos:")
        for segment in subtitle_data["segments"][:3]:
            print(f"\nTimestamp: {segment['start']}ms -> {segment['end']}ms")
            print(f"Texto: {segment['text']}")
            
    except Exception as e:
        print(f"Error durante la prueba: {str(e)}")
    finally:
        # Limpiar el video descargado
        if video_path.exists():
            video_path.unlink()

if __name__ == "__main__":
    # URL de ejemplo - un video corto en español
    VIDEO_URL = "https://www.youtube.com/watch?v=EaZNcuodOac&ab_channel=CortometrajesCortos"  # Reemplazar con una URL real
    asyncio.run(test_subtitle_generation(VIDEO_URL))