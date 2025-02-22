import os
from PIL import Image
from google.cloud import texttospeech_v1
from pydub import AudioSegment
from pathlib import Path
import subprocess
import logging

class AudioProcessor:
    def __init__(self, settings):
        self.settings = settings
        # Set credentials before initializing the client
        credentials_path = Path(self.settings.BASE_DIR) / 'api-key.json'
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path)
        
        # Now initialize the client
        try:
            self.tts_client = texttospeech_v1.TextToSpeechClient()
            self.setup_tts()
        except Exception as e:
            logging.error(f"Failed to initialize TTS client: {str(e)}")
            raise
        
    def setup_tts(self):
        self.voice_params = texttospeech_v1.VoiceSelectionParams(
            language_code=self.settings.LANGUAGE_CODE,
            name=self.settings.VOICE_NAME
        )
        self.audio_config = texttospeech_v1.AudioConfig(
            audio_encoding=texttospeech_v1.AudioEncoding.LINEAR16,
            speaking_rate=1.2,
            pitch=0.0
        )
        
    def generate_audio(self, text: str, output_path: Path) -> bool:
        try:
            if not text:
                return False

            synthesis_input = texttospeech_v1.SynthesisInput(text=text)
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice_params,
                audio_config=self.audio_config
            )
            
            with open(output_path, 'wb') as out:
                out.write(response.audio_content)
            
            return True
            
        except Exception as e:
            logging.error(f"Error generating audio: {str(e)}")
            return False
            
    def generate_audio_descriptions(self, descriptions: list) -> list[Path]:
        audio_files = []
        for i, desc in enumerate(descriptions):
            audio_file = self.settings.AUDIO_DIR / f"desc_{i}.wav"
            if self.generate_audio(desc['description'], audio_file):
                audio_files.append(audio_file)
        return audio_files
        
    def merge_audio_descriptions(self, video_path: Path, descriptions: list, 
                               audio_files: list[Path]) -> Path:
        try:
            original_audio = AudioSegment.from_file(str(video_path))
            
            for desc, audio_file in zip(descriptions, audio_files):
                desc_audio = AudioSegment.from_file(str(audio_file))
                start_time = desc['start_time']
                segment_duration = len(desc_audio)
                
                # Split the audio into segments
                pre_segment = original_audio[:start_time]
                target_segment = original_audio[start_time:start_time + segment_duration]
                post_segment = original_audio[start_time + segment_duration:]
                
                # Calculate dynamic volume reduction
                segment_rms = target_segment.rms
                base_rms = original_audio.rms
                volume_reduction = min(-5, -10 * (segment_rms / base_rms))
                
                # Apply effects
                lowered_segment = target_segment + volume_reduction
                faded_out_segment = lowered_segment.fade_out(800)
                faded_in_segment = desc_audio.fade_in(800)
                
                # Merge segments
                combined_segment = faded_out_segment.overlay(
                    faded_in_segment,
                    position=0,
                    gain_during_overlay=-2
                )
                
                original_audio = pre_segment + combined_segment + post_segment
            
            output_path = self.settings.AUDIO_DIR / f"{video_path.stem}_described.wav"
            original_audio.export(str(output_path), format="wav")
            return output_path
            
        except Exception as e:
            logging.error(f"Error merging audio descriptions: {str(e)}")
            raise
            
    def merge_video_audio(self, video_path: Path, audio_path: Path) -> Path:
        try:
            output_path = self.settings.OUTPUT_DIR / f"{video_path.stem}_final.mp4"
            temp_path = self.settings.PROCESSED_DIR / "temp_output.mp4"
            
            # Extract video without audio
            extract_command = [
                'ffmpeg',
                '-i', str(video_path),
                '-an',
                '-c:v', 'copy',
                '-y',
                str(temp_path)
            ]
            
            process = subprocess.run(
                extract_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg error during video extraction: {process.stderr.decode()}")
            
            # Merge video with new audio
            merge_command = [
                'ffmpeg',
                '-i', str(temp_path),
                '-i', str(audio_path),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-shortest',
                '-y', str(output_path)
            ]
            
            process = subprocess.run(
                merge_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if process.returncode != 0:
                raise RuntimeError(f"FFmpeg error during merging: {process.stderr.decode()}")
            
            # Cleanup
            if temp_path.exists():
                temp_path.unlink()
                
            return output_path
                
        except Exception as e:
            logging.error(f"Error merging video and audio: {str(e)}")
            if temp_path.exists():
                temp_path.unlink()
            raise