from pathlib import Path
import logging
import os
from google.cloud import texttospeech_v1
from typing import Optional

class VoiceSynthesizer:
    """Handles text-to-speech synthesis using Google Cloud TTS."""
    
    def __init__(self, language_code: str = 'es-ES', voice_name: str = 'es-ES-Wavenet-C'):
        self.setup_tts(language_code, voice_name)
    
    def setup_tts(self, language_code: str, voice_name: str) -> None:
        try:
            if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
                logging.warning("GOOGLE_APPLICATION_CREDENTIALS environment variable not set")

            self.tts_client = texttospeech_v1.TextToSpeechClient()
            self.voice_params = texttospeech_v1.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name
            )
            self.audio_config = texttospeech_v1.AudioConfig(
                audio_encoding=texttospeech_v1.AudioEncoding.LINEAR16,
                speaking_rate=1.0,
                pitch=0.0
            )
            logging.info("TTS client initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing TTS client: {str(e)}")
            raise

    def generate_audio(self, text: str, output_path: Path) -> Optional[Path]:
        try:
            if not text:
                logging.error("No text provided for audio generation")
                return None

            synthesis_input = texttospeech_v1.SynthesisInput(text=text)
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice_params,
                audio_config=self.audio_config
            )
            
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as out:
                out.write(response.audio_content)
                logging.info(f"Audio generated successfully: {output_path}")
            
            return output_path
            
        except Exception as e:
            logging.error(f"Error generating audio: {str(e)}")
            return None