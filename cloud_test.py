import os
from dotenv import load_dotenv
import sys
from pathlib import Path
import cv2
from PIL import Image as PILImage
import io
from pydub import AudioSegment
from pydub.silence import detect_silence
from google.cloud import texttospeech_v1
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Image
import logging
from datetime import datetime
import yt_dlp

load_dotenv()

class VideoDescriptionGenerator:
    def __init__(self, language_code='es-ES'):
        self.setup_directories()
        self.setup_models()
        self.setup_tts(language_code)
        
    def setup_directories(self):
        """Create necessary directories for input and output files"""
        self.base_dir = Path.cwd()
        self.input_dir = self.base_dir / "input_videos"
        self.output_dir = self.base_dir / "output_audio"
        self.temp_dir = self.base_dir / "temp"
        
        for directory in [self.input_dir, self.output_dir, self.temp_dir]:
            directory.mkdir(exist_ok=True)
            
        logging.info("Directorios creados exitosamente")

    def setup_models(self):
        """Initialize the Gemini Vision model"""
        try:
            logging.info("Inicializando modelo Gemini Vision...")
            
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            if not project_id:
                raise ValueError("Variable de entorno GOOGLE_CLOUD_PROJECT no establecida")
            
            location = "us-central1"
            vertexai.init(project=project_id, location=location)
            
            self.vision_model = GenerativeModel("gemini-pro-vision")
            
            logging.info("Modelo Gemini Vision inicializado exitosamente")
        except Exception as e:
            logging.error(f"Error al inicializar el modelo Gemini: {str(e)}")
            raise

    def setup_tts(self, language_code):
        """Initialize Google Cloud Text-to-Speech client"""
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
            logging.info("Cliente TTS inicializado exitosamente")
        except Exception as e:
            logging.error(f"Error al inicializar el cliente TTS: {str(e)}")
            raise

    def extract_frame(self, video_path: Path, timestamp_ms: int) -> PILImage.Image:
        """Extract a frame from the video at given timestamp"""
        try:
            cap = cv2.VideoCapture(str(video_path))
            cap.set(cv2.CAP_PROP_POS_MSEC, timestamp_ms)
            ret, frame = cap.read()
            cap.release()

            if not ret:
                logging.error("Error al extraer el frame del video")
                return None

            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = PILImage.fromarray(frame_rgb)
            return pil_image
            
        except Exception as e:
            logging.error(f"Error al extraer frame: {str(e)}")
            return None

    def generate_description(self, image: PILImage.Image, max_duration_ms: int) -> str:
        """Generate description and ensure it fits within the silent duration"""
        try:
            if image is None:
                return ""

            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG')
            img_byte_arr = img_byte_arr.getvalue()

            vertex_image = Image.from_bytes(img_byte_arr)

            prompt = """Actúa como un experto en audiodescripción siguiendo la norma UNE 153020. 
            Describe la escena siguiente en lenguaje claro y fluido. Describe la escena siguiente considerando estas pautas:

            - Usa lenguaje sencillo, fluido y directo
            - Describe solo lo que se ve, sin interpretar ni adelantar sucesos
            - Utiliza presente de indicativo
            - Sé preciso en la descripción de lugares, personas y acciones
            - No uses expresiones como "se ve", "aparece" o "podemos ver"
            - Comienza la descripción con "En esta escena"
            - Prioriza: Qué (acción), Quién, Cómo, Dónde
            - Mantén la descripción en máximo 2 frases
            - Evita redundancias con el audio original
            - No uses metáforas ni lenguaje poético.
            """

            response = self.vision_model.generate_content(
                [prompt, vertex_image],
                generation_config={
                    "max_output_tokens": 100,  # Limit output tokens to avoid excessive text
                    "temperature": 0.4,
                    "top_p": 0.8,
                    "top_k": 40
                }
            )

            if response and response.text:
                description = response.text.strip()
                words = description.split()

                # Estimate the max words that can fit in the available silence (Assuming ~150 words per minute)
                max_words = int((max_duration_ms / 1000) * 2.5)  # ~2.5 words per second

                if len(words) > max_words:
                    description = " ".join(words[:max_words]) + "."

                logging.info(f"Descripción ajustada: {description}")
                return description

            return ""

        except Exception as e:
            logging.error(f"Error al generar la descripción: {str(e)}")
            return ""


    def generate_audio(self, text: str, output_path: Path) -> bool:
        """Generate speech from text using Google Cloud TTS"""
        try:
            if not text:
                logging.error("No se proporcionó texto para generar audio")
                return False

            synthesis_input = texttospeech_v1.SynthesisInput(text=text)
            
            response = self.tts_client.synthesize_speech(
                input=synthesis_input,
                voice=self.voice_params,
                audio_config=self.audio_config
            )
            
            with open(output_path, 'wb') as out:
                out.write(response.audio_content)
                logging.info(f"Audio generado exitosamente: {output_path}")
            
            return True
            
        except Exception as e:
            logging.error(f"Error al generar audio: {str(e)}")
            return False

    def detect_silent_scenes(self, video_path: Path) -> list[tuple[float, float]]:
        """Detect silent segments in the video"""
        try:
            audio = AudioSegment.from_file(str(video_path))
            
            silent_ranges = detect_silence(
                audio,
                min_silence_len=2500,  # 2.5 seconds minimum
                silence_thresh=-35,
                seek_step=100
            )
            
            silent_ranges = [
                (start, end) for start, end in silent_ranges 
                if (end - start) >= 2500
            ]
            
            logging.info(f"Se detectaron {len(silent_ranges)} escenas silenciosas")
            return silent_ranges
            
        except Exception as e:
            logging.error(f"Error al detectar escenas silenciosas: {str(e)}")
            return []

    def validate_video(self, video_path: Path) -> tuple[bool, str]:
        """Validate the input video file"""
        try:
            if not video_path.exists():
                return False, "El archivo de video no existe"

            cap = cv2.VideoCapture(str(video_path))
            if not cap.isOpened():
                return False, "No se puede abrir el archivo de video"

            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            
            cap.release()

            if duration > 300:  # 5 minutes
                return False, "El video es demasiado largo. La duración máxima es de 5 minutos"

            return True, "Video válido"
            
        except Exception as e:
            return False, f"Error al validar video: {str(e)}"

    def process_video(self, input_path: Path) -> Path:
        """Process the video and generate audio descriptions"""
        try:
            is_valid, message = self.validate_video(input_path)
            if not is_valid:
                raise ValueError(message)

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"{input_path.stem}_{timestamp}_described.wav"

            silent_ranges = self.detect_silent_scenes(input_path)
            descriptions = []
            
            for i, (start_time, end_time) in enumerate(silent_ranges):
                logging.info(f"Procesando escena silenciosa {i+1}/{len(silent_ranges)}")

                mid_time = (start_time + end_time) // 2
                frame = self.extract_frame(input_path, mid_time)

                if frame:
                    duration_ms = end_time - start_time  # Calculate silence duration
                    description = self.generate_description(frame, duration_ms)  # Pass duration
                    if description:
                        audio_file = self.temp_dir / f"desc_{i}.wav"
                        if self.generate_audio(description, audio_file):
                            descriptions.append({
                                'start_time': start_time,
                                'end_time': end_time,
                                'description': description,
                                'audio_file': audio_file
                            })
                            logging.info(f"Descripción {i+1} generada: {description}")


            if descriptions:
                self.merge_audio_descriptions(input_path, descriptions, output_path)
            else:
                logging.error("No se generaron descripciones válidas")
                return None
            
            # Cleanup
            for desc in descriptions:
                if os.path.exists(desc['audio_file']):
                    os.remove(desc['audio_file'])

            logging.info(f"Video procesado exitosamente. Guardado en: {output_path}")
            return output_path
            
        except Exception as e:
            logging.error(f"Error al procesar video: {str(e)}")
            return None

    def merge_audio_descriptions(self, video_path: Path, descriptions: list, output_path: Path):
        """Merge original video audio with generated descriptions using fade in/out"""
        try:
            original_audio = AudioSegment.from_file(str(video_path))

            for desc in descriptions:
                desc_audio = AudioSegment.from_file(str(desc['audio_file']))

                start_time = desc['start_time']
                segment_duration = len(desc_audio)

                # Extract the segment of original audio where the description will be inserted
                pre_segment = original_audio[:start_time]
                target_segment = original_audio[start_time:start_time + segment_duration]
                post_segment = original_audio[start_time + segment_duration:]

                # Apply fade out and fade in (e.g., 500ms fades)
                faded_out_segment = target_segment.fade_out(500)
                faded_in_segment = desc_audio.fade_in(500)

                # Combine everything: original before, faded out, description, faded in original
                original_audio = pre_segment + faded_out_segment.overlay(faded_in_segment) + post_segment

            # Export final merged audio
            original_audio.export(str(output_path), format="wav")
            logging.info(f"Audio merged successfully: {output_path}")

        except Exception as e:
            logging.error(f"Error merging audio descriptions: {str(e)}")


