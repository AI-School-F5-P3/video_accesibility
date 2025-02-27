import os
import json
import datetime
import logging
import tempfile
import subprocess
import sys
import shutil
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

        # Máxima duración permitida (100 minutos en segundos)
        self.MAX_DURATION = 6000

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
        
        try:
            self.text_processor = TextProcessor()
            logger.info("TextProcessor initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing TextProcessor: {str(e)}")
            raise
        
        self.voice_synthesizer = VoiceSynthesizer()
        
        # Inicializar modelo de VertexAI
        self._init_vertex_ai()
        
        # Inicializar componentes
        self.video_analyzer = VideoAnalyzer(model=self.vertex_model)
        self.audio_processor = AudioProcessor(model=self.vertex_model)
        self.speech_processor = SpeechProcessor(model=self.vertex_model)
        
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
    
    def _check_ffmpeg(self) -> bool:
        """Verifica si ffmpeg está instalado y disponible."""
        try:
            subprocess.run(['ffmpeg', '-version'], capture_output=True)
            return True
        except FileNotFoundError:
            return False
    
    def _get_video(self) -> str:
        """
        Obtiene el video desde la fuente (URL o archivo local).
        
        Returns:
            str: Ruta al archivo de video
        """
        if self.source.startswith(('http://', 'https://', 'www.', 'youtube.com', 'youtu.be')):
            # Es una URL de YouTube
            logger.info(f"Descargando video de YouTube: {self.source}")
            yt_manager = YouTubeVideoManager(youtube_url=self.source)
            video_path = yt_manager.download_video(output_dir=self.temp_dir)
            return video_path
        elif os.path.isfile(self.source):
            # Es un archivo local
            logger.info(f"Usando archivo de video local: {self.source}")
            return self.source
        else:
            raise ValueError(f"Fuente no válida: {self.source}")
        
    def _get_video_duration(self, video_path: str) -> float:
        """
        Obtiene la duración del video en segundos.
        
        Args:
            video_path (str): Ruta al archivo de video
            
        Returns:
            float: Duración en segundos
        """
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', 
                '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
                capture_output=True,
                text=True
            )
            duration = float(result.stdout.strip())
            logger.info(f"Duración del video: {duration:.2f} segundos")
            return duration
        except Exception as e:
            logger.error(f"Error al obtener duración del video: {e}")
            raise
    
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
            logger.info(f"Iniciando procesamiento del video: {self.source}")
            
            # Analizar todo el video primero para mejor contexto
            logger.info("Analizando escenas del video...")
            scenes = self.video_analyzer.detect_scenes(video_path)
            logger.info(f"Se detectaron {len(scenes)} escenas en el video")
            
            # Generar subtítulos según UNE 153010
            logger.info("Generando subtítulos según estándar UNE 153010...")
            srt_path, subtitles_data = self._generate_subtitles(video_path)
            logger.info(f"Subtítulos generados y guardados en: {srt_path}")
            
            # Generar guion completo minuto a minuto
            logger.info("Generando guion completo minuto a minuto...")
            full_script_path = self._generate_full_script(video_path, subtitles_data, scenes)
            logger.info(f"Guion completo generado y guardado en: {full_script_path}")
            
            # Generar audiodescripción a partir del guion completo
            logger.info("Generando audiodescripción a partir del guion completo...")
            audio_desc_path, audio_desc_script = self._generate_audio_description_from_script(full_script_path, video_path)
            logger.info(f"Audiodescripción generada y guardada en: {audio_desc_path}")
            
            # Extraer audio original del video
            orig_audio_path = self._extract_audio_from_video(video_path)
            logger.info(f"Audio original extraído y guardado en: {orig_audio_path}")
            
            # Generar video final con audiodescripción y subtítulos
            logger.info("Generando video final con accesibilidad completa...")
            final_video = self._merge_audio_description_fixed(video_path, audio_desc_path, srt_path)
            logger.info(f"Video final generado y guardado en: {final_video}")
            
            # Preparar archivos para descarga
            output_files = self._prepare_output_files(
                video_path, 
                srt_path,
                audio_desc_path,
                audio_desc_script,
                full_script_path,
                final_video,
                orig_audio_path
            )
            
            logger.info("¡Procesamiento completado con éxito!")
            return output_files
            
        except Exception as e:
            logger.error(f"Error en el procesamiento: {e}")
            raise

    def _extract_audio_from_video(self, video_path: str) -> str:
        """
        Extrae el audio original del video en formato MP3.
        
        Args:
            video_path (str): Ruta al archivo de video
            
        Returns:
            str: Ruta al archivo de audio extraído
        """
        logger.info("Extrayendo audio original del video...")
        output_path = self.output_dir / "original_audio.mp3"
        
        try:
            subprocess.run([
                'ffmpeg', '-y',
                '-i', video_path,
                '-vn',  # Sin video
                '-acodec', 'libmp3lame',  # Usar codec MP3
                '-q:a', '2',  # Alta calidad
                str(output_path)
            ], check=True, capture_output=True)
            
            return str(output_path)
        except subprocess.CalledProcessError as e:
            logger.error(f"Error al extraer audio del video: {e.stderr.decode()}")
            raise RuntimeError(f"Error al extraer audio: {e}")

    def _generate_subtitles(self, video_path: str) -> tuple[str, List[Dict]]:
        """
        Genera subtítulos según UNE 153010 y los guarda en un archivo .srt.
        
        Returns:
            Tuple con la ruta al archivo .srt generado y los datos de subtítulos procesados.
        """
        logger.info("Generando subtítulos...")
        
        # Transcribir audio
        result = self.whisper_model.transcribe(video_path)
        
        # Procesar transcripción para formato SRT
        segments = result["segments"]
        srt_content = []
        subtitles_data = []
        
        for i, segment in enumerate(segments, 1):
            # Formatear tiempos
            start = self._format_timecode(segment['start'])
            end = self._format_timecode(segment['end'])
            
            # Formatear texto según UNE 153010
            formatted_subtitles = self.text_processor.format_subtitles(segment['text'])
            
            for j, subtitle in enumerate(formatted_subtitles):
                subtitle_index = i * 10 + j  # Evita índices duplicados
                srt_content.extend([
                    str(subtitle_index),
                    f"{start} --> {end}",
                    subtitle['text'],
                    ""
                ])
                
                # Guardar datos para uso posterior
                subtitles_data.append({
                    'index': subtitle_index,
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': subtitle['text']
                })
        
        # Guardar archivo SRT según la norma UNE 153010
        srt_path = self.output_dir / "subtitles_une153010.srt"
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_content))
            
        return str(srt_path), subtitles_data

    def _format_timecode(self, seconds: float) -> str:
        """Convierte segundos a formato de tiempo SRT (HH:MM:SS,mmm)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"

    def _generate_full_script(self, video_path, subtitles, scenes):
        """
        Genera un guion completo del video combinando transcripciones y descripciones,
        organizando el contenido minuto a minuto.
        
        Args:
            video_path (str): Ruta al video
            subtitles (list): Lista de subtítulos procesados
            scenes (list): Lista de escenas detectadas
            
        Returns:
            str: Ruta al archivo de guion generado
        """
        logger.info("Generando guion completo minuto a minuto...")
        
        # Obtener duración total del video
        total_duration = self._get_video_duration(video_path)
        total_minutes = int(total_duration / 60) + 1
        
        # Preparar datos para segmentación por minutos
        minute_segments = {}
        
        # Organizar subtítulos por minutos
        for sub in subtitles:
            minute = int(sub['start'] / 60)
            if minute not in minute_segments:
                minute_segments[minute] = {"subtitles": [], "scenes": []}
            minute_segments[minute]["subtitles"].append(sub)
        
        # Organizar escenas por minutos
        for scene in scenes:
            start_minute = int(scene['start_time'] / 60)
            end_minute = int(scene['end_time'] / 60)
            
            for minute in range(start_minute, end_minute + 1):
                if minute not in minute_segments:
                    minute_segments[minute] = {"subtitles": [], "scenes": []}
                minute_segments[minute]["scenes"].append(scene)
        
        # Generar guion completo con IA
        prompt = f"""
        Actúa como un guionista profesional especializado en audiodescripción según la norma UNE 153020.
        
        Crea un guion completo MINUTO A MINUTO del siguiente video con duración total de {total_minutes} minutos.
        El guion debe incluir tanto los diálogos (subtítulos) como las descripciones visuales (audiodescripción).
        
        Para cada minuto, incluye una sección claramente identificada (MINUTO 1, MINUTO 2, etc.) y detalla TODO lo que sucede
        en ese segmento de tiempo, integrando diálogos y elementos visuales.
        
        En cada silencio o pausa debe haber una audiodescripción. Asegúrate de que las descripciones:
        - Sean breves y concisas
        - Se integren naturalmente entre los diálogos
        - Describan elementos visuales relevantes
        - Sean objetivas y no interpreten intenciones
        - No repitan información que ya se deduce del audio
        
        CONTENIDO DEL VIDEO POR MINUTOS:
        """
        
        # Añadir contenido organizado por minutos
        for minute in range(total_minutes):
            prompt += f"\n\nMINUTO {minute+1}:\n"
            
            if minute in minute_segments:
                data = minute_segments[minute]
                
                if data["subtitles"]:
                    prompt += "DIÁLOGOS:\n"
                    for sub in data["subtitles"]:
                        time_str = f"{sub['start']:.2f}s - {sub['end']:.2f}s"
                        prompt += f"- [{time_str}] {sub['text']}\n"
                
                if data["scenes"]:
                    prompt += "\nCONTENIDO VISUAL:\n"
                    for scene in data["scenes"]:
                        if minute * 60 <= scene['start_time'] <= (minute + 1) * 60:
                            time_str = f"{scene['start_time']:.2f}s - {min(scene['end_time'], (minute + 1) * 60):.2f}s"
                            prompt += f"- [{time_str}] {scene['description']}\n"
            else:
                prompt += "[Sin contenido transcrito para este minuto]\n"
        
        prompt += """
        El guion final debe:
        1. Mantener una estructura clara MINUTO A MINUTO
        2. Integrar diálogos y descripciones de forma coherente
        3. Incluir acotaciones detalladas sobre lo que se ve en pantalla
        4. Identificar claramente a los personajes cuando hablan
        5. Seguir el formato profesional de guion cinematográfico
        6. Marcar claramente los tiempos de cada elemento (en segundos)
        7. Aportar contexto visual para cada diálogo cuando sea necesario
        
        Para la audiodescripción, respeta todas las normas UNE 153020:
        - Usa lenguaje claro y sencillo adaptado al contenido
        - Evita describir lo obvio
        - No adelantes acontecimientos ni censures información
        - Incluye claramente qué momentos son descripciones para distinguirlos de los diálogos
        """

        # Usar VertexAI para generar el guion
        response = self.vertex_model.generate_content(prompt)
        script = response.text
        
        # Guardar guion completo
        script_path = self.output_dir / "full_script_minute_by_minute.txt"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        
        return str(script_path)
    
    def _generate_audio_description_from_script(self, script_path: str, video_path: str) -> tuple[str, str]:
        """
        Genera la audiodescripción a partir del guion completo.
        
        Args:
            script_path (str): Ruta al guion completo
            video_path (str): Ruta al video original
            
        Returns:
            Tuple con ruta a la audiodescripción y al script de audiodescripción
        """
        logger.info("Extrayendo descripciones del guion completo...")
        
        # Leer el guion completo
        with open(script_path, 'r', encoding='utf-8') as f:
            full_script = f.read()
        
        # Procesar con IA para extraer solo las partes de audiodescripción
        prompt = """
        Extrae solamente las audiodescripciones del siguiente guion completo.
        
        Para cada descripción, incluye:
        1. El tiempo exacto en segundos (inicio-fin)
        2. El texto de la descripción
        
        Usa este formato:
        [INICIO_SEGUNDOS-FIN_SEGUNDOS] TEXTO_DESCRIPCIÓN
        
        Por ejemplo:
        [25.5-30.2] El personaje camina lentamente hacia la ventana.
        
        Asegúrate de:
        - Incluir SOLO las descripciones, no los diálogos
        - Mantener los tiempos exactos del guion original
        - Incluir las descripciones más importantes y relevantes
        
        GUION COMPLETO:
        """
        prompt += full_script
        
        # Generar script de audiodescripción
        response = self.vertex_model.generate_content(prompt)
        descriptions_script = response.text
        
        # Guardar script de audiodescripción
        audiodesc_script_path = self.output_dir / "audio_description_script.txt"
        with open(audiodesc_script_path, 'w', encoding='utf-8') as f:
            f.write(descriptions_script)
        
        logger.info("Generando audio para cada descripción...")
        
        # Parsear el script para extraer las descripciones y tiempos
        descriptions = []
        
        for line in descriptions_script.split('\n'):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('MINUTO'):
                continue
                
            # Buscar formato [inicio-fin] Descripción
            import re
            match = re.match(r'\[(\d+\.?\d*)-(\d+\.?\d*)\]\s*(.*)', line)
            
            if match:
                start_time = float(match.group(1))
                end_time = float(match.group(2))
                description_text = match.group(3)
                
                descriptions.append({
                    'start': start_time,
                    'end': end_time,
                    'text': description_text
                })
        
        # Generar audio para cada descripción
        audio_segments = []
        
        # Opciones de voz según UNE 153020
        voice_options = {
            'rate': 1.1,  # Ligeramente más rápido para aprovechar silencios cortos
            'pitch': 0.0  # Tono natural
        }
        
        blank_audio = AudioSegment.silent(duration=1000)  # 1 segundo de silencio
        combined_audio = AudioSegment.silent(duration=0)
        
        for i, desc in enumerate(descriptions):
            # Calcular la duración disponible
            available_duration = desc['end'] - desc['start']
            
            # Ajustar texto si es necesario para que quepa en el tiempo disponible
            description_text = self.text_processor.format_audio_description(
                desc['text'],
                max_duration=available_duration
            )
            
            # Nombre temporal del archivo
            temp_audio_file = self.temp_dir / f"desc_{i}.mp3"
            
            logger.info(f"Generando audio para descripción {i+1}: {description_text[:50]}...")
            
            # Generar audio
            audio_content = self.voice_synthesizer.generate_audio(
                description_text,
                rate=voice_options['rate'],
                pitch=voice_options['pitch']
            )
            
            # Guardar audio
            with open(temp_audio_file, 'wb') as f:
                f.write(audio_content)
            
            # Añadir a la lista de segmentos
            audio_segments.append({
                'file': str(temp_audio_file),
                'start': desc['start'],
                'end': desc['end'],
                'text': description_text
            })
            
            # Cargar y posicionar el audio en la pista combinada
            try:
                segment = AudioSegment.from_file(temp_audio_file)
                
                # Calcular posición en milisegundos
                position_ms = int(desc['start'] * 1000)
                
                # Si la posición es mayor que la duración actual, añadir silencio
                if position_ms > len(combined_audio):
                    silence_needed = position_ms - len(combined_audio)
                    combined_audio += AudioSegment.silent(duration=silence_needed)
                
                # Añadir el segmento
                combined_audio = combined_audio.overlay(segment, position=position_ms)
                
            except Exception as e:
                logger.error(f"Error procesando segmento de audio {i}: {e}")
        
        # Guardar audio combinado en MP3
        audio_desc_path = self.output_dir / "audio_description.mp3"
        combined_audio.export(str(audio_desc_path), format="mp3", bitrate="192k")
        
        # Mejorar calidad del audio final
        enhanced_audio_path = self.output_dir / "audio_description_enhanced.mp3"
        try:
            # Normalizar y mejorar calidad del audio con FFmpeg
            subprocess.run([
                'ffmpeg', '-y',
                '-i', str(audio_desc_path),
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11',  # Normalización para mejor calidad
                '-ar', '48000',  # Alta frecuencia de muestreo
                '-b:a', '192k',  # Bitrate alto
                str(enhanced_audio_path)
            ], check=True, capture_output=True)
            
            return str(enhanced_audio_path), str(audiodesc_script_path)
        except subprocess.CalledProcessError as e:
            logger.warning(f"No se pudo mejorar el audio, usando versión original: {e}")
            return str(audio_desc_path), str(audiodesc_script_path)

    def _merge_audio_description_fixed(self, video_path: str, audio_desc_path: str, srt_path: str) -> str:
        """
        Versión corregida para generar video final con audiodescripción y subtítulos.
        
        Args:
            video_path: Ruta al video original
            audio_desc_path: Ruta al audio de audiodescripción
            srt_path: Ruta al archivo de subtítulos
            
        Returns:
            Ruta al video final
        """
        logger.info("Generando video final con audiodescripción y subtítulos (versión corregida)...")

        # Asegurar que el directorio de salida existe
        output_path = self.output_dir / "video_with_accessibility.mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Normalizar rutas para evitar problemas
        video_path_norm = str(Path(video_path).resolve())
        audio_desc_path_norm = str(Path(audio_desc_path).resolve())
        srt_path_norm = str(Path(srt_path).resolve())
        output_path_norm = str(output_path.resolve())

        # Verificar que los archivos existen
        for path, name in [(video_path_norm, "Video"), (srt_path_norm, "Subtítulos")]:
            if not os.path.exists(path):
                logger.error(f"{name} no encontrado en: {path}")
                raise FileNotFoundError(f"{name} no encontrado en: {path}")
        
        # Verificar archivo de audio de descripción
        if not os.path.exists(audio_desc_path_norm):
            logger.error(f"Audio descripción no encontrado en: {audio_desc_path_norm}")
            raise FileNotFoundError(f"Audio descripción no encontrado en: {audio_desc_path_norm}")

        logger.info(f"Video original: {video_path_norm} ({os.path.getsize(video_path_norm)} bytes)")
        logger.info(f"Audio descripción: {audio_desc_path_norm} ({os.path.getsize(audio_desc_path_norm)} bytes)")
        logger.info(f"Subtítulos: {srt_path_norm} ({os.path.getsize(srt_path_norm)} bytes)")

        # Extraer subtítulos normalizados para FFmpeg
        if os.name == 'nt':  # Windows
            srt_path_escaped = srt_path_norm.replace('\\', '/').replace(':', '\\\\:')
        else:
            srt_path_escaped = srt_path_norm.replace(':', '\\\\:')

        # Estilo de subtítulos según UNE 153010
        subtitle_style = (
            'FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF,BackColour=&H80000000,'
            'OutlineColour=&H000000,BorderStyle=3,Outline=1,Shadow=1,MarginV=20,Alignment=2'
        )

        # Extraer audio del video original
        temp_orig_audio = self.temp_dir / "orig_audio.wav"
        try:
            logger.info("Extrayendo audio del video original...")
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', video_path_norm,
                '-vn',              # Sin video
                '-c:a', 'pcm_s16le', # Formato WAV
                '-ar', '44100',     # Sample rate estándar
                str(temp_orig_audio)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error extrayendo audio original: {result.stderr}")
                raise RuntimeError("Error al extraer audio del video original")
                
            logger.info("Audio original extraído correctamente")
        except Exception as e:
            logger.error(f"Error en la extracción de audio original: {str(e)}")
            raise RuntimeError(f"Error al extraer audio del video original: {str(e)}")

        # SOLUCIÓN: Regenerar el audio de descripción desde los datos de texto
        # Vamos a intentar localizar o generar un script de audiodescripción
        audio_desc_script_path = None
        
        # Buscar si existe un archivo de script de audiodescripción en la misma carpeta
        possible_script_paths = [
            audio_desc_path_norm.replace('.mp3', '.txt'),
            os.path.join(self.output_dir, 'audio_description_script.txt'),
            os.path.join(os.path.dirname(audio_desc_path_norm), 'audio_description_script.txt')
        ]
        
        for path in possible_script_paths:
            if os.path.exists(path):
                audio_desc_script_path = path
                logger.info(f"Encontrado script de audiodescripción: {path}")
                break
        
        # Si encontramos el script, regenerar el audio
        temp_audio_desc_fixed = self.temp_dir / "audio_desc_fixed.wav"
        
        if audio_desc_script_path:
            try:
                # Regenerar audio descripción usando TTS
                logger.info("Regenerando audio de descripción desde script...")
                
                # Aquí deberíamos utilizar el mismo TTS que usó originalmente
                # Como ejemplo, usamos un comando genérico - sustitúyelo por el TTS específico que uses
                with open(audio_desc_script_path, 'r', encoding='utf-8') as f:
                    script_content = f.read()
                
                # Si estás usando Google Text-to-Speech, podrías hacer algo como:
                try:
                    from google.cloud import texttospeech
                    
                    client = texttospeech.TextToSpeechClient()
                    synthesis_input = texttospeech.SynthesisInput(text=script_content)
                    
                    voice = texttospeech.VoiceSelectionParams(
                        language_code="es-ES",
                        name="es-ES-Standard-A"
                    )
                    
                    audio_config = texttospeech.AudioConfig(
                        audio_encoding=texttospeech.AudioEncoding.LINEAR16,
                        sample_rate_hertz=44100
                    )
                    
                    response = client.synthesize_speech(
                        input=synthesis_input, voice=voice, audio_config=audio_config
                    )
                    
                    with open(str(temp_audio_desc_fixed), "wb") as out:
                        out.write(response.audio_content)
                        
                    logger.info(f"Audio de descripción regenerado correctamente: {temp_audio_desc_fixed}")
                    
                except ImportError:
                    # Si no está disponible Google TTS, intentamos con otra solución
                    logger.warning("Google TTS no disponible, intentando otra solución...")
                    
                    # Intentar con gTTS (requiere pip install gtts)
                    try:
                        from gtts import gTTS
                        
                        tts = gTTS(text=script_content, lang='es')
                        temp_mp3 = self.temp_dir / "temp_desc.mp3"
                        tts.save(str(temp_mp3))
                        
                        # Convertir a WAV
                        result = subprocess.run([
                            'ffmpeg', '-y',
                            '-i', str(temp_mp3),
                            '-c:a', 'pcm_s16le',
                            '-ar', '44100',
                            str(temp_audio_desc_fixed)
                        ], capture_output=True, text=True)
                        
                        if result.returncode != 0:
                            raise RuntimeError(f"Error convirtiendo audio: {result.stderr}")
                            
                        logger.info(f"Audio de descripción regenerado con gTTS: {temp_audio_desc_fixed}")
                        
                    except ImportError:
                        logger.warning("gTTS no disponible, usando un archivo de prueba silencioso...")
                        
                        # Crear un archivo de audio silencioso como último recurso
                        result = subprocess.run([
                            'ffmpeg', '-y',
                            '-f', 'lavfi',
                            '-i', 'anullsrc=r=44100:cl=stereo',
                            '-t', '10',  # 10 segundos de silencio
                            '-c:a', 'pcm_s16le',
                            str(temp_audio_desc_fixed)
                        ], capture_output=True, text=True)
                        
                        if result.returncode != 0:
                            raise RuntimeError(f"Error creando audio silencioso: {result.stderr}")
                            
                        logger.warning("Creado archivo de audio silencioso como reemplazo")
                
                audio_desc_path_norm = str(temp_audio_desc_fixed)
                
            except Exception as e:
                logger.error(f"Error regenerando audio de descripción: {str(e)}")
                logger.warning("Intentando continuar con el video original sin audiodescripción...")
                
                # Si falla todo, simplemente usaremos el audio original
                temp_audio_mixed = temp_orig_audio
                
        else:
            # Si no hay script, intentamos arreglar el archivo de audio directamente
            try:
                logger.info("Intentando recuperar el audio de descripción existente...")
                
                # Intentar convertir directamente a WAV saltando validación de formato
                result = subprocess.run([
                    'ffmpeg', '-y',
                    '-f', 'mp3',  # Forzar formato mp3 sin detección
                    '-i', audio_desc_path_norm,
                    '-c:a', 'pcm_s16le',
                    '-ar', '44100',
                    str(temp_audio_desc_fixed)
                ], capture_output=True, text=True)
                
                if result.returncode != 0:
                    logger.error(f"Error recuperando audio: {result.stderr}")
                    logger.warning("Creando audio silencioso como reemplazo...")
                    
                    # Crear un archivo de audio silencioso como último recurso
                    result = subprocess.run([
                        'ffmpeg', '-y',
                        '-f', 'lavfi',
                        '-i', 'anullsrc=r=44100:cl=stereo',
                        '-t', '10',  # 10 segundos de silencio
                        '-c:a', 'pcm_s16le',
                        str(temp_audio_desc_fixed)
                    ], capture_output=True, text=True)
                    
                    if result.returncode != 0:
                        raise RuntimeError(f"Error creando audio silencioso: {result.stderr}")
                        
                    logger.warning("Creado archivo de audio silencioso como reemplazo")
                
                audio_desc_path_norm = str(temp_audio_desc_fixed)
                
            except Exception as e:
                logger.error(f"Error procesando audio de descripción: {str(e)}")
                logger.warning("Continuando sin audiodescripción...")
                
                # Si falla todo, simplemente usaremos el audio original
                temp_audio_mixed = temp_orig_audio
                return self._generate_video_without_audio_desc(video_path_norm, srt_path_escaped, 
                                                            subtitle_style, output_path_norm)

        # Generar archivo de audio mixto
        temp_audio_mixed = self.temp_dir / "mixed_audio.wav"
        try:
            # Mezclar audio original y audiodescripción
            logger.info("Mezclando audio original y audiodescripción...")
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', str(temp_orig_audio),
                '-i', audio_desc_path_norm,
                '-filter_complex', 
                '[0:a]volume=0.8[a1];[1:a]volume=1.0[a2];[a1][a2]amix=inputs=2:duration=longest[aout]',
                '-map', '[aout]',
                '-c:a', 'pcm_s16le',
                str(temp_audio_mixed)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error mezclando audio: {result.stderr}")
                logger.warning("Usando audio original sin mezclar...")
                temp_audio_mixed = temp_orig_audio
            else:
                logger.info("Audio mezclado correctamente")
            
        except Exception as e:
            logger.error(f"Error mezclando audio: {str(e)}")
            logger.warning("Usando audio original sin mezclar...")
            temp_audio_mixed = temp_orig_audio

        # Generar video final con el audio mezclado y los subtítulos
        try:
            logger.info("Generando video final con audio y subtítulos...")
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', video_path_norm,
                '-i', str(temp_audio_mixed),
                '-map', '0:v',
                '-map', '1:a',
                '-c:v', 'libx264',
                '-crf', '18',
                '-preset', 'medium',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-c:s', 'mov_text',
                '-metadata:s:s:0', 'language=spa',
                '-metadata', 'title="Video con audiodescripción según UNE 153020"',
                '-metadata', 'comment="Subtítulos según UNE 153010"',
                output_path_norm
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error generando video final: {result.stderr}")
                raise RuntimeError("Error al generar video final con subtítulos")
                
            logger.info(f"Video accesible generado correctamente: {output_path_norm}")
            
        except Exception as e:
            logger.error(f"Error generando video final: {str(e)}")
            raise RuntimeError(f"Error al generar video final: {str(e)}")

        # Generar también una versión solo con audio mezclado (sin subtítulos)
        audio_only_output = self.output_dir / "audio_with_description.mp3"
        try:
            logger.info("Generando versión MP3 del audio mezclado...")
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', str(temp_audio_mixed),
                '-c:a', 'libmp3lame',
                '-q:a', '2',
                str(audio_only_output)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.warning(f"Error generando MP3 final: {result.stderr}")
            else:
                logger.info(f"Audio con descripción generado en: {str(audio_only_output)}")
        except Exception as e:
            logger.warning(f"Error al guardar audio con descripción: {str(e)}")

        return str(output_path)

    def _generate_video_without_audio_desc(self, video_path, srt_path_escaped, subtitle_style, output_path):
        """Genera video solo con subtítulos, sin audiodescripción."""
        try:
            logger.info("Generando video solo con subtítulos (sin audiodescripción)...")
            result = subprocess.run([
                'ffmpeg', '-y',
                '-i', video_path,
                '-c:v', 'libx264',
                '-crf', '18',
                '-preset', 'medium',
                '-c:a', 'aac',
                '-b:a', '192k',
                '-vf', f"subtitles='{srt_path_escaped}':force_style='{subtitle_style}'",
                '-metadata', 'title="Video con subtítulos según UNE 153010"',
                output_path
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                logger.error(f"Error generando video con subtítulos: {result.stderr}")
                raise RuntimeError("Error al generar video con subtítulos")
                
            logger.info(f"Video con subtítulos generado correctamente: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Error generando video con subtítulos: {str(e)}")
            raise RuntimeError(f"Error al generar video con subtítulos: {str(e)}")

    def _prepare_output_files(self, 
                            video_path: str,
                            srt_path: str,
                            audio_desc_path: str,
                            audio_desc_script: str,
                            full_script_path: str,
                            final_video_path: str,
                            orig_audio_path: str) -> Dict[str, str]:
        """Prepara y organiza archivos finales."""
        # Copiar archivos a directorio final
        final_paths = {
            'subtitles': srt_path,
            'audio_description': audio_desc_path,
            'audio_description_script': audio_desc_script,
            'full_script': full_script_path,
            'video_with_audio_description': final_video_path,
            'original_audio': orig_audio_path
        }
        
        # Copiar archivos para el video_processor.py
        temp_dir = Path("C:/Users/Administrator/AppData/Local/Temp")
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            # Copiar video
            shutil.copy2(video_path, temp_dir / "video.mp4")
            logger.info(f"Video copiado a {temp_dir / 'video.mp4'}")
            
            # Extraer y copiar audio
            audio_temp = self.temp_dir / "temp_audio.aac"
            subprocess.run([
                'ffmpeg', '-y',
                '-i', video_path,
                '-vn', '-acodec', 'copy',
                str(audio_temp)
            ], check=True)
            shutil.copy2(str(audio_temp), temp_dir / "audio.aac")
            logger.info(f"Audio copiado a {temp_dir / 'audio.aac'}")
            
            # Copiar subtítulos
            shutil.copy2(srt_path, temp_dir / "subtitles.srt")
            logger.info(f"Subtítulos copiados a {temp_dir / 'subtitles.srt'}")
        except Exception as e:
            logger.error(f"Error copiando archivos para video_processor: {e}")
        
        # Generar archivo de metadatos
        metadata = {
            'processed_at': str(datetime.datetime.now()),
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
    def generate_from_script(self, script_path: str) -> dict:
        """
        Genera archivos de accesibilidad partiendo del guion completo.
        """
        logger.info(f"Generando archivos de accesibilidad desde el guion: {script_path}")
        
        if not os.path.isfile(script_path):
            raise FileNotFoundError(f"El archivo de guion no existe: {script_path}")
        
        with open(script_path, 'r', encoding='utf-8') as f:
            script_content = f.read()
        
        subtitles_data, descriptions_data = self._parse_script_content(script_content)
        srt_path = self._generate_srt_from_parsed_data(subtitles_data)
        audio_desc_path = self._generate_audio_from_descriptions(descriptions_data)
        
        video_path = self.source if os.path.isfile(self.source) else input("Introduce la ruta al video original: ")
        if not os.path.isfile(video_path):
            raise FileNotFoundError(f"El archivo de video no existe: {video_path}")
        
        final_video_path = self.merge_audio_description(video_path, audio_desc_path, srt_path)
        
        return {
            'subtitles': srt_path,
            'audio_description': audio_desc_path,
            'final_video': final_video_path
        }


if __name__ == "__main__":
    print("\n===== SISTEMA DE GENERACIÓN DE ACCESIBILIDAD PARA VIDEOS =====")
    print("(Compatible con estándares UNE 153010 y UNE 153020)")
    print("\nEste programa procesa videos para generar:")
    print("- Subtítulos profesionales (UNE 153010)")  
    print("- Audiodescripción (UNE 153020)")
    print("- Guion completo minuto a minuto")
    print("- Video final con accesibilidad integrada")
    print("\nSoporta videos de YouTube y archivos locales.\n")
    
    # Solicitar ruta o URL del video
    source = input("Introduce URL de YouTube o ruta al video local: ")
    
    # Solicitar directorio de salida (opcional)
    output_dir = input("Directorio de salida (dejar en blanco para usar 'output/'): ")
    output_dir = output_dir if output_dir.strip() else "output"
    
    try:
        # Inicializar pipeline
        print("\n[1/5] Iniciando pipeline de procesamiento...")
        pipeline = AccessibilityPipeline(source, output_dir)
        
        # Procesar video
        print("[2/5] Analizando video...")
        output_files = pipeline.process_video()
        
        # Mostrar resultados
        print("\n✅ ¡Procesamiento completado con éxito!")
        print("\nArchivos generados:")
        
        # Agrupar por categoría
        print("\n📝 GUIONES:")
        if 'full_script' in output_files:
            print(f"  - Guion completo: {output_files['full_script']}")
        if 'audio_description_script' in output_files:
            print(f"  - Guion de audiodescripción: {output_files['audio_description_script']}")
            
        print("\n🎬 MEDIOS:")
        if 'video_with_audio_description' in output_files:
            print(f"  - Video accesible: {output_files['video_with_audio_description']}")
        if 'subtitles' in output_files:
            print(f"  - Archivo de subtítulos: {output_files['subtitles']}")
        if 'audio_description' in output_files:
            print(f"  - Audio de descripciones: {output_files['audio_description']}")
        
        # Abrir directorio de salida
        print(f"\n📂 Todos los archivos se han guardado en: {os.path.abspath(output_dir)}")
        try:
            if os.name == 'nt':  # Windows
                os.startfile(output_dir)
            elif os.name == 'posix':  # Linux/Mac
                if 'darwin' in sys.platform:  # Mac
                    subprocess.run(['open', output_dir])
                else:  # Linux
                    subprocess.run(['xdg-open', output_dir])
            print("\n▶️ Abriendo directorio de salida...")
        except:
            pass
        
    except Exception as e:
        print(f"\n❌ Error durante el procesamiento: {str(e)}")
        # Sugerir soluciones comunes
        if "ffmpeg" in str(e).lower():
            print("\nSugerencia: Asegúrate de tener ffmpeg instalado y en el PATH del sistema.")
            print("Puedes descargarlo desde: https://ffmpeg.org/download.html")
        elif "whisper" in str(e).lower():
            print("\nSugerencia: Verifica que openai-whisper esté correctamente instalado:")
            print("pip install openai-whisper setuptools-rust")
        elif "vertex" in str(e).lower() or "google" in str(e).lower():
            print("\nSugerencia: Verifica tus credenciales de Google Cloud y variables de entorno.")
            print("Asegúrate de que GOOGLE_APPLICATION_CREDENTIALS esté configurado correctamente.")