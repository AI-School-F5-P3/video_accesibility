import logging
import tempfile
import io
import os
import cv2
import json
import numpy as np
import yt_dlp
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dataclasses import dataclass
from google.cloud import vision
from vertexai.generative_models import GenerativeModel
from pydantic import BaseModel, field_validator
from dotenv import load_dotenv
import torch
import whisper
from pydub import AudioSegment
from pydub.silence import detect_silence

load_dotenv()


from video_processor import move_files_and_process_ffmpeg
# Llamar a la función para mover archivos y procesar video
move_files_and_process_ffmpeg()


model = whisper.load_model("base")
ffmpeg_path = os.getenv("FFMPEG_PATH", "ffmpeg")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

# Configuración de Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuración de Video según UNE153020
@dataclass
class VideoConfig:
    frame_rate: int = 25
    min_scene_duration: float = 2.0
    resolution: Tuple[int, int] = (1920, 1080)
    quality_threshold: float = 0.85

# Metadatos de Video
class YouTubeVideoMetadata(BaseModel):
    url: str
    title: str
    duration: int
    video_format: str
    thumbnail: str
    width: int
    height: int
    fps: Optional[float] = None
    uploader: Optional[str] = None

    @field_validator('video_format')
    @classmethod
    def validate_video_format(cls, v):
        allowed_formats = ['.mp4', '.avi', '.mov', '.mkv', '.webm']
        if v not in allowed_formats:
            raise ValueError(f'Formato no válido: {allowed_formats}')
        return v

