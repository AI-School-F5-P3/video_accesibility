from typing import Dict, List, Optional, Any
import numpy as np
from vertexai.generative_models import GenerativeModel
from dataclasses import dataclass
import logging
from pathlib import Path
from pydub import AudioSegment
import speech_recognition as sr
from ..core.error_handler import ProcessingError

logger = logging.getLogger(__name__)

@dataclass
class AudioConfig:
    """Audio processing configuration following UNE standards."""
    sample_rate: int = 44100
    min_silence_duration: float = 2.0  # UNE153020 requirement
    min_silence_db: float = -40.0
    max_background_noise: float = -35.0
    frame_size: int = 1024

class AudioProcessor:
    """
    Handles audio processing and silence detection for audio descriptions.
    Implements UNE153020 standards for audio accessibility.
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the audio processor with AI Studio integration.
        
        Args:
            config: Audio processing configuration
        """
        self.config = config
        self.recognizer = sr.Recognizer()
        self.min_silence_len = config.get('min_silence_len', 1000)
        self.silence_thresh = config.get('silence_thresh', -40)
        self.temp_dir = Path(config.get('temp_dir', 'temp'))
        self.temp_dir.mkdir(exist_ok=True)
        self._initialize_processor()
    
    def _initialize_processor(self) -> None:
        """Initialize internal processing components."""
        if not self.model:
            self.model = self._get_default_model()
    
    def _get_default_model(self) -> GenerativeModel:
        """Provides a default model for testing."""
        class MockModel:
            def generate_content(self, *args, **kwargs):
                return type('Response', (), {'text': 'Mock audio analysis'})()
        return MockModel()
    
    async def extract_audio(self, video_path: Path) -> Path:
        """Extrae el audio del video"""
        try:
            audio_path = self.temp_dir / f"{video_path.stem}_audio.wav"
            audio = AudioSegment.from_file(str(video_path))
            audio.export(str(audio_path), format="wav")
            return audio_path
        except Exception as e:
            logger.error(f"Error extrayendo audio: {e}")
            raise ProcessingError("AUDIO_EXTRACTION_ERROR", str(e))

    async def detect_silence(self, audio_path: Path) -> List[Dict[str, float]]:
        """Detecta períodos de silencio en el audio"""
        try:
            audio = AudioSegment.from_wav(str(audio_path))
            silence_ranges = []
            
            # Detectar silencios usando pydub
            segments = audio.detect_silence(
                min_silence_len=self.min_silence_len,
                silence_thresh=self.silence_thresh
            )
            
            for start, end in segments:
                silence_ranges.append({
                    'start': start / 1000.0,  # Convertir a segundos
                    'end': end / 1000.0,
                    'duration': (end - start) / 1000.0
                })
            
            return silence_ranges
        except Exception as e:
            logger.error(f"Error detectando silencios: {e}")
            raise ProcessingError("SILENCE_DETECTION_ERROR", str(e))

    async def transcribe_audio(self, audio_path: Path) -> str:
        """Transcribe el audio a texto"""
        try:
            with sr.AudioFile(str(audio_path)) as source:
                audio = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio, language='es-ES')
                return text
        except Exception as e:
            logger.error(f"Error en transcripción: {e}")
            raise ProcessingError("TRANSCRIPTION_ERROR", str(e))

    async def analyze_audio_segments(self, audio_path: Path) -> List[Dict[str, Any]]:
        """Analiza segmentos de audio para audiodescripción"""
        try:
            audio = AudioSegment.from_wav(str(audio_path))
            silence_ranges = await self.detect_silence(audio_path)
            segments = []
            
            for i, silence in enumerate(silence_ranges[:-1]):
                segment = {
                    'start': silence['end'],
                    'end': silence_ranges[i + 1]['start'],
                    'duration': silence_ranges[i + 1]['start'] - silence['end'],
                    'has_speech': True
                }
                segments.append(segment)
            
            return segments
        except Exception as e:
            logger.error(f"Error analizando segmentos: {e}")
            raise ProcessingError("SEGMENT_ANALYSIS_ERROR", str(e))

    def cleanup(self):
        """Limpia archivos temporales"""
        try:
            for file in self.temp_dir.glob("*"):
                file.unlink()
        except Exception as e:
            logger.warning(f"Error limpiando archivos temporales: {e}")