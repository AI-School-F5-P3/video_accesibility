from typing import Dict, Any, List, Optional, Union
import logging
import subprocess
import os
from pathlib import Path
from gtts import gTTS
from vertexai.generative_models import GenerativeModel
from google.cloud import texttospeech
from src.core.audio_processor import AudioProcessor
from src.core.video_analyzer import VideoAnalyzer
from src.core.speech_processor import SpeechProcessor
from src.core.text_processor import TextProcessor
from src.config.ai_studio_config import AIStudioConfig
from src.config import UNE153010Config, UNE153020Config
from src.api.youtube_api import YouTubeAPI  # Añadir import
import vertexai
from vertexai.language_models import TextGenerationModel

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoPipeline:
    """Pipeline principal para procesar videos y hacerlos accesibles."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        vertexai.init(
            project=os.getenv('GOOGLE_CLOUD_PROJECT'),
            location=os.getenv('VERTEX_LOCATION')
        )
        self.model = TextGenerationModel.from_pretrained("text-bison@001")
        self.youtube_api = YouTubeAPI(config['youtube_api_key'])
        self.text_processor = TextProcessor()
        self.audio_processor = AudioProcessor()
        self.video_analyzer = VideoAnalyzer()
        self._initialize_processors()  # Añadido
        
    async def process_url(
        self, 
        url: str, 
        service_type: str
    ) -> Dict[str, str]:
        """Procesa URL de YouTube"""
        try:
            # Descargar video
            video_data = self.youtube_api.download_video(url)
            
            # Procesar según tipo de servicio
            if service_type == "AUDIODESCRIPCION":
                return await self.audio_service.process_video(
                    video_data['video_path']
                )
            elif service_type == "SUBTITULADO":
                return await self.subtitle_service.generate_subtitles(
                    video_data['video_path']
                )
            else:
                raise ValueError(f"Tipo de servicio no válido: {service_type}")
                
        except Exception as e:
            self.logger.error(f"Error en pipeline: {str(e)}")
            raise

    def _initialize_processors(self) -> None:
        """Inicializa los procesadores necesarios."""
        try:
            self.video_analyzer = VideoAnalyzer(model=self.model)
            self.audio_processor = AudioProcessor(model=self.model)
            self.speech_processor = SpeechProcessor(model=self.model)
            self.text_processor = TextProcessor()
        except Exception as e:
            self.logger.error(f"Error inicializando procesadores: {e}")
            raise

    def process_video(self, video_path: str) -> str:
        try:
            # Convertir string a Path
            video_path = Path(video_path)
            
            # Log información del video
            self._log_video_info(video_path)
            
            # Análisis del video
            analyzer = self.video_analyzer
            scenes = analyzer.detect_scenes(str(video_path))
            
            # Generar descripciones
            descriptions = []
            for scene in scenes:
                self.logger.info(f"Procesando escena con timestamp: {scene.get('timestamp')}")
                
                # Detectar silencios
                silence = analyzer.detect_silence(str(video_path), scene.get('start_time', 0), scene.get('end_time', 0))
                if silence:
                    self.logger.info(f"Silencio encontrado: {silence}")
                    
                    # Calcular duración disponible
                    duration = silence['end'] - silence['start']
                    self.logger.info(f"Duración calculada: {duration}")
                    
                    # Usar un sistema de fallback para descripciones
                    description = None
                    try:
                        description = analyzer.generate_description(str(video_path), scene.get('start_time', 0))
                    except Exception as e:
                        self.logger.warning(f"Error en generación de descripción: {e}")
                    
                    if not description:
                        description = f"Escena en tiempo {scene.get('start_time', 0):.1f} segundos"

                    formatted_description = self.text_processor.format_audio_description(
                        description,
                        max_duration=duration
                    )
                    
                    if formatted_description:  # Verificación adicional
                        descriptions.append({
                            'text': formatted_description,
                            'start': silence['start'],
                            'end': silence['end']
                        })
                        self.logger.info(f"Descripción añadida: {formatted_description}")

            # Asegurar que siempre haya al menos una descripción
            if not descriptions:
                self.logger.warning("No se generaron descripciones - usando descripción por defecto")
                descriptions = [{
                    'text': 'Este video contiene escenas sin diálogo',
                    'start': 0,
                    'end': 3
                }]

            # Verificar que hay texto antes de procesar
            if not any(d['text'] for d in descriptions):
                raise ValueError("No hay texto válido para procesar en las descripciones")

            # Exportar video con descripciones
            return self._export_video(
                video_path=video_path,
                descriptions=descriptions
            )
            
        except Exception as e:
            self.logger.error(f"Error processing video: {str(e)}")
            raise

    def _generate_descriptions(
        self,
        scene_analysis: Dict[str, Any],
        silences: List[Dict[str, float]]
    ) -> List[Dict[str, Any]]:
        descriptions = []
        
        for scene in scene_analysis.get("scenes", []):
            logger.info(f"Procesando escena con timestamp: {scene.get('timestamp')}")
            
            silence = self._find_best_silence(scene, silences)
            logger.info(f"Silencio encontrado: {silence}")
            
            if silence:
                duration = silence["end"] - silence["start"]
                logger.info(f"Duración calculada: {duration}")
                
                try:
                    description = self.text_processor.format_audio_description(
                        text=scene.get("description", ""),
                        max_duration=duration
                    )
                    
                    descriptions.append({
                        "text": description,
                        "start": silence["start"],
                        "end": silence["end"],
                        "scene_timestamp": scene.get("timestamp", 0)
                    })
                except Exception as e:
                    logger.error(f"Error al formatear descripción: {str(e)}")
                    continue
        
        return descriptions
        
    def _find_best_silence(
        self,
        scene: Dict[str, Any],
        silences: List[Dict[str, float]]
    ) -> Optional[Dict[str, float]]:
        """Find the best silence period for a scene description."""
        scene_time = scene.get("timestamp", 0)
        best_silence = None
        min_distance = float('inf')
        
        for silence in silences:
            distance = abs(silence["start"] - scene_time)
            if distance < min_distance:
                min_distance = distance
                best_silence = silence
                
        return best_silence
        
    def _export_video(
        self,
        video_path: Path,
        descriptions: List[Dict[str, Any]],
        subtitles: List[Dict[str, Any]] = None
    ) -> Path:
        """
        Export final video with audio descriptions and optional subtitles.
        """
        output_path = self.output_dir / f"{video_path.stem}_accessible{video_path.suffix}"
        
        # Generate audio descriptions WAV file
        descriptions_audio = self._generate_descriptions_audio(descriptions)
        
        # Merge original video with descriptions
        command = [
            'ffmpeg', '-y',
            '-i', str(video_path),
            '-i', descriptions_audio,
            '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=longest[aout]',
            '-map', '0:v',
            '-map', '[aout]'
        ]
        
        if self.add_subtitles and subtitles:
            subtitle_path = self._generate_subtitles_file(subtitles)
            command.extend(['-vf', f'subtitles={subtitle_path}'])
            
        command.append(str(output_path))
        
        subprocess.run(command, check=True)
        return output_path

    def _process_with_ai(self, content: str, prompt_template: str) -> str:
        """Process content with Vertex AI."""
        try:
            prompt = prompt_template.format(content=content)
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            raise RuntimeError(f"AI processing error: {str(e)}")

    def _generate_descriptions_audio(self, descriptions: List[Dict[str, Any]]) -> Path:
        """Generate audio file from descriptions using text-to-speech."""
        temp_audio_path = self.temp_dir / "descriptions.wav"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Mejorar el filtrado y logging de descripciones
            valid_descriptions = []
            for d in descriptions:
                if d.get("text") and isinstance(d["text"], str) and d["text"].strip():
                    valid_descriptions.append(d["text"].strip())
                else:
                    self.logger.warning(f"Descripción inválida encontrada: {d}")

            if not valid_descriptions:
                # Proporcionar una descripción por defecto en lugar de lanzar error
                default_text = "Video sin descripciones de audio disponibles"
                self.logger.warning(f"Usando texto por defecto: {default_text}")
                valid_descriptions = [default_text]

            # Concatenar con pausas más naturales
            full_text = " ... ".join(valid_descriptions)
            
            self.logger.info(f"Generando audio para el texto: {full_text}")
            
            from gtts import gTTS
            tts = gTTS(text=full_text, lang='es', slow=False)
            tts.save(str(temp_audio_path))
            
            return temp_audio_path
            
        except Exception as e:
            self.logger.error(f"Error generando audio: {str(e)}")
            raise

    def _generate_subtitles_file(self, subtitles: List[Dict[str, Any]]) -> Path:
        """Generate subtitles file in SRT format."""
        srt_path = self.temp_dir / "subtitles.srt"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(srt_path, 'w', encoding='utf-8') as f:
                for idx, sub in enumerate(subtitles, 1):
                    f.write(f"{idx}\n")
                    f.write(f"{self._format_timestamp(sub['start'])} --> {self._format_timestamp(sub['end'])}\n")
                    f.write(f"{sub['text']}\n\n")
                    
            return srt_path
            
        except Exception as e:
            logger.error(f"Error generando subtítulos: {str(e)}")
            raise

    def _format_timestamp(self, seconds: float) -> str:
        """Convert seconds to SRT timestamp format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        msecs = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{msecs:03d}"

    def _setup_directories(self) -> None:
        """Configura los directorios necesarios."""
        try:
            self.output_dir.mkdir(parents=True, exist_ok=True)
            self.temp_dir.mkdir(parents=True, exist_ok=True)
            
            if not os.access(self.output_dir, os.W_OK):
                raise PermissionError(f"No hay permisos de escritura en {self.output_dir}")
                
        except Exception as e:
            self.logger.error(f"Error configurando directorios: {e}")
            raise

    def _log_video_info(self, video_path: str) -> None:
        """Registra información básica del video."""
        try:
            video_file = Path(video_path)
            file_size_mb = video_file.stat().st_size / (1024 * 1024)
            
            self.logger.info(f"🎥 Procesando video: {video_file.name}")
            self.logger.info(f"📂 Ruta completa: {video_file.absolute()}")
            self.logger.info(f"💾 Tamaño: {file_size_mb:.2f} MB")
            
            if not video_file.exists():
                raise FileNotFoundError(f"No se encuentra el archivo: {video_path}")
            
            if not os.access(video_path, os.R_OK):
                raise PermissionError(f"No hay permisos de lectura para: {video_path}")
                
        except Exception as e:
            self.logger.error(f"Error al obtener información del video: {str(e)}")
            raise

# En el mismo archivo test_video_pipeline.py

@pytest.mark.asyncio
@pytest.mark.parametrize("service_type", ["AUDIODESCRIPCION", "SUBTITULADO"])
async def test_service_types(pipeline, mock_text_model, service_type):
    """Test diferentes tipos de servicio"""
    with patch('src.pipeline.video_pipeline.VideoPipeline.download_video') as mock_download:
        mock_download.return_value = {
            'video_path': 'test.mp4',
            'metadata': {'title': 'Test Video'}
        }
        mock_text_model.predict.return_value = Mock(text="Texto de prueba generado")
        
        result = await pipeline.process_url("https://youtube.com/test", service_type)
        assert result is not None

@pytest.mark.asyncio
async def test_invalid_service_type(pipeline):
    """Test tipo de servicio inválido"""
    with pytest.raises(ValueError):
        await pipeline.process_url("https://youtube.com/test", "SERVICIO_INVALIDO")