# Analizador de Video
class VideoAnalyzer:
    def __init__(self, model: Optional[GenerativeModel] = None, config: Optional[VideoConfig] = None):
        self.model = model
        self.config = config or VideoConfig()
        # Ajustamos los parámetros para mejor detección
        self.silence_threshold = -35  # dB
        self.min_silence_duration = 1.0  # segundos
        self.scene_threshold = 30.0  # umbral para detectar cambios de escena
        self.min_scene_duration = 2.0  # duración mínima de una escena
        self.current_video_path = None

    def detect_scenes(self, video_path: str) -> List[Dict[str, Any]]:
        """
        Detecta escenas en el video usando análisis de diferencia entre frames.
        """
        try:
            self.current_video_path = video_path
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise ValueError("No se pudo abrir el video")

            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            scenes = []
            prev_frame = None
            current_scene_start = 0
            frame_count = 0

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # Convertir frame a escala de grises para comparación
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                if prev_frame is not None:
                    # Calcular diferencia entre frames
                    diff = cv2.absdiff(gray, prev_frame)
                    mean_diff = np.mean(diff)

                    # Detectar cambio de escena
                    if mean_diff > self.scene_threshold:
                        current_time = frame_count / fps
                        if (current_time - current_scene_start) >= self.min_scene_duration:
                            scenes.append({
                                'start_time': current_scene_start,
                                'end_time': current_time,
                                'description': f'Escena {len(scenes) + 1}',
                                'frame_diff': float(mean_diff)
                            })
                            current_scene_start = current_time

                prev_frame = gray
                frame_count += 1

            # Añadir última escena
            if current_scene_start < (total_frames / fps):
                scenes.append({
                    'start_time': current_scene_start,
                    'end_time': total_frames / fps,
                    'description': f'Escena {len(scenes) + 1}',
                    'frame_diff': 0.0
                })

            cap.release()
            return scenes

        except Exception as e:
            logger.error(f"Error en detección de escenas: {str(e)}")
            return []
    
    


    def detect_silence(self, video_path: str) -> List[Dict[str, float]]:
        """
        Detecta silencios en el video usando análisis de audio mejorado.
        """
        try:
            # Extraer audio a archivo temporal
            temp_audio = tempfile.mktemp(suffix='.wav')
            extract_cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-ac', '1',  # Convertir a mono
                '-ar', '44100',  # Frecuencia de muestreo estándar
                '-vn',  # No video
                temp_audio
            ]
            subprocess.run(extract_cmd, capture_output=True, check=True)

            # Cargar audio con pydub para análisis detallado
            audio = AudioSegment.from_wav(temp_audio)
            
            # Detectar silencios usando pydub
            silence_ranges = detect_silence(
                audio,
                min_silence_len=int(self.min_silence_duration * 1000),  # convertir a ms
                silence_thresh=self.silence_threshold
            )

            # Procesar y filtrar silencios
            silences = []
            for start, end in silence_ranges:
                duration = (end - start) / 1000.0  # convertir a segundos
                
                # Solo incluir silencios significativos
                if duration >= self.min_silence_duration:
                    silences.append({
                        'start': start / 1000.0,
                        'end': end / 1000.0,
                        'duration': duration,
                        'is_dialogue_gap': self._is_dialogue_gap(audio, start, end)
                    })

            # Limpiar archivo temporal
            os.remove(temp_audio)
            
            return silences

        except Exception as e:
            logger.error(f"Error en detección de silencios: {str(e)}")
            return []
    def _extract_key_frame(self, start_time: float, end_time: float) -> str:
        """
        Extrae un fotograma clave representativo de una escena para su análisis.
        
        Args:
            start_time (float): Tiempo de inicio de la escena en segundos
            end_time (float): Tiempo de fin de la escena en segundos
            
        Returns:
            str: Ruta al fotograma extraído
        """
        try:
            # Calcular tiempo para extraer el frame (a 1/3 de la escena)
            frame_time = start_time + (end_time - start_time) / 3
            
            # Crear directorio temporal si no existe
            temp_dir = Path(tempfile.gettempdir()) / "video_frames"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Generar nombre de archivo único
            frame_path = str(temp_dir / f"frame_{frame_time:.2f}.jpg")
            
            # Extraer frame usando ffmpeg
            extract_cmd = [
                'ffmpeg', '-y',
                '-ss', str(frame_time),
                '-i', self.current_video_path if hasattr(self, 'current_video_path') else "input_video",
                '-vframes', '1',
                '-q:v', '2',
                frame_path
            ]
            
            # Execute command
            subprocess.run(extract_cmd, capture_output=True, check=True)
            
            return frame_path
        
        except Exception as e:
            logger.error(f"Error extrayendo fotograma clave: {str(e)}")
            return ""
    
    def describe_scene(self, start_time, end_time, scene_info):
        """
        Genera una descripción detallada de una escena específica.
            
        Args:
            start_time (float): Tiempo de inicio del silencio
            end_time (float): Tiempo de fin del silencio
            scene_info (dict): Información de la escena detectada
                
        Returns:
            str: Descripción textual detallada de la escena
        """
        # Extraer fotogramas clave para análisis
        frame_path = self._extract_key_frame(scene_info['start_time'], scene_info['end_time'])
        
        # Añadir información del frame extraído al prompt
        frame_info = f"Frame extraído: {frame_path}" if frame_path else "No se pudo extraer frame"
        
        # Generar prompt detallado para mejorar la descripción
        prompt = f"""
        Actúa como un experto en audiodescripción según la norma UNE 153020.

        Genera una descripción detallada de lo que sucede en esta escena basada en la siguiente información:
        - Tiempo: {start_time:.2f}s a {end_time:.2f}s
        - Elementos visuales: {scene_info.get('visual_elements', [])}
        - Tipo de escena: {scene_info.get('scene_type', 'no especificado')}
        - Personajes detectados: {scene_info.get('characters', [])}
        - {frame_info}
        
        Tu descripción debe:
        1. Describir acciones de personajes
        2. Mencionar cambios importantes de escena
        3. Describir elementos visuales relevantes
        4. Ser concisa pero informativa
        5. Adaptarse para ser narrada en el tiempo disponible ({end_time - start_time:.2f}s)
        6. Seguir todas las pautas de la norma UNE 153020
        """
        
        response = self.model.generate_content(prompt)
        description = response.text.strip()
    
        return description
    
    def _is_dialogue_gap(self, audio: AudioSegment, start_ms: int, end_ms: int) -> bool:
        """
        Determina si un silencio es probablemente una pausa entre diálogos.
        """
        try:
            # Analizar el audio antes y después del silencio
            context_duration = 500  # ms
            
            # Obtener segmentos de audio antes y después del silencio
            before_silence = audio[max(0, start_ms - context_duration):start_ms]
            after_silence = audio[end_ms:min(len(audio), end_ms + context_duration)]
            
            # Calcular volumen promedio antes y después
            before_volume = before_silence.dBFS if len(before_silence) > 0 else -float('inf')
            after_volume = after_silence.dBFS if len(after_silence) > 0 else -float('inf')
            
            # Si hay audio significativo antes y después, probablemente es una pausa de diálogo
            threshold = -45  # dB
            return before_volume > threshold and after_volume > threshold
            
        except Exception as e:
            logger.warning(f"Error analizando gap de diálogo: {str(e)}")
            return False

    def analyze_audio_content(self, video_path: str) -> Dict[str, Any]:
        """
        Analiza el contenido de audio para determinar si hay diálogos o solo música.
        """
        try:
            # Extraer audio para análisis
            temp_audio = tempfile.mktemp(suffix='.wav')
            extract_cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-ac', '1',
                '-ar', '44100',
                temp_audio
            ]
            subprocess.run(extract_cmd, capture_output=True, check=True)
            
            # Cargar audio con pydub
            audio = AudioSegment.from_wav(temp_audio)
            
            # Analizar características del audio
            segments = len(audio) // 1000  # dividir en segmentos de 1 segundo
            dialogue_segments = 0
            music_segments = 0
            
            for i in range(segments):
                segment = audio[i*1000:(i+1)*1000]
                
                # Análisis básico de frecuencias para distinguir voz de música
                if self._has_speech_characteristics(segment):
                    dialogue_segments += 1
                else:
                    music_segments += 1
            
            # Limpiar
            os.remove(temp_audio)
            
            return {
                'has_dialogues': dialogue_segments > (segments * 0.1),  # más del 10% con diálogo
                'has_music': music_segments > (segments * 0.1),
                'dialogue_percentage': (dialogue_segments / segments) * 100 if segments > 0 else 0,
                'music_percentage': (music_segments / segments) * 100 if segments > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error en análisis de contenido de audio: {str(e)}")
            return {
                'has_dialogues': False,
                'has_music': False,
                'error': str(e)
            }
        
    def _has_speech_characteristics(self, audio_segment: AudioSegment) -> bool:
        """
        Determina si un segmento de audio contiene características típicas de voz humana.
        """
        # Implementación básica - se puede mejorar con análisis espectral más detallado
        try:
            # Características típicas de voz humana
            typical_speech_db = -35
            typical_speech_variance = 5
            
            if len(audio_segment) == 0:
                return False
            
            # Obtener valores de dB para el segmento
            db_values = [audio_segment[i:i+100].dBFS for i in range(0, len(audio_segment), 100)]
            db_values = [x for x in db_values if x != float('-inf')]
            
            if not db_values:
                return False
            
            # Calcular estadísticas
            mean_db = sum(db_values) / len(db_values)
            variance = sum((x - mean_db) ** 2 for x in db_values) / len(db_values)
            
            # La voz humana tiende a tener más variación que la música de fondo
            return (typical_speech_db - 10 <= mean_db <= typical_speech_db + 10 and 
                    variance >= typical_speech_variance)
            
        except Exception as e:
            logger.warning(f"Error en análisis de características de voz: {str(e)}")
            return False

# Extractor de Frames
class FrameExtractor:
    def __init__(self, video_path: str, output_dir: str, interval: int = 3):
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.interval = interval
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)

    def extract_frames(self) -> List[Tuple[float, str]]:
        frames_info = []
        frame_interval = int(self.fps * self.interval)
        current_frame = 0
        while True:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = self.cap.read()
            if not ret:
                break
            timestamp = current_frame / self.fps
            frame_path = self.output_dir / f"frame_{timestamp:.2f}.jpg"
            cv2.imwrite(str(frame_path), frame)
            frames_info.append((timestamp, str(frame_path)))
            current_frame += frame_interval
        self.cap.release()
        return frames_info

