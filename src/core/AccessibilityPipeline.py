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
        
        # Inicializar componentes (ahora correctamente indentados dentro de __init__)
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
            
            # Generar audiodescripción según UNE 153020
            logger.info("Generando audiodescripción según estándar UNE 153020...")
            audio_desc_path, audio_desc_script = self._generate_audio_description(video_path, scenes)
            logger.info(f"Audiodescripción generada y guardada en: {audio_desc_path}")
            
            # Generar guion completo minuto a minuto
            logger.info("Generando guion completo minuto a minuto...")
            full_script_path = self._generate_full_script(video_path, subtitles_data, self.descriptions_data)
            logger.info(f"Guion completo generado y guardado en: {full_script_path}")
            
            # Generar video final con audiodescripción y subtítulos
            logger.info("Generando video final con accesibilidad completa...")
            final_video = self._merge_audio_description(video_path, audio_desc_path, srt_path)
            logger.info(f"Video final generado y guardado en: {final_video}")
            
            # Preparar archivos para descarga
            output_files = self._prepare_output_files(
                video_path, 
                srt_path,
                audio_desc_path,
                audio_desc_script,
                full_script_path,
                final_video
            )
            
            logger.info("¡Procesamiento completado con éxito!")
            return output_files
            
        except Exception as e:
            logger.error(f"Error en el procesamiento: {e}")
            raise

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
            start = str(timedelta(seconds=int(segment['start']))).replace('.', ',')
            end = str(timedelta(seconds=int(segment['end']))).replace('.', ',')
            
            # Formatear texto según UNE 153010
            formatted_subtitles = self.text_processor.format_subtitles(segment['text'])
            
            for subtitle in formatted_subtitles:
                srt_content.extend([
                    str(i),
                    f"{start} --> {end}",
                    subtitle['text'],
                    ""
                ])
                
                # Guardar datos para uso posterior
                subtitles_data.append({
                    'index': i,
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': subtitle['text']
                })
        
        # Asegurar que el directorio exista antes de escribir el archivo
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Guardar archivo SRT
        srt_path = self.output_dir / "subtitles.srt"
        with open(srt_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(srt_content))
            
        return str(srt_path), subtitles_data

    def _generate_audio_description(self, video_path: str, scenes=None) -> tuple[str, str]:
        """
        Genera audiodescripción según UNE 153020 con mejor calidad de audio.
        
        Returns:
            Tuple con ruta al archivo de audio y script
        """
        logger.info("Generando audiodescripción...")
        
        # Detectar escenas y silencios
        if scenes is None:
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
        
        # Almacenar descripciones para uso posterior
        self.descriptions_data = descriptions

        # Mejorar calidad de texto antes de síntesis
        for desc in descriptions:
            desc['text'] = self.text_processor.format_audio_description(
                desc['text'],
                max_duration=desc['end'] - desc['start']
            )
        
        # Generar script completo para mejor coherencia
        script_content = []
        for desc in descriptions:
            script_content.extend([
                f"[{desc['start']:.2f} - {desc['end']:.2f}]",
                desc['text'],
                ""
            ])
        
        # Guardar script
        script_path = self.output_dir / "audio_description_script.txt"
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(script_content))
        
        # Mejorar generación de audio
        audio_segments = []
        
        # Opciones de voz mejoradas (ajustar según el sintetizador disponible)
        voice_options = {
            'rate': 0.9,  # Velocidad ligeramente más lenta para mejor comprensión
            'pitch': 1.0,  # Tono natural
            'volume': 1.2  # Volumen ligeramente aumentado para destacar sobre el audio original
        }
        
        for desc in descriptions:
            # Crear nombre de archivo sin espacios
            filename = f"desc_{desc['start']:.2f}.mp3"
            audio_file = self.temp_dir / filename

            # Generar audio con opciones mejoradas
            audio_file = self.voice_synthesizer.generate_audio(
                desc['text'], 
                rate=voice_options['rate'],
                pitch=voice_options['pitch']
            )
            
            if audio_file:
                audio_segments.append({
                    'file': audio_file,
                    'start': desc['start']
                })
        
        # Combinar segmentos de audio con mejor calidad
        final_audio = self._combine_audio_segments(audio_segments)
        
        # Mejorar calidad del audio final
        enhanced_audio_path = self.output_dir / "audio_description_enhanced.mp3"
        try:
            # Normalizar y mejorar calidad del audio
            subprocess.run([
                'ffmpeg', '-y',
                '-i', final_audio,
                '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11,highpass=f=200,lowpass=f=3000',  # Normalización y filtros para claridad
                '-ar', '48000',  # Alta frecuencia de muestreo
                '-b:a', '192k',  # Bitrate alto
                str(enhanced_audio_path)
            ], check=True)
            
            return str(enhanced_audio_path), str(script_path)
        except subprocess.CalledProcessError:
            # Si falla la mejora, usar el audio original
            logger.warning("No se pudo mejorar el audio, usando versión original")
            return final_audio, str(script_path)

    def _combine_audio_segments(self, segments: List[Dict[str, Any]]) -> str:
        """Combina segmentos de audio con silencios entre ellos."""
        combined = AudioSegment.silent(duration=0)
        
        for segment in segments:
            # Añadir silencio hasta el tiempo de inicio
            silence_duration = int(segment['start'] * 1000) - len(combined)
            if silence_duration > 0:
                combined += AudioSegment.silent(duration=silence_duration)
            
            # Añadir segmento de audio
            try:
                audio = AudioSegment.from_file(segment['file'])
                combined += audio
            except Exception as e:
                logger.error(f"Error al procesar archivo de audio '{segment['file']}': {e}")
        
        
        # Guardar audio final
        output_path = self.output_dir / "audio_description.mp3"
        combined.export(output_path, format="mp3")
        
        return str(output_path)

    def _generate_full_script(self, video_path, subtitles, audio_descriptions):
        """
        Genera un guion completo del video combinando transcripciones y descripciones,
        organizando el contenido minuto a minuto.
        
        Args:
            video_path (str): Ruta al video
            subtitles (list): Lista de subtítulos procesados
            audio_descriptions (list): Lista de descripciones de audio
            
        Returns:
            str: Ruta al archivo de guion generado
        """
        logger.info("Generando guion completo minuto a minuto...")
        
        # Obtener duración total del video
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
            capture_output=True,
            text=True
        )
        total_duration = float(result.stdout)
        
        # Preparar datos para segmentación por minutos
        minute_segments = {}
        total_minutes = int(total_duration / 60) + 1
        
        # Organizar subtítulos por minutos
        for sub in subtitles:
            minute = int(sub['start'] / 60)
            if minute not in minute_segments:
                minute_segments[minute] = {"subtitles": [], "descriptions": []}
            minute_segments[minute]["subtitles"].append(sub)
        
        # Organizar descripciones por minutos
        for desc in audio_descriptions:
            minute = int(desc['start'] / 60)
            if minute not in minute_segments:
                minute_segments[minute] = {"subtitles": [], "descriptions": []}
            minute_segments[minute]["descriptions"].append(desc)
        
        # Generar guion completo con IA
        prompt = f"""
        Actúa como un guionista profesional especializado en audiodescripción según la norma UNE 153020.
        
        Crea un guion completo MINUTO A MINUTO del siguiente video con duración total de {total_minutes} minutos.
        El guion debe incluir tanto los diálogos (subtítulos) como las descripciones visuales (audiodescripción).
        
        Para cada minuto, incluye una sección claramente identificada (MINUTO 1, MINUTO 2, etc.) y detalla TODO lo que sucede
        en ese segmento de tiempo, integrando diálogos y elementos visuales.
        
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
                
                if data["descriptions"]:
                    prompt += "\nDESCRIPCIONES VISUALES:\n"
                    for desc in data["descriptions"]:
                        time_str = f"{desc['start']:.2f}s - {desc['end']:.2f}s"
                        prompt += f"- [{time_str}] {desc['text']}\n"
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
        """

        # Usar VertexAI para generar el guion
        response = self.vertex_model.generate_content(prompt)
        script = response.text
        
        # Guardar guion completo
        script_path = self.output_dir / "full_script_minute_by_minute.txt"
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(script)
        
        return str(script_path)

    def _merge_audio_description(self, video_path: str, audio_desc_path: str, srt_path: str) -> str:
        """
        Combina el video original con la audiodescripción y subtítulos con mejor calidad.
        
        Args:
            video_path (str): Ruta al video original
            audio_desc_path (str): Ruta al audio de la descripción
            srt_path (str): Ruta al archivo SRT de subtítulos
            
        Returns:
            Ruta al video final
        """
        logger.info("Generando video final con audiodescripción y subtítulos...")
        
        output_path = self.output_dir / "video_with_accessibility.mp4"
        
        # Nos aseguramos de que el directorio de salida exista
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Normalizar rutas para evitar problemas con espacios y caracteres especiales
        video_path_norm = str(Path(video_path).resolve())
        audio_desc_path_norm = str(Path(audio_desc_path).resolve())
        srt_path_norm = str(Path(srt_path).resolve())
        output_path_norm = str(output_path.resolve())

        # Mezclar audio original con audiodescripción con mejor calidad de mezcla
        temp_audio_path = self.temp_dir / "mixed_audio.aac"
        temp_audio_path_norm = str(temp_audio_path.resolve())

        # Extraer audio original primero
        original_audio_path = self.temp_dir / "original_audio.aac"
        original_audio_path_norm = str(original_audio_path.resolve())
        
        try:
            # Extraer audio original y normalizar su volumen
            subprocess.run([
                'ffmpeg', '-y',
                '-i', video_path_norm,
                '-vn',
                '-af', 'loudnorm=I=-18:TP=-1.5:LRA=11', # Normalizar volumen
                '-c:a', 'aac',
                '-b:a', '192k',
                original_audio_path_norm
            ], check=True, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error extracting original audio: {e.stderr}")
            raise
        
        # Mezclar ambos audios con método avanzado para mejor integración
        try:
            subprocess.run([
                'ffmpeg', '-y',
                '-i', original_audio_path_norm,
                '-i', audio_desc_path_norm,
                '-filter_complex', 
                # Complejidad adicional: Bajar volumen de audio original durante descripciones
                '[0:a]volume=1.0[original];'
                '[1:a]volume=1.2[desc];'
                '[original][desc]amix=inputs=2:duration=first:dropout_transition=0.5,'
                'dynaudnorm=f=200:g=3:p=0.5',  # Normalización dinámica
                '-c:a', 'aac',
                '-b:a', '256k',  # Mayor bitrate para mejor calidad
                '-ar', '48000',  # Alta frecuencia de muestreo
                temp_audio_path_norm
            ], check=True, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error mixing audio: {e.stderr}")
            # Intentar método alternativo si falla
            try:
                logger.info("Intentando método alternativo para mezclar audio...")
                subprocess.run([
                    'ffmpeg', '-y',
                    '-i', original_audio_path_norm,
                    '-i', audio_desc_path_norm,
                    '-filter_complex', 
                    '[0:a][1:a]amix=inputs=2:duration=first:weights=0.8 0.9',  # Mezcla con pesos
                    '-c:a', 'aac',
                    '-b:a', '192k',
                    temp_audio_path_norm
                ], check=True, stderr=subprocess.PIPE, text=True)
            except subprocess.CalledProcessError as e2:
                logger.error(f"FFmpeg error con método alternativo: {e2.stderr}")
                raise
        
        # Configuración mejorada de subtítulos (según UNE 153010)
        # Escapar la ruta del archivo de subtítulos para Windows
        if os.name == 'nt':  # Windows
            srt_path_escaped = srt_path_norm.replace('\\', '\\\\').replace(':', '\\:')
        else:  # Linux/Mac
            srt_path_escaped = srt_path_norm.replace(':', '\\:')
        
        # Añadir subtítulos al video final con estilo UNE
        try:
            subtitle_style = (
                'FontName=Arial,FontSize=24,PrimaryColour=&HFFFFFF,BackColour=&H80000000,'
                'OutlineColour=&H000000,BorderStyle=3,Outline=1,Shadow=1,MarginV=20,'
                'Alignment=2'  # Centrado en la parte inferior
            )
            
            subprocess.run([
                'ffmpeg', '-y',
                '-i', video_path_norm,
                '-i', temp_audio_path_norm,
                '-c:v', 'libx264',
                '-preset', 'slow',  # Mejor calidad de codificación
                '-crf', '18',  # Alta calidad visual
                '-c:a', 'aac',
                '-b:a', '192k',
                '-vf', f"subtitles='{srt_path_escaped}':force_style='{subtitle_style}'",
                '-metadata', 'title="Video con audiodescripción según UNE 153020"',
                '-metadata', 'comment="Subtítulos según UNE 153010"',
                output_path_norm
            ], check=True, stderr=subprocess.PIPE, text=True)
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error adding subtitles: {e.stderr}")
            raise
        
        return str(output_path)
    
    def _prepare_output_files(self, 
                            video_path: str,
                            srt_path: str,
                            audio_desc_path: str,
                            audio_desc_script: str,
                            full_script_path: str,
                            final_video_path: str) -> Dict[str, str]:
        """Prepara y organiza archivos finales."""
        # Copiar archivos a directorio final
        final_paths = {
            'subtitles': srt_path,
            'audio_description': audio_desc_path,
            'audio_description_script': audio_desc_script,
            'full_script': full_script_path,
            'video_with_audio_description': final_video_path
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