import asyncio
from pathlib import Path
from src.config.setup import Settings
from src.services.subtitle_service import SubtitleService
from src.core.speech_processor import SpeechProcessor

async def test_subtitle_generation():
    try:
        # Initialize settings
        settings = Settings()
        
        # Initialize services
        speech_processor = SpeechProcessor(settings)
        subtitle_service = SubtitleService(settings)
        
        # Path to test video
        video_path = Path("test_video.mp4")  # Asegúrate de tener un video de prueba aquí
        
        if not video_path.exists():
            print(f"Error: No se encuentra el video de prueba en {video_path}")
            return
            
        print("1. Iniciando transcripción del video...")
        transcript = await speech_processor.transcribe_video(video_path)
        
        print(f"2. Transcripción completada. Número de segmentos: {len(transcript.segments)}")
        
        print("3. Generando subtítulos en formato SRT...")
        subtitle_id = await subtitle_service.create_subtitles(
            video_id="test",
            transcript=transcript,
            format="srt"
        )
        
        print(f"4. Subtítulos generados. ID: {subtitle_id}")
        
        print("5. Recuperando subtítulos generados...")
        subtitle_data = await subtitle_service.get_subtitles("test", format="srt")
        
        print("\nPrimeros 3 segmentos de subtítulos:")
        for segment in subtitle_data["segments"][:3]:
            print(f"\nTimestamp: {segment['start']}ms -> {segment['end']}ms")
            print(f"Texto: {segment['text']}")
            
    except Exception as e:
        print(f"Error durante la prueba: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_subtitle_generation())