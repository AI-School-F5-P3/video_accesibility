from typing import Optional
from pathlib import Path
from src.core.audio_processor import VoiceSynthesizer
from src.utils.directory_utils import setup_directories
import os


class SpeechService:
    def __init__(self):
        self.directories = setup_directories()
        self.synthesizer = VoiceSynthesizer()
    
    def generate_description_audio(self, description: str, filename: str) -> Optional[Path]:
        output_path = self.directories['audio'] / f"{filename}.wav"
        return self.synthesizer.generate_audio(description, output_path)