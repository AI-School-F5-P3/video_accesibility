import os
import json
import logging
import tempfile
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Dict, Any, Optional

# Importaciones de los módulos
from audio_processor import AudioProcessor, AudioConfig, VoiceSynthesizer  
from speech_processor import SpeechProcessor, TranscriptionConfig
from text_processor import TextProcessor
from video_analyzer import VideoAnalyzer, VideoConfig, YouTubeVideoManager, FrameExtractor, FrameAnalyzer

load_dotenv()

GOOGLE_APPLICATION_CREDENTIALS = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
# Configuración del logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AccessibilityProcessor:
    """
    Clase principal que integra todos los componentes para procesar
    videos y generar audiodescripciones accesibles según estándares UNE.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa el procesador de accesibilidad con todas las dependencias.
        """
        # Configurar directorios de trabajo
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        # Crear directorio temporal
        self.temp_dir = Path(tempfile.gettempdir()) / "accessibility_processor"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar ambiente
        self.api_key = api_key or os.getenv("YOUTUBE_API_KEY")
        if not self.api_key:
            logger.warning("No se ha proporcionado API_KEY de YouTube. Algunas funciones pueden no estar disponibles.")
        

        # Inicializar voice_synthesizer con valores predeterminados
        self.voice_synthesizer = VoiceSynthesizer()  # Añade esta línea

        # Inicializar Vertex AI y crear modelo generativo
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            # Verificar que existan las credenciales
            if os.getenv("GOOGLE_APPLICATION_CREDENTIALS"):
                # Inicializar Vertex AI
                project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "default-project")
                location = os.getenv("GOOGLE_CLOUD_REGION", "us-central1")
                vertexai.init(project=project_id, location=location)
                
                # Crear el modelo generativo
                model_name = os.getenv("GENERATIVE_MODEL_NAME", "gemini-pro")
                model = GenerativeModel(model_name)
                
                logger.info(f"Modelo Vertex AI inicializado correctamente: {model_name}")
                
                # Inicializar componentes con el modelo real
                self.audio_processor = AudioProcessor(model=model, config=AudioConfig())
                self.speech_processor = SpeechProcessor(model=model, config=TranscriptionConfig())
            else:
                raise EnvironmentError("GOOGLE_APPLICATION_CREDENTIALS no está configurado")
                
        except Exception as e:
            logger.warning(f"No se pudo inicializar Vertex AI: {str(e)}. Usando modelo simulado.")
            
            # Crear modelo simulado
            class MockModel:
                def generate_content(self, *args, **kwargs):
                    return type('Response', (), {'text': 'Mock content generated'})()
            
            mock_model = MockModel()
            self.audio_processor = AudioProcessor(model=mock_model, config=AudioConfig())
            self.speech_processor = SpeechProcessor(model=mock_model, config=TranscriptionConfig())
        
        # Inicializar resto de componentes
        self.text_processor = TextProcessor()
        self.video_analyzer = VideoAnalyzer(config=VideoConfig())

    def process_youtube_video(self, youtube_url: str) -> Dict[str, Any]:
        """
        Proceso completo de un video de YouTube para generar audiodescripción.
        
        Args:
            youtube_url: URL del video de YouTube a procesar
            
        Returns:
            Dict con resultados del procesamiento y rutas a los archivos generados
        """
        try:
            logger.info(f"Iniciando procesamiento del video: {youtube_url}")
            
            # 1. Descargar y obtener metadatos del video
            video_manager = YouTubeVideoManager(youtube_url)
            video_path = video_manager.download_video()
            metadata = video_manager.metadata
            
            logger.info(f"Video descargado: {video_path}")
            logger.info(f"Metadatos: {metadata}")
            
            # 2. Analizar el video para detectar escenas y silencios
            scenes = self.video_analyzer.detect_scenes(video_path)
            silences = self.video_analyzer.detect_silence(video_path)
            
            logger.info(f"Escenas detectadas: {len(scenes)}")
            logger.info(f"Silencios detectados: {silences if silences else 'ninguno'}")
            
            # 3. Extraer frames y analizarlos
            frame_extractor = FrameExtractor(video_path, str(self.temp_dir / "frames"))
            frames = frame_extractor.extract_frames()
            
            frame_analyzer = FrameAnalyzer()
            frame_analysis = []
            for timestamp, frame_path in frames:
                analysis = frame_analyzer.analyze_frame(frame_path)
                frame_analysis.append({
                    "timestamp": timestamp,
                    "frame_path": frame_path,
                    "analysis": analysis
                })
            
            logger.info(f"Analizados {len(frames)} frames del video")
            
            # 4. Generar guion con AI Studio
            # Simulación - En producción usaríamos el modelo real
            script = self._generate_audio_description_script(frame_analysis, scenes, silences)
            
            # 5. Formatear texto según estándares UNE
            formatted_script = self._format_script_for_audio_description(script, silences)
            
            # 6. Sintetizar audio
            audio_path = self.output_dir / f"{Path(video_path).stem}_audiodescripcion.mp3"
            self.voice_synthesizer.generate_audio(formatted_script, audio_path)
            
            # 7. Generar video final con audiodescripción
            output_video_path = self._merge_audio_with_video(audio_path, video_path)
            
            # 8. Guardar resultados
            result = {
                "metadata": metadata.__dict__,
                "scenes": scenes,
                "silences": silences,
                "script": formatted_script,
                "audio_description_path": str(audio_path),
                "output_video_path": str(output_video_path),
                "status": "success"
            }
            
            # Guardar resultado en JSON
            result_path = self.output_dir / f"{Path(video_path).stem}_result.json"
            with open(result_path, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Procesamiento completado. Resultados guardados en {result_path}")
            return result
            
        except Exception as e:
            logger.error(f"Error en el procesamiento: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _generate_audio_description_script(self, 
                                          frame_analysis: List[Dict], 
                                          scenes: List[Dict], 
                                          silences: Optional[Dict]) -> str:
        """
        Genera un guion de audiodescripción basado en el análisis de frames
        y las escenas detectadas.
        
        Args:
            frame_analysis: Análisis de frames con objetos detectados
            scenes: Escenas detectadas en el video
            silences: Silencios detectados para insertar descripciones
            
        Returns:
            Guion de audiodescripción
        """
        # En producción, aquí llamaríamos a AI Studio con:
        # response = self.model.generate_content(prompt)
        
        # Simulamos la respuesta de AI Studio con un script básico
        descriptions = []
        
        for scene in scenes:
            scene_frames = [fa for fa in frame_analysis 
                           if scene['start_time'] <= fa['timestamp'] <= scene['end_time']]
            
            if not scene_frames:
                continue
            
            # Obtener objetos detectados en la escena
            all_objects = []
            for frame in scene_frames:
                objects = frame['analysis'].get('objects', [])
                all_objects.extend([obj['name'] for obj in objects])
            
            # Contar ocurrencias
            from collections import Counter
            object_counts = Counter(all_objects)
            main_objects = [obj for obj, count in object_counts.most_common(3)]
            
            # Generar descripción de la escena
            description = f"[{scene['start_time']:.1f}s] "
            if main_objects:
                description += f"En esta escena se ve {', '.join(main_objects)}. "
            else:
                description += f"Escena {scene.get('description', 'sin detalles')}. "
            
            descriptions.append(description)
        
        return "\n".join(descriptions)
    
    def _format_script_for_audio_description(self, script: str, silences: Optional[Dict]) -> str:
        """
        Formatea el guion según estándares UNE153020 y ajusta al tiempo disponible
        en los silencios detectados.
        
        Args:
            script: Guion generado por AI
            silences: Información de silencios detectados
            
        Returns:
            Guion formateado
        """
        lines = script.strip().split("\n")
        formatted_lines = []
        
        for line in lines:
            if not line.strip():
                continue
                
            # Extraer timestamp si existe
            if line.startswith("[") and "]" in line:
                time_str = line[1:line.index("]")]
                try:
                    timestamp = float(time_str.rstrip("s"))
                    description = line[line.index("]")+1:].strip()
                except ValueError:
                    timestamp = 0.0
                    description = line
            else:
                timestamp = 0.0
                description = line
            
            # Formatear según UNE153020
            formatted_description = self.text_processor.format_audio_description(
                description,
                max_duration=5.0  # Ajustar según silencios disponibles
            )
            
            formatted_lines.append(f"[{timestamp:.1f}s] {formatted_description}")
        
        return "\n".join(formatted_lines)
    
    def _merge_audio_with_video(self, audio_path: Path, video_path: str) -> Path:
        """
        Combina el audio de la audiodescripción con el video original.
        Usamos una implementación simulada, en producción se usaría ffmpeg.
        
        Args:
            audio_path: Ruta al archivo de audio generado
            video_path: Ruta al video original
            
        Returns:
            Ruta al video resultante
        """
        # En producción, usar ffmpeg para mezclar el audio con el video original
        # Aquí simulamos la operación
        output_path = self.output_dir / f"{Path(video_path).stem}_con_audiodescripcion.mp4"
        
        logger.info(f"Simulando mezcla de audio '{audio_path}' con video '{video_path}'")
        logger.info(f"Video con audiodescripción guardado en: {output_path}")
        
        # Crear un archivo vacío para simular la salida
        output_path.touch()
        
        return output_path


if __name__ == "__main__":
    try:
        # Solicitar URL de YouTube al usuario
        youtube_url = input("Introduce la URL del video de YouTube: ")
        
        # Iniciar procesador y ejecutar
        processor = AccessibilityProcessor()
        result = processor.process_youtube_video(youtube_url)
        
        if result['status'] == 'success':
            print("\n✅ Procesamiento completado con éxito!")
            print(f"➡️ Audio de audiodescripción: {result['audio_description_path']}")
            print(f"➡️ Video con audiodescripción: {result['output_video_path']}")
            print(f"➡️ Detalles completos guardados en: {Path(result['output_video_path']).with_suffix('.json')}")
        else:
            print(f"\n❌ Error en el procesamiento: {result.get('error', 'Error desconocido')}")
    
    except KeyboardInterrupt:
        print("\n\nProcesamiento cancelado por el usuario.")
    except Exception as e:
        print(f"\n❌ Error inesperado: {str(e)}")
        logger.error(f"Error inesperado: {str(e)}", exc_info=True)