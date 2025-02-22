

import os
import json
import datetime
import logging
import tempfile
import subprocess
import sys
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from datetime import timedelta

import whisper
from pydub import AudioSegment
from vertexai.generative_models import GenerativeModel
from dotenv import load_dotenv

sys.path.append("src/core")
from video_analyzer import VideoAnalyzer, YouTubeVideoManager
from audio_processor import AudioProcessor, VoiceSynthesizer
from speech_processor import SpeechProcessor
from text_processor import TextProcessor

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AccessibilityPipeline:
    """
    Pipeline unificado para procesamiento de accesibilidad de videos.
    Implementa estándares UNE 153010 (subtítulos) y UNE 153020 (audiodescripción).
    """
    def __init__(self, source: str, output_dir: Optional[str] = None):

        # Máxima duración permitida (10 minutos en segundos)
        self.MAX_DURATION = 600

        self.source = source
        self.output_dir = Path(output_dir) if output_dir else Path("output")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Inicializar Whisper con manejo de errores
        try:
            self.whisper_model = whisper.load_model("base")
            logger.info("Whisper initialized successfully")
        except ImportError as e:
            logger.error("Error importing Whisper. Make sure openai-whisper is installed correctly")
            logger.error("Try: pip install openai-whisper setuptools-rust")
            raise ImportError("Failed to import Whisper. Please install openai-whisper") from e
        except Exception as e:
            logger.error(f"Error initializing Whisper: {str(e)}")
            raise
        
        # Verificar ffmpeg
        if not self._check_ffmpeg():
            raise RuntimeError("ffmpeg not found. Please install ffmpeg and add it to PATH")
        

    def _init_vertex_ai(self):
        """Inicializa el modelo de VertexAI."""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
            vertexai.init(project=project_id, location=location)
            
            self.vertex_model = GenerativeModel("gemini-pro")
        except Exception as e:
            logger.error(f"Error inicializando VertexAI: {e}")
            raise

    # Inicializar modelo de VertexAI
        self._init_vertex_ai()
        
        # Inicializar componentes
        self.video_analyzer = VideoAnalyzer(model=self.vertex_model)
        self.audio_processor = AudioProcessor(model=self.vertex_model)
        self.speech_processor = SpeechProcessor(model=self.vertex_model)
        try:
            self.text_processor = TextProcessor()
            logger.info("TextProcessor initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing TextProcessor: {str(e)}")
            raise
        self.voice_synthesizer = VoiceSynthesizer()
        
        
    
    def _check_ffmpeg(self) -> bool:
        """Verifica si ffmpeg está instalado y disponible."""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True)
            return True
        except FileNotFoundError:
            return False
    

    def process_video(self) -> Dict[str, str]:
        """
        Procesa el video completo generando subtítulos y audiodescripción.
        
        Returns:
            Dict con rutas a los archivos generados
        """
        try:
            # Obtener video
            video_path = self._get_video()
            
            # Verificar duración
            duration = self._get_video_duration(video_path)
            if duration > self.MAX_DURATION:
                raise ValueError(f"Video excede duración máxima de {self.MAX_DURATION/60} minutos")
            
            # Procesar video
            logger.info("Iniciando procesamiento de accesibilidad...")
            
            # Generar subtítulos
            srt_path = self._generate_subtitles(video_path)
            
            # Generar audiodescripción
            audio_desc_path, audio_desc_script = self._generate_audio_description(video_path)
            
            # Generar video final con audiodescripción
            final_video = self._merge_audio_description(video_path, audio_desc_path)
            
            # Preparar archivos para descarga
            output_files = self._prepare_output_files(
                video_path, 
                srt_path,
                audio_desc_path,
                audio_desc_script,
                final_video
            )
            
            return output_files
            
        except Exception as e:
            logger.error(f"Error en el procesamiento: {e}")
            raise

    def _get_video(self) -> str:
        """Obtiene el video desde URL o archivo local."""
        if self.source.startswith(('http://', 'https://')):
            # Descargar de YouTube
            yt_manager = YouTubeVideoManager(self.source)
            video_path = yt_manager.download_video()
        else:
            # Copiar archivo local
            video_path = str(self.temp_dir / "input_video.mp4")
            subprocess.run(['ffmpeg', '-i', self.source, '-c', 'copy', video_path])
        
        return video_path

    def _get_video_duration(self, video_path: str) -> float:
        """Obtiene la duración del video en segundos."""
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
            capture_output=True,
            text=True
        )
        return float(result.stdout)

    def _generate_subtitles(self, video_path: str) -> str:
        """
        Genera subtítulos según UNE 153010.
        
        Returns:
            Ruta al archivo .srt generado
        """
        logger.info("Generando subtítulos...")
        
        # Transcribir audio
        result = self.whisper_model.transcribe(video_path)
        
        # Procesar transcripción para formato SRT
        segments = result["segments"]
        srt_content = []
        
        for i, segment in enumerate(segments, 1):
            # Formatear tiempos
            start = str(timedelta(seconds=int(segment['start']))).replace('.', ',')
            end = str(timedelta(seconds=int(segment['end']))).replace('.', ',')
            
            # Formatear texto según UNE 153010
            text = self.text_processor.format_subtitles(segment['text'])
            
            # Añadir entrada SRT
            srt_content.extend([
                str(i),
                f"{start} --> {end}",
                text,
                ""
            ])
        
        # Guardar archivo SRT
        srt_path = self.output_dir / "subtitles.srt"
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_content))
            
        return str(srt_path)

    def _generate_audio_description(self, video_path: str) -> tuple[str, str]:
        """
        Genera audiodescripción según UNE 153020.
        
        Returns:
            Tuple con ruta al archivo de audio y script
        """
        logger.info("Generando audiodescripción...")
        
        # Detectar escenas y silencios
        scenes = self.video_analyzer.detect_scenes(video_path)
        silences = self.video_analyzer.detect_silence(video_path)
        
        # Generar descripciones de escenas
        descriptions = []
        for silence in silences:
            # Encontrar escena correspondiente
            current_scene = next(
                (s for s in scenes if s['start_time'] <= silence['start'] <= s['end_time']),
                None
            )
            
            if current_scene and silence['duration'] >= 2.0:  # UNE 153020 mínimo
                desc = self.video_analyzer.describe_scene(
                    silence['start'],
                    silence['end'],
                    current_scene
                )
                descriptions.append({
                    'start': silence['start'],
                    'end': silence['end'],
                    'text': desc
                })
        
        # Generar audio para cada descripción
        audio_segments = []
        script_content = []
        
        for desc in descriptions:
            # Formatear texto según UNE 153020
            text = self.text_processor.format_audio_description(
                desc['text'],
                max_duration=desc['end'] - desc['start']
            )
            
            # Generar audio
            audio_file = self.voice_synthesizer.generate_audio(
                text,
                self.temp_dir / f"desc_{desc['start']}.mp3"
            )
            
            if audio_file:
                audio_segments.append({
                    'file': audio_file,
                    'start': desc['start']
                })
                
            # Añadir al script
            script_content.extend([
                f"[{desc['start']:.2f} - {desc['end']:.2f}]",
                text,
                ""
            ])
        
        # Guardar script
        script_path = self.output_dir / "audio_description_script.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_content))
        
        # Combinar segmentos de audio
        final_audio = self._combine_audio_segments(audio_segments)
        
        return str(final_audio), str(script_path)

    def _combine_audio_segments(self, segments: List[Dict[str, Any]]) -> str:
        """Combina segmentos de audio con silencios entre ellos."""
        combined = AudioSegment.silent(duration=0)
        
        for segment in segments:
            # Añadir silencio hasta el tiempo de inicio
            silence_duration = int(segment['start'] * 1000) - len(combined)
            if silence_duration > 0:
                combined += AudioSegment.silent(duration=silence_duration)
            
            # Añadir segmento de audio
            audio = AudioSegment.from_file(segment['file'])
            combined += audio
        
        # Guardar audio final
        output_path = self.output_dir / "audio_description.mp3"
        combined.export(output_path, format="mp3")
        
        return str(output_path)

    def _merge_audio_description(self, video_path: str, audio_desc_path: str) -> str:
        """
        Combina el video original con la audiodescripción.
        
        Returns:
            Ruta al video final
        """
        logger.info("Generando video final con audiodescripción...")
        
        output_path = self.output_dir / "video_with_audio_description.mp4"
        
        # Mezclar audio original con audiodescripción
        subprocess.run([
            'ffmpeg', '-y',
            '-i', video_path,
            '-i', audio_desc_path,
            '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first[aout]',
            '-map', '0:v',
            '-map', '[aout]',
            '-c:v', 'copy',
            str(output_path)
        ], check=True)
        
        return str(output_path)

    def _prepare_output_files(self, 
                            video_path: str,
                            srt_path: str,
                            audio_desc_path: str,
                            script_path: str,
                            final_video_path: str) -> Dict[str, str]:
        """Prepara y organiza archivos finales."""
        # Copiar archivos a directorio final
        final_paths = {
            'subtitles': srt_path,
            'audio_description': audio_desc_path,
            'audio_description_script': script_path,
            'video_with_audio_description': final_video_path
        }
        
        # Generar archivo de metadatos
        metadata = {
            'processed_at': str(datetime.now()),
            'source': self.source,
            'standards': {
                'subtitles': 'UNE 153010',
                'audio_description': 'UNE 153020'
            },
            'files': final_paths
        }
        
        metadata_path = self.output_dir / 'metadata.json'
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        final_paths['metadata'] = str(metadata_path)
        return final_paths

if __name__ == "__main__":
    # Ejemplo de uso
    source = input("Introduce URL de YouTube o ruta al video: ")
    pipeline = AccessibilityPipeline(source)
    
    try:
        output_files = pipeline.process_video()
        print("\n✅ Procesamiento completado!")
        print("\nArchivos generados:")
        for key, path in output_files.items():
            print(f"- {key}: {path}")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")