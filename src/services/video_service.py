from pathlib import Path
import uuid
import logging
import os
import subprocess
import aiofiles
import time
import asyncio
import json
from typing import Optional, Dict, List, Tuple
from fastapi import UploadFile
from ..core.video_analyzer import VideoAnalyzer
from ..core.text_processor import TextProcessor
from ..core.speech_processor import SpeechProcessor
from ..core.audio_processor import AudioProcessor
from ..models.scene import Scene
from ..utils.validators import validate_video_file

class VideoService:
    def __init__(self, settings):
        self.settings = settings
        self.video_analyzer = VideoAnalyzer(settings)
        self.text_processor = TextProcessor(settings)
        self.speech_processor = SpeechProcessor(settings)
        self.audio_processor = AudioProcessor(settings)
        self._processing_status = {}  # Store processing status
        
        # Crear directorios necesarios
        self.video_dir = Path("data/raw")
        self.video_dir.mkdir(parents=True, exist_ok=True)
        
        # Directorio para videos procesados
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    async def save_video(self, file: UploadFile) -> str:
        """Save uploaded video and return video_id"""
        try:
            # Generate unique ID for video
            video_id = str(uuid.uuid4())
            
            # Create video directory
            video_dir = self.settings.RAW_DIR / video_id
            video_dir.mkdir(parents=True, exist_ok=True)
            
            # Save video file
            video_path = video_dir / file.filename
            content = await file.read()
            with open(video_path, "wb") as f:
                f.write(content)
                
            # Initialize processing status
            self._processing_status[video_id] = {
                "status": "uploaded",
                "progress": 0,
                "current_step": "initialization",
                "error": None
            }
            
            return video_id
            
        except Exception as e:
            logging.error(f"Error saving video: {str(e)}")
            raise

    async def save_uploaded_video(self, video_id: str, file: UploadFile) -> Path:
        """Guarda un video subido y devuelve la ruta"""
        try:
            # Crear directorio si no existe
            video_dir = self.video_dir / video_id
            video_dir.mkdir(parents=True, exist_ok=True)
            
            # Guardar archivo
            file_ext = self._get_extension(file.filename)
            video_path = video_dir / f"{video_id}{file_ext}"
            
            # Asegurarnos de que el contenido del archivo está en la posición inicial
            await file.seek(0)
            
            # Verificar que el archivo no esté vacío
            first_chunk = await file.read(1024)
            if not first_chunk:
                raise ValueError("El archivo subido está vacío")
            
            # Guardar el archivo
            with open(video_path, 'wb') as out_file:
                # Escribir el primer chunk que ya leímos
                out_file.write(first_chunk)
                
                # Leer y escribir el resto del archivo
                while True:
                    chunk = await file.read(1024 * 1024)  # Leer en chunks de 1MB
                    if not chunk:
                        break
                    out_file.write(chunk)
            
            # Verificar que el archivo se guardó correctamente
            if not video_path.exists() or video_path.stat().st_size == 0:
                raise ValueError("Error al guardar el archivo: el archivo resultante está vacío")
            
            # Verificar que es un archivo de video válido
            probe_command = [
                'ffprobe',
                '-v', 'error',
                '-show_format',
                '-show_streams',
                str(video_path)
            ]
            
            result = subprocess.run(probe_command, capture_output=True, text=True)
            if result.returncode != 0:
                logging.error(f"Error validando video: {result.stderr}")
                raise ValueError("El archivo subido no es un video válido")
            
            # Actualizar estado
            self._processing_status[video_id] = {
                "status": "uploaded",
                "progress": 10,
                "current_step": "Video cargado correctamente",
                "error": None
            }
            
            return video_path
            
        except Exception as e:
            logging.error(f"Error saving uploaded video: {str(e)}")
            self._processing_status[video_id] = {
                "status": "error",
                "progress": 0,
                "current_step": "Error al guardar video",
                "error": str(e)
            }
            raise

    async def download_youtube_video(self, video_id: str, youtube_url: str) -> Path:
        """Descarga un video de YouTube y devuelve la ruta"""
        try:
            # Crear directorio si no existe
            video_dir = self.video_dir / video_id
            video_dir.mkdir(parents=True, exist_ok=True)
            video_path = video_dir / f"{video_id}.mp4"
            
            # Actualizar estado
            self._processing_status[video_id] = {
                "status": "processing",
                "progress": 5,
                "current_step": "Descargando video de YouTube",
                "error": None
            }
            
            # Usar yt-dlp con opciones más flexibles
            try:
                command = [
                    'yt-dlp',
                    '-f', 'best[ext=mp4]/best',  # Formato más flexible
                    '-o', str(video_path),
                    '--no-playlist',
                    youtube_url
                ]
                
                # Ejecutar comando
                result = subprocess.run(command, check=True, capture_output=True, text=True)
                logging.info(f"yt-dlp output: {result.stdout}")
                
            except subprocess.CalledProcessError as e:
                logging.error(f"Error en yt-dlp: {e.stderr if hasattr(e, 'stderr') else str(e)}")
                
                # Intentar una segunda vez con opciones más básicas
                logging.info("Intentando descarga alternativa...")
                alt_command = [
                    'yt-dlp',
                    '-f', 'best',  # Sin restricciones de formato
                    '-o', str(video_path),
                    '--no-playlist',
                    youtube_url
                ]
                subprocess.run(alt_command, check=True, capture_output=True)
            
            if not video_path.exists() or video_path.stat().st_size == 0:
                raise Exception(f"Error downloading video from {youtube_url}")
            
            # Actualizar estado
            self._processing_status[video_id] = {
                "status": "uploaded",
                "progress": 10,
                "current_step": "Video descargado correctamente",
                "error": None
            }
            
            return video_path
                
        except Exception as e:
            logging.error(f"Error downloading YouTube video: {str(e)}")
            self._processing_status[video_id] = {
                "status": "error",
                "progress": 0,
                "current_step": "Error al descargar video",
                "error": str(e)
            }
            raise

    async def analyze_video(self, video_id: str, options: Dict = None) -> Dict:
        """Process video with specified options"""
        try:
            video_path = await self.get_video_path(video_id)
            if not video_path:
                raise ValueError(f"Video not found: {video_id}")

            results = {}
            options = options or {}
            
            # Update status
            self._update_status(video_id, "processing", "Starting video analysis")
            
            # Extract scenes for analysis
            scenes = await self.video_analyzer.extract_scenes(video_path)
            self._update_status(video_id, "processing", "Scenes extracted", 20)

            # Generate audio description if requested
            if options.get('audioDesc'):
                desc_result = await self._generate_audio_description(
                    video_id,
                    video_path,
                    scenes,
                    voice_type=options.get('voice_type', 'es-ES-F')
                )
                results['audio_description'] = desc_result

            # Generate subtitles if requested
            if options.get('subtitles'):
                sub_result = await self._generate_subtitles(
                    video_id,
                    video_path,
                    format=options.get('subtitle_format', 'srt'),
                    language=options.get('language', 'es')
                )
                results['subtitles'] = sub_result

            # Update final status
            self._update_status(video_id, "completed", "Processing completed", 100)
            
            return results

        except Exception as e:
            self._update_status(video_id, "error", str(e))
            logging.error(f"Error processing video: {str(e)}")
            raise

    async def _generate_audio_description(
        self,
        video_id: str,
        video_path: Path,
        scenes: List[Scene],
        voice_type: str
    ) -> Dict:
        """Generate audio description for video"""
        try:
            self._update_status(video_id, "processing", "Detecting silence intervals", 30)
            silence_intervals = await self.speech_processor.detect_speech_silence(video_path)
            
            self._update_status(video_id, "processing", "Generating descriptions", 50)
            descriptions = await self.text_processor.generate_descriptions(scenes)
            
            self._update_status(video_id, "processing", "Synthesizing audio", 70)
            audio_files = await self.audio_processor.generate_audio_descriptions(
                descriptions=descriptions,
                voice_type=voice_type
            )
            
            self._update_status(video_id, "processing", "Merging audio", 90)
            final_audio = await self.audio_processor.merge_audio_descriptions(
                video_path=video_path,
                descriptions=descriptions,
                audio_files=audio_files
            )
            
            return {
                "status": "completed",
                "audio_path": str(final_audio),
                "description_count": len(descriptions)
            }
            
        except Exception as e:
            logging.error(f"Error generating audio description: {str(e)}")
            raise

    async def _generate_subtitles(
        self,
        video_id: str,
        video_path: Path,
        format: str = "srt",
        language: str = "es"
    ) -> Dict:
        """Generate subtitles for video"""
        try:
            self._update_status(video_id, "processing", "Transcribing audio", 40)
            transcript = await self.speech_processor.transcribe_video(video_path)
            
            self._update_status(video_id, "processing", "Generating subtitles", 60)
            subtitle_path = self.settings.TRANSCRIPTS_DIR / f"{video_id}_subtitles.{format}"
            
            # Format and save subtitles
            with open(subtitle_path, "w", encoding="utf-8") as f:
                if format == "srt":
                    f.write(transcript.to_srt())
                else:
                    f.write(transcript.to_json())
            
            return {
                "status": "completed",
                "subtitle_path": str(subtitle_path),
                "format": format,
                "language": language
            }
            
        except Exception as e:
            logging.error(f"Error generating subtitles: {str(e)}")
            raise

    async def get_video_path(self, video_id: str) -> Optional[Path]:
        """Obtiene la ruta del video por ID"""
        try:
            # Primero, buscar en el directorio del video_id
            video_dir = self.video_dir / video_id
            if video_dir.exists():
                # Buscar cualquier archivo de video en ese directorio
                for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                    files = list(video_dir.glob(f"*{ext}"))
                    if files:
                        return files[0]
                
                # Si no encuentra archivos con extensiones específicas, buscar cualquier archivo
                files = list(video_dir.glob("*"))
                if files:
                    return files[0]
            
            # Si no encuentra en el directorio específico, buscar en 'data/raw'
            for ext in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
                files = list(self.video_dir.glob(f"{video_id}*{ext}"))
                if files:
                    return files[0]
            
            return None
            
        except Exception as e:
            logging.error(f"Error getting video path: {str(e)}")
            return None

    def _update_status(
        self,
        video_id: str,
        status: str,
        message: str,
        progress: int = None
    ):
        """Update processing status"""
        if video_id in self._processing_status:
            self._processing_status[video_id].update({
                "status": status,
                "current_step": message,
                "error": None if status != "error" else message
            })
            if progress is not None:
                self._processing_status[video_id]["progress"] = progress

    async def get_status(self, video_id: str) -> Dict:
        """Get current processing status"""
        return self._processing_status.get(video_id, {
            "status": "not_found",
            "progress": 0,
            "current_step": None,
            "error": None
        })

    async def delete_video(self, video_id: str) -> bool:
        """Delete video and associated files"""
        try:
            # Buscar y eliminar archivos del video
            video_path = await self.get_video_path(video_id)
            if video_path and video_path.exists():
                video_path.unlink()
            
            # Eliminar directorio del video si existe
            video_dir = self.video_dir / video_id
            if video_dir.exists():
                # Eliminar todos los archivos dentro del directorio
                for file in video_dir.glob("*"):
                    file.unlink()
                # Eliminar el directorio vacío
                try:
                    video_dir.rmdir()
                except:
                    pass
            
            # Eliminar archivos de subtítulos
            subtitles_dir = Path("data/transcripts")
            if subtitles_dir.exists():
                subtitle_files = list(subtitles_dir.glob(f"{video_id}*.*"))
                for file in subtitle_files:
                    file.unlink()
            
            # Eliminar archivos de audio
            audio_dir = Path("data/audio")
            if audio_dir.exists():
                audio_files = list(audio_dir.glob(f"{video_id}*.*"))
                for file in audio_files:
                    file.unlink()
            
            # Eliminar datos procesados
            processed_dir = Path("data/processed") / video_id
            if processed_dir.exists():
                import shutil
                shutil.rmtree(processed_dir)
            
            # Eliminar videos procesados con audiodescripciones integradas
            integrated_video = Path(f"data/processed/{video_id}_with_audiodesc.mp4")
            if integrated_video.exists():
                integrated_video.unlink()
            
            # Clean up processing status
            self._processing_status.pop(video_id, None)
            
            return True
            
        except Exception as e:
            logging.error(f"Error deleting video: {str(e)}")
            return False
            
    def _get_extension(self, filename: str) -> str:
        """Extrae la extensión de un nombre de archivo"""
        if not filename:
            return ".mp4"  # Extensión predeterminada
        
        _, ext = os.path.splitext(filename)
        return ext if ext else ".mp4"

    async def render_with_audiodesc(self, video_id: str) -> bool:
        """
        Combina el video original con las audiodescripciones generadas para crear un nuevo video.
        """
        try:
            # Actualizar estado
            self._update_status(video_id, "processing", "Iniciando renderizado del video con audiodescripciones", 0)
            
            # Obtener rutas de archivos
            video_path = await self.get_video_path(video_id)
            if not video_path:
                raise ValueError(f"Video no encontrado: {video_id}")
            
            audio_path = Path(f"data/audio/{video_id}_described.mp3")
            if not audio_path.exists():
                raise ValueError(f"Audiodescripción no encontrada para video {video_id}")
            
            # Directorio para resultados
            output_dir = self.processed_dir
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Ruta del video de salida
            output_path = output_dir / f"{video_id}_with_audiodesc.mp4"
            
            # Actualizar estado
            self._update_status(video_id, "processing", "Combinando video con audiodescripciones", 20)
            
            # Usar FFmpeg para combinar el video con las audiodescripciones
            try:
                # Comando FFmpeg para combinar video con audio
                command = [
                    'ffmpeg',
                    '-i', str(video_path),  # Video original
                    '-i', str(audio_path),  # Audio con audiodescripciones
                    '-map', '0:v',  # Usar el stream de video del primer input
                    '-map', '1:a',  # Usar el stream de audio del segundo input
                    '-c:v', 'copy',  # Copiar el video sin re-codificar
                    '-c:a', 'aac',  # Codificar audio como AAC
                    '-b:a', '192k',  # Bitrate de audio
                    '-shortest',  # Terminar cuando el stream más corto acabe
                    '-y',  # Sobrescribir archivo de salida si existe
                    str(output_path)
                ]
                
                # Ejecutar comando
                result = subprocess.run(command, capture_output=True, text=True)
                
                if result.returncode != 0:
                    logging.error(f"Error en FFmpeg: {result.stderr}")
                    raise Exception(f"Error al renderizar video: {result.stderr}")
                
                # Verificar que el archivo de salida existe
                if not output_path.exists():
                    raise Exception("El archivo de salida no se generó correctamente")
                
                # Actualizar estado
                self._update_status(video_id, "completed", "Video con audiodescripciones generado correctamente", 100)
                
                return True
            
            except Exception as e:
                logging.error(f"Error en FFmpeg: {str(e)}")
                self._update_status(video_id, "error", f"Error al renderizar video: {str(e)}")
                return False
                
        except Exception as e:
            logging.error(f"Error rendering video with audiodescriptions: {str(e)}")
            self._update_status(video_id, "error", f"Error al renderizar video: {str(e)}")
            return False

    async def wait_and_render_with_audiodesc(self, video_id: str) -> bool:
        """
        Espera a que las audiodescripciones estén generadas y luego renderiza el video.
        """
        try:
            # Esperar a que las audiodescripciones estén completas
            max_wait_seconds = 600  # 10 minutos
            wait_interval = 5  # 5 segundos
            
            self._update_status(video_id, "waiting", "Esperando a que las audiodescripciones estén listas", 10)
            
            start_time = time.time()
            audiodesc_ready = False
            
            while time.time() - start_time < max_wait_seconds:
                # Verificar si las audiodescripciones están listas
                audio_path = Path(f"data/audio/{video_id}_described.mp3")
                if audio_path.exists():
                    audiodesc_ready = True
                    break
                
                # Esperar un tiempo antes de verificar de nuevo
                await asyncio.sleep(wait_interval)
            
            if not audiodesc_ready:
                self._update_status(video_id, "error", 
                                  "Tiempo de espera agotado para audiodescripciones", 0)
                return False
            
            # Renderizar el video
            return await self.render_with_audiodesc(video_id)
            
        except Exception as e:
            logging.error(f"Error waiting for audiodescriptions: {str(e)}")
            self._update_status(video_id, "error", f"Error al esperar audiodescripciones: {str(e)}")
            return False

    async def get_audiodesc_data(self, video_id: str) -> List[Dict]:
        """
        Obtiene los datos de las audiodescripciones para un video.
        """
        try:
            # Buscar archivo JSON con datos de audiodescripciones
            audiodesc_json = Path(f"data/audio/{video_id}_descriptions.json")
            if audiodesc_json.exists():
                with open(audiodesc_json, 'r', encoding='utf-8') as f:
                    return json.load(f)
            
            # Si no existe, intentar obtener de otra manera (depende de la implementación)
            return []
            
        except Exception as e:
            logging.error(f"Error getting audiodescription data: {str(e)}")
            return []

    def save_rendered_video_path(self, video_id: str, output_path: Path) -> None:
        """
        Guarda la ruta del video renderizado en el estado.
        """
        try:
            if video_id in self._processing_status:
                self._processing_status[video_id]["rendered_video_path"] = str(output_path)
                
        except Exception as e:
            logging.error(f"Error saving rendered video path: {str(e)}")