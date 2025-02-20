from moviepy.editor import VideoFileClip
import whisper
from pathlib import Path
import logging

class VideoProcessor:
    def __init__(self, input_path: str, output_dir: str):
        self.input_path = Path(input_path)
        self.output_dir = Path(output_dir)
        self.logger = logging.getLogger(__name__)
        self._setup()

    def _setup(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model = whisper.load_model("base")

    async def process_video(self):
        try:
            # Extraer audio
            video = VideoFileClip(str(self.input_path))
            audio_path = self.output_dir / f"{self.input_path.stem}_audio.wav"
            video.audio.write_audiofile(str(audio_path))

            # Transcribir audio
            result = self.model.transcribe(str(audio_path))
            
            # Guardar transcripción
            transcript_path = self.output_dir / f"{self.input_path.stem}_transcript.txt"
            with open(transcript_path, 'w', encoding='utf-8') as f:
                f.write(result["text"])

            return {
                "audio_path": str(audio_path),
                "transcript_path": str(transcript_path)
            }

        except Exception as e:
            self.logger.error(f"Error procesando video: {e}")
            raise