def main():
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('video_description.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        if not os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            raise ValueError("Credenciales de Google Cloud no encontradas. Configure la variable GOOGLE_APPLICATION_CREDENTIALS")
        
        if not os.getenv('GOOGLE_CLOUD_PROJECT'):
            raise ValueError("ID del proyecto de Google Cloud no encontrado. Configure la variable GOOGLE_CLOUD_PROJECT")
        
        print("\n=== Generador de Audiodescripción UNE 153020 ===")
        generator = VideoDescriptionGenerator()
        
        if len(sys.argv) > 1:
            input_source = sys.argv[1]
        else:
            input_source = input("\nIngrese URL de YouTube o ruta del video local: ").strip()
        
        if input_source.startswith(('http://', 'https://', 'www.')):
            print("\nDescargando video de YouTube...")
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': str(generator.input_dir / '%(title)s.%(ext)s'),
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(input_source, download=True)
                video_path = Path(ydl.prepare_filename(info))
        else:
            video_path = Path(input_source)
        
        print(f"\nProcesando video: {video_path}")
        output_path = generator.process_video(video_path)
        
        if output_path:
            print(f"\n¡Procesamiento completado!")
            print(f"Archivo de salida: {output_path}")
            print("\nNota: El archivo de salida está en formato WAV y contiene el audio original")
            print("      del video con las descripciones insertadas en los momentos de silencio.")
        else:
            print("\nError al procesar el video. Revise el archivo 'video_description.log' para más detalles.")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        logging.error(f"Error en la ejecución principal: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()