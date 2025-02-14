import os
from dotenv import load_dotenv
import sys
from pathlib import Path
import cv2
from PIL import Image
import io
from pydub import AudioSegment
from pydub.silence import detect_silence
from google.cloud import texttospeech_v1
import google.generativeai as genai
import logging
from datetime import datetime
import yt_dlp
import json
import subprocess 

load_dotenv()

class VideoDescriptionGenerator:
    def __init__(self, language_code='es-ES'):
        self.setup_logging()
        self.setup_directories()
        self.setup_models()
        self.setup_tts(language_code)
    
    def setup_logging(self):
        log_dir = Path.cwd() / 'logs'
        log_dir.mkdir(exist_ok=True)
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'video_description.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
    def setup_directories(self):
        self.base_dir = Path.cwd()
        self.input_dir = self.base_dir / "input_videos"
        self.output_dir = self.base_dir / "output_audio"
        self.output_video_dir = self.base_dir / "output_video"
        self.text_dir = self.base_dir / "output_text"
        self.temp_dir = self.base_dir / "temp"
        
        for directory in [self.input_dir, self.output_dir, self.output_video_dir, self.text_dir, self.temp_dir]:
            directory.mkdir(exist_ok=True)

    def save_script(self, descriptions: list, output_path: Path):
        script = [{
            'timestamp': desc['start_time'] / 1000,  # Convert to seconds
            'duration': (desc['end_time'] - desc['start_time']) / 1000,
            'text': desc['description']
        } for desc in descriptions]
        
        json_path = self.text_dir / f"{output_path.stem}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(script, f, ensure_ascii=False, indent=2)


    def setup_models(self):
        try:
            api_key = os.getenv('GOOGLE_AI_STUDIO_API_KEY')
            if not api_key:
                raise ValueError("GOOGLE_AI_STUDIO_API_KEY not set")
            
            genai.configure(api_key=api_key)
            self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
            
        except Exception as e:
            logging.error(f"Error initializing Gemini model: {str(e)}")
            raise

    def setup_tts(self, language_code):
        try:
            self.tts_client = texttospeech_v1.TextToSpeechClient()
            self.voice_params = texttospeech_v1.VoiceSelectionParams(
                language_code=language_code,
                name='es-ES-Wavenet-C'
            )
            self.audio_config = texttospeech_v1.AudioConfig(
                audio_encoding=texttospeech_v1.AudioEncoding.LINEAR16,
                speaking_rate=1.0,
                pitch=0.0
            )
        except Exception as e:
            logging.error(f"Error initializing TTS client: {str(e)}")
            raise

    def extract_frame(self, video_path: Path, timestamp_ms: int) -> Image.Image:
        try:
            cap = cv2.VideoCapture(str(video_path))
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
            ret, frame = cap.read()
            cap.release()

            if not ret:
                return None

            return Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            
        except Exception as e:
            logging.error(f"Error extracting frame: {str(e)}")
            return None

    def generate_description(self, image: Image.Image, max_duration_ms: int) -> str:
        try:
            if image is None:
                return ""

            prompt = """Actúa como un experto en audiodescripción siguiendo la norma UNE 153020. 
                Describe la escena siguiente en lenguaje claro y fluido considerando estas pautas:
                - Usa lenguaje sencillo, fluido y directo
                - Describe solo lo que se ve, sin interpretar
                - Utiliza presente de indicativo
                - Sé preciso en la descripción
                - No uses "se ve", "aparece" o "podemos ver"
                - Comienza con "En esta escena"
                - Prioriza: Qué, Quién, Cómo, Dónde
                - Máximo 2 frases
                - Evita redundancias
                - No uses metáforas"""


            response = self.vision_model.generate_content([prompt, image])
            
            if response and response.text:
                description = response.text.strip()
                words = description.split()
                max_words = int((max_duration_ms / 1000) * 2.5)

                if len(words) > max_words:
                    description = " ".join(words[:max_words]) + "."

                return description

            return ""

        except Exception as e:
            logging.error(f"Error generating description: {str(e)}")
            return ""
        
    def merge_video_audio(self, video_path: Path, audio_path: Path) -> Path:
            try:
                output_path = self.output_video_dir / f"{video_path.stem}_final.mp4"
                temp_path = self.temp_dir / "temp_output.mp4"
                
                # First, extract original video without audio
                extract_command = [
                    'ffmpeg',
                    '-i', str(video_path),
                    '-an',  # Remove audio
                    '-c:v', 'copy',  # Copy video codec
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
                
                # Then combine video with new audio
                merge_command = [
                        'ffmpeg',
                        '-i', str(video_path),
                        '-i', str(audio_path),
                        '-map', '0:v:0',  # Ensure video is from input video
                        '-map', '1:a:0',  # Ensure audio is from generated audio
                        '-c:v', 'copy',
                        '-c:a', 'aac',
                        '-b:a', '192k',
                        '-shortest',  # Prevent longer audio than video
                        '-y', str(output_path)
                    ]
                
                process = subprocess.run(
                    merge_command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                
                if process.returncode != 0:
                    raise RuntimeError(f"FFmpeg error during merging: {process.stderr.decode()}")
                
                # Clean up temporary file
                if temp_path.exists():
                    temp_path.unlink()
                    
                return output_path
                    
            except Exception as e:
                logging.error(f"Error merging video and audio: {str(e)}")
                if temp_path.exists():
                    temp_path.unlink()
                raise

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

    def detect_silent_scenes(self, video_path: Path) -> list[tuple[float, float]]:
        try:
            audio = AudioSegment.from_file(str(video_path))
            
            silent_ranges = detect_silence(
                audio,
                min_silence_len=2500,
                silence_thresh=-35,
                seek_step=100
            )
            
            return [(start, end) for start, end in silent_ranges if (end - start) >= 2500]
            
        except Exception as e:
            logging.error(f"Error detecting silent scenes: {str(e)}")
            return []

    def validate_video(self, video_path: Path) -> tuple[bool, str]:
        try:
            if not video_path.exists():
                return False, "Video file does not exist"

            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return False, "Cannot open video file"

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            
            cap.release()

            if duration > 300:
                return False, "Video is too long. Maximum duration is 5 minutes"

            return True, "Valid video"
            
        except Exception as e:
            return False, f"Error validating video: {str(e)}"

    def process_video(self, input_path: Path) -> tuple[Path, Path]:
        try:
            is_valid, message = self.validate_video(input_path)
            if not is_valid:
                raise ValueError(message)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_audio_path = self.output_dir / f"{input_path.stem}_{timestamp}_described.wav"

            silent_ranges = self.detect_silent_scenes(input_path)
            descriptions = []
            
            for i, (start_time, end_time) in enumerate(silent_ranges):
                mid_time = (start_time + end_time) // 2
                frame = self.extract_frame(input_path, mid_time)

                if frame:
                    duration_ms = end_time - start_time
                    description = self.generate_description(frame, duration_ms)
                    if description:
                        audio_file = self.temp_dir / f"desc_{i}.wav"
                        if self.generate_audio(description, audio_file):
                            descriptions.append({
                                'start_time': start_time,
                                'end_time': end_time,
                                'description': description,
                                'audio_file': audio_file
                            })

            if descriptions:
                # Save script first
                self.save_script(descriptions, output_audio_path)
                
                # Merge audio descriptions and get the output path
                described_audio_path = self.merge_audio_descriptions(input_path, descriptions, output_audio_path)
                
                # Merge video with described audio
                final_video_path = self.merge_video_audio(input_path, described_audio_path)
                
                return described_audio_path, final_video_path
            
            return None, None

        except Exception as e:
            logging.error(f"Error processing video: {str(e)}")
            raise

    def merge_audio_descriptions(self, video_path: Path, descriptions: list, output_path: Path) -> Path:
        try:
            original_audio = AudioSegment.from_file(str(video_path))

            for desc in descriptions:
                desc_audio = AudioSegment.from_file(str(desc['audio_file']))
                start_time = desc['start_time']
                segment_duration = len(desc_audio)

                pre_segment = original_audio[:start_time]
                target_segment = original_audio[start_time:start_time + segment_duration]
                post_segment = original_audio[start_time + segment_duration:]

                faded_out_segment = target_segment.fade_out(500)
                faded_in_segment = desc_audio.fade_in(500)

                original_audio = pre_segment + faded_out_segment.overlay(faded_in_segment) + post_segment

            original_audio.export(str(output_path), format="wav")
            return output_path  # Return the path where the audio was saved

        except Exception as e:
            logging.error(f"Error merging audio descriptions: {str(e)}")
            raise

def main():
    try:
        if not os.getenv('GOOGLE_AI_STUDIO_API_KEY'):
            raise ValueError("Google AI Studio API key not found. Set GOOGLE_AI_STUDIO_API_KEY")
        
        print("\n=== UNE 153020 Audio Description Generator ===")
        generator = VideoDescriptionGenerator()
        
        input_source = sys.argv[1] if len(sys.argv) > 1 else input("\nEnter YouTube URL or local video path: ").strip()
        
        if input_source.startswith(('http://', 'https://', 'www.')):
            print("\nDownloading YouTube video...")
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': str(generator.input_dir / '%(title)s.%(ext)s'),
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(input_source, download=True)
                video_path = Path(ydl.prepare_filename(info))
        else:
            video_path = Path(input_source)
        
        print(f"\nProcessing video: {video_path}")
        audio_path, video_path = generator.process_video(video_path)
        
        if audio_path and video_path:
            print(f"\nProcessing completed!")
            print(f"Output audio: {audio_path}")
            print(f"Output video: {video_path}")
            print(f"Output script: {generator.text_dir / f'{audio_path.stem}.json'}")
        else:
            print("\nError processing video. Check 'logs/video_description.log' for details.")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        logging.error(f"Error in main execution: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()