from pathlib import Path
import logging
import json
import os
import subprocess
import asyncio
from typing import Dict, List, Optional, Tuple
from ..core.video_analyzer import VideoAnalyzer
from ..core.text_processor import TextProcessor
from ..core.audio_processor import AudioProcessor
from ..core.speech_processor import SpeechProcessor
from ..models.scene import Scene

class AudioDescService:
    def __init__(self, settings):
        self.settings = settings
        self.video_analyzer = VideoAnalyzer(settings)
        self.text_processor = TextProcessor(settings)
        self.audio_processor = AudioProcessor(settings)
        self.speech_processor = SpeechProcessor(settings)
        self._processing_status = {}  # Estado de procesamiento por video_id
        
        # Crear directorios necesarios
        self.audio_dir = Path(self.settings.AUDIO_DIR)
        self.audio_dir.mkdir(parents=True, exist_ok=True)
        
        self.processed_dir = Path(self.settings.PROCESSED_DIR)
        self.processed_dir.mkdir(parents=True, exist_ok=True)

    async def generate_audiodescription(self, video_id: str, video_path: Path, options: Dict = None) -> Dict:
        """Genera una audiodescripción para un video"""
        try:
            options = options or {}
            
            # Actualizar estado
            self._update_status(video_id, "processing", "Iniciando análisis de video", 5)
            
            # Extraer escenas
            self._update_status(video_id, "processing", "Extrayendo escenas", 10)
            scenes = await self.video_analyzer.extract_scenes(video_path)
            
            # Detectar intervalos de silencio
            self._update_status(video_id, "processing", "Detectando intervalos de silencio", 25)
            silence_intervals = await self.speech_processor.detect_speech_silence(video_path)
            
            # Generar descripciones
            self._update_status(video_id, "processing", "Generando descripciones de escenas", 40)
            descriptions = await self.text_processor.generate_descriptions(
                scenes, 
                language=options.get('language', 'es'),
                style=options.get('style', 'neutral'),
                max_length=options.get('max_length', 150)
            )
            
            # Guardar descripciones en JSON
            desc_data = []
            for i, desc in enumerate(descriptions):
                desc_data.append({
                    "id": i,
                    "time": desc.time_point if hasattr(desc, 'time_point') else scenes[i].time_point,
                    "description": desc.text if hasattr(desc, 'text') else str(desc),
                    "duration": desc.duration if hasattr(desc, 'duration') else 5.0
                })
                
            desc_json_path = self.processed_dir / video_id / "descriptions.json"
            os.makedirs(os.path.dirname(desc_json_path), exist_ok=True)
            
            with open(desc_json_path, 'w', encoding='utf-8') as f:
                json.dump(desc_data, f, ensure_ascii=False, indent=2)
                
            # Sintetizar audio
            self._update_status(video_id, "processing", "Sintetizando voz para audiodescripciones", 60)
            voice_type = options.get('voice_type', 'es-ES-F')
            audio_files = await self.audio_processor.generate_audio_descriptions(
                descriptions=descriptions,
                voice_type=voice_type
            )
            
            # Fusionar audio
            self._update_status(video_id, "processing", "Fusionando audiodescripciones", 80)
            final_audio_path = await self.audio_processor.merge_audio_descriptions(
                video_path=video_path,
                descriptions=descriptions,
                audio_files=audio_files,
                output_path=self.audio_dir / f"{video_id}_described.mp3"
            )
            
            # Copiar también las descripciones JSON al directorio de audio para fácil acceso
            audio_json_path = self.audio_dir / f"{video_id}_descriptions.json"
            with open(audio_json_path, 'w', encoding='utf-8') as f:
                json.dump(desc_data, f, ensure_ascii=False, indent=2)
            
            # Actualizar estado
            self._update_status(video_id, "completed", "Audiodescripción generada correctamente", 100)
            
            return {
                "status": "completed",
                "video_id": video_id,
                "audio_path": str(final_audio_path),
                "description_json": str(desc_json_path),
                "description_count": len(descriptions)
            }
            
        except Exception as e:
            logging.error(f"Error generando audiodescripción: {str(e)}")
            self._update_status(video_id, "error", str(e))
            raise

    async def render_video_with_audiodesc(self, video_id: str, video_path: Path) -> Dict:
        """Renderiza un video con las audiodescripciones generadas"""
        try:
            # Actualizar estado
            self._update_status(video_id, "processing", "Iniciando renderizado con audiodescripciones", 5)
            
            # Verificar que existe el audio de audiodescripción
            audio_path = self.audio_dir / f"{video_id}_described.mp3"
            if not audio_path.exists():
                raise FileNotFoundError(f"No se encontró la audiodescripción para el video {video_id}")
            
            # Ruta de salida
            output_path = self.processed_dir / f"{video_id}_with_audiodesc.mp4"
            
            # Actualizar estado
            self._update_status(video_id, "processing", "Combinando video con audiodescripciones", 30)
            
            # Ejecutar FFmpeg para combinar
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
            
            # Ejecutar el comando
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            # Esperar a que termine el proceso
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                logging.error(f"Error en FFmpeg: {stderr.decode()}")
                raise Exception(f"Error al renderizar video: {stderr.decode()}")
            
            # Actualizar estado
            self._update_status(video_id, "completed", "Video con audiodescripciones generado correctamente", 100)
            
            return {
                "status": "completed",
                "video_id": video_id,
                "output_path": str(output_path)
            }
            
        except Exception as e:
            logging.error(f"Error renderizando video con audiodescripciones: {str(e)}")
            self._update_status(video_id, "error", str(e))
            raise

    async def get_audiodescription_data(self, video_id: str) -> List[Dict]:
        """Obtiene los datos de audiodescripción para un video"""
        try:
            # Buscar archivo JSON en directorio de procesamiento
            json_path = self.processed_dir / video_id / "descriptions.json"
            
            # Si no existe, buscar en directorio de audio
            if not json_path.exists():
                json_path = self.audio_dir / f"{video_id}_descriptions.json"
            
            if not json_path.exists():
                return []
            
            with open(json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            logging.error(f"Error obteniendo datos de audiodescripción: {str(e)}")
            return []

    async def generate_preview_audiodesc(self, video_id: str, scene_index: int, description: str) -> Dict:
        """Genera una audiodescripción de prueba para una escena específica"""
        try:
            # Actualizar estado
            self._update_status(video_id, "processing", f"Generando audiodescripción de prueba para escena {scene_index}", 10)
            
            # Generar el audio
            audio_path = self.audio_dir / f"{video_id}_preview_{scene_index}.mp3"
            
            # Crear objeto de descripción
            desc = {
                "text": description,
                "time_point": 0,  # No importa para la vista previa
                "duration": len(description.split()) * 0.5  # Estimación básica
            }
            
            # Generar audio
            audio_path = await self.audio_processor.generate_single_audio_description(
                desc,
                output_path=audio_path,
                voice_type="es-ES-F"  # Usar voz predeterminada
            )
            
            # Actualizar estado
            self._update_status(video_id, "completed", "Audiodescripción de prueba generada", 100)
            
            return {
                "status": "completed",
                "audio_path": str(audio_path),
                "description": description
            }
            
        except Exception as e:
            logging.error(f"Error generando audiodescripción de prueba: {str(e)}")
            self._update_status(video_id, "error", str(e))
            raise

    async def update_description(self, video_id: str, desc_id: int, new_text: str) -> Dict:
        """Actualiza una descripción específica"""
        try:
            # Obtener datos actuales
            desc_data = await self.get_audiodescription_data(video_id)
            
            if not desc_data:
                raise ValueError(f"No se encontraron descripciones para el video {video_id}")
            
            # Encontrar la descripción por ID
            desc_found = False
            for desc in desc_data:
                if desc["id"] == desc_id:
                    desc["description"] = new_text
                    desc_found = True
                    break
            
            if not desc_found:
                raise ValueError(f"No se encontró la descripción con ID {desc_id}")
            
            # Guardar cambios
            json_paths = [
                self.processed_dir / video_id / "descriptions.json",
                self.audio_dir / f"{video_id}_descriptions.json"
            ]
            
            for json_path in json_paths:
                if json_path.exists():
                    with open(json_path, 'w', encoding='utf-8') as f:
                        json.dump(desc_data, f, ensure_ascii=False, indent=2)
            
            # Regenerar audio para esta descripción
            audio_path = self.audio_dir / f"{video_id}_desc_{desc_id}.mp3"
            
            desc_obj = {
                "text": new_text,
                "time_point": desc["time"],
                "duration": desc["duration"]
            }
            
            await self.audio_processor.generate_single_audio_description(
                desc_obj,
                output_path=audio_path,
                voice_type="es-ES-F"  # Voz predeterminada
            )
            
            return {
                "status": "updated",
                "desc_id": desc_id,
                "description": new_text
            }
            
        except Exception as e:
            logging.error(f"Error actualizando descripción: {str(e)}")
            raise

    async def delete_audiodescription(self, video_id: str) -> bool:
        """Elimina las audiodescripciones de un video"""
        try:
            # Eliminar archivos de audio
            audio_files = list(self.audio_dir.glob(f"{video_id}*.mp3"))
            json_files = list(self.audio_dir.glob(f"{video_id}*.json"))
            
            for file in audio_files + json_files:
                if file.exists():
                    file.unlink()
            
            # Eliminar archivos de procesamiento
            proc_dir = self.processed_dir / video_id
            if proc_dir.exists():
                # Eliminar sólo los archivos de audiodescripción
                desc_json = proc_dir / "descriptions.json"
                if desc_json.exists():
                    desc_json.unlink()
            
            # Eliminar video con audiodescripción
            output_video = self.processed_dir / f"{video_id}_with_audiodesc.mp4"
            if output_video.exists():
                output_video.unlink()
            
            # Eliminar estado
            self._processing_status.pop(video_id, None)
            
            return True
            
        except Exception as e:
            logging.error(f"Error eliminando audiodescripción: {str(e)}")
            return False

    async def get_status(self, video_id: str) -> Dict:
        """Obtiene el estado del procesamiento de audiodescripciones"""
        return self._processing_status.get(video_id, {
            "status": "not_found",
            "progress": 0,
            "current_step": "No se encontró información de procesamiento",
            "error": None
        })

    def _update_status(self, video_id: str, status: str, message: str, progress: int = None):
        """Actualiza el estado de procesamiento"""
        if video_id not in self._processing_status:
            self._processing_status[video_id] = {
                "status": status,
                "progress": progress if progress is not None else 0,
                "current_step": message,
                "error": None if status != "error" else message
            }
        else:
            self._processing_status[video_id].update({
                "status": status,
                "current_step": message,
                "error": None if status != "error" else message
            })
            if progress is not None:
                self._processing_status[video_id]["progress"] = progress

    async def check_audiodesc_available(self, video_id: str) -> bool:
        """Comprueba si hay audiodescripciones disponibles para un video"""
        audio_path = self.audio_dir / f"{video_id}_described.mp3"
        return audio_path.exists()

    async def get_available_voices(self) -> List[Dict]:
        """Obtiene una lista de voces disponibles para audiodescripción"""
        try:
            # Esta función dependerá del proveedor de TTS que estés utilizando
            # Aquí proporcionamos algunas voces comunes en español
            return [
                {"id": "es-ES-F", "name": "Española femenina", "language": "es-ES", "gender": "female"},
                {"id": "es-ES-M", "name": "Española masculina", "language": "es-ES", "gender": "male"},
                {"id": "es-MX-F", "name": "Mexicana femenina", "language": "es-MX", "gender": "female"},
                {"id": "es-MX-M", "name": "Mexicana masculina", "language": "es-MX", "gender": "male"},
                {"id": "es-AR-F", "name": "Argentina femenina", "language": "es-AR", "gender": "female"}
            ]
        except Exception as e:
            logging.error(f"Error obteniendo voces disponibles: {str(e)}")
            return []