# Analizador de Frames con Google Vision
class FrameAnalyzer:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def analyze_frame(self, frame_path: str) -> Dict:
        try:
            with io.open(frame_path, 'rb') as image_file:
                content = image_file.read()
            image = vision.Image(content=content)
            response = self.client.annotate_image({'image': image, 'features': [{'type_': vision.Feature.Type.OBJECT_LOCALIZATION}]})
            return {'objects': [{'name': obj.name} for obj in response.localized_object_annotations]}
        except Exception as e:
            logger.error(f"Error analizando frame {frame_path}: {str(e)}")
            return {'error': str(e)}

# Gestor Principal
class YouTubeVideoManager:
    def __init__(self, youtube_url: str):
        self.youtube_url = youtube_url
        self.metadata = self._extract_youtube_metadata()
        self.video_path = None

    def _extract_youtube_metadata(self) -> YouTubeVideoMetadata:
        ydl_opts = {'quiet': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(self.youtube_url, download=False)
            return YouTubeVideoMetadata(
                url=self.youtube_url, title=info_dict.get('title', 'Unknown'), duration=info_dict.get('duration', 0),
                video_format='.mp4', thumbnail=info_dict.get('thumbnail', ''), width=1920, height=1080
            )

    def download_video(self) -> str:
        ydl_opts = {
            'format': 'best',  # Cambiado de 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]' a 'best'
            'outtmpl': os.path.join(tempfile.gettempdir(), '%(title)s.%(ext)s')
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(self.youtube_url, download=True)
            return ydl.prepare_filename(info_dict)
    def analyze_video(self):
        self.video_path = self.download_video()
        extractor = FrameExtractor(self.video_path, "./frames")
        frames = extractor.extract_frames()
        analyzer = FrameAnalyzer()
        results = [analyzer.analyze_frame(frame[1]) for frame in frames]
        with open("video_analysis.json", "w") as f:
            json.dump(results, f, indent=2)
        os.remove(self.video_path)

# Ejecución
if __name__ == "__main__":
    youtube_url = input("Ingresa la URL del video de YouTube: ")
    manager = YouTubeVideoManager(youtube_url)
    manager.analyze_video()
    print("Análisis completado.")