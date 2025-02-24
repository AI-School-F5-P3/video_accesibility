from typing import Dict, Any, Optional
import logging
from pathlib import Path
from pydub import AudioSegment
import speech_recognition as sr
from ...core.error_handler import ProcessingError, ErrorType, ErrorDetails

logger = logging.getLogger(__name__)

class AudioProcessor:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.recognizer = sr.Recognizer()
        self.min_silence_len = config.get('min_silence_len', 1000)
        self.silence_thresh = config.get('silence_thresh', -40)
        
    async def extract_audio(self, video_path: Path) -> Path:
        """Extrae el audio del video"""
        try:
            audio_path = video_path.with_suffix('.wav')
            audio = AudioSegment.from_file(str(video_path))
            audio.export(str(audio_path), format="wav")
            return audio_path
        except Exception as e:
            raise ProcessingError(
                ErrorType.AUDIO_PROCESSING_ERROR,
                ErrorDetails(
                    component="AudioProcessor",
                    message=f"Error extrayendo audio: {str(e)}",
                    code="EXTRACTION_ERROR"
                )
            )

    async def transcribe(self, audio_path: Path, language: str = "es-ES") -> str:
        """Transcribe el audio a texto"""
        try:
            with sr.AudioFile(str(audio_path)) as source:
                audio = self.recognizer.record(source)
                return self.recognizer.recognize_google(audio, language=language)
        except Exception as e:
            raise ProcessingError(
                ErrorType.AUDIO_PROCESSING_ERROR,
                ErrorDetails(
                    component="AudioProcessor",
                    message=f"Error en transcripción: {str(e)}",
                    code="TRANSCRIPTION_ERROR"
                )
            )