import os
import logging
from pathlib import Path
from PIL import Image
import tempfile
import time
import json
import subprocess
from gtts import gTTS

class AudioProcessor:
    def __init__(self, settings):
        self.settings = settings
        self.tts_client = None
        
        # Importaciones aquí para evitar dependencias circulares
        from src.core.video_analyzer import VideoAnalyzer
        from src.core.text_processor import TextProcessor
        
        self.video_analyzer = VideoAnalyzer(settings)
        self.text_processor = TextProcessor(settings)
        
        self.processing_status = {}  # Almacena el estado de procesamiento por video_id
        
        # Crear directorios necesarios
        audio_dir = Path("data/audio")
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Configuración TTS simple
        logging.info("Using gTTS for text-to-speech conversion")
    
    async def generate_description(self, video_id: str, video_path: Path, voice_type: str = "es"):
        """Genera audiodescripciones para el video"""
        try:
            # Código original para procesamiento real
            # Actualizar estado
            self.processing_status[video_id] = {
                "status": "processing",
                "progress": 0,
                "current_step": "Analizando video"
            }
            
            # Crear directorios
            audio_dir = Path("data/audio")
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            data_dir = Path("data/processed") / video_id
            data_dir.mkdir(parents=True, exist_ok=True)
            
            # Obtener duración del video
            video_duration = self._get_video_duration(video_path)
            logging.info(f"Video duration: {video_duration} seconds")
            
            # Extraer frames a intervalos regulares
            self.processing_status[video_id].update({
                "progress": 10,
                "current_step": "Extrayendo fotogramas clave"
            })
            
            # Podemos detectar escenas o simplemente tomar frames cada X segundos
            frame_interval = 10  # segundos
            timestamps = list(range(0, int(video_duration), frame_interval))
            
            descriptions = []
            for i, timestamp_sec in enumerate(timestamps):
                progress = int(10 + (i / len(timestamps)) * 40)  # Progreso entre 10% y 50%
                self.processing_status[video_id].update({
                    "progress": progress,
                    "current_step": f"Analizando escena {i+1} de {len(timestamps)}"
                })
                
                # Extraer frame
                timestamp_ms = timestamp_sec * 1000
                frame = self.video_analyzer.extract_frame(video_path, timestamp_ms)
                
                if frame:
                    # Guardar frame para referencia
                    frame_path = data_dir / f"frame_{i}.jpg"
                    frame.save(frame_path)
                    
                    # Generar descripción usando el procesador de texto (Gemini)
                    desc_text = self.text_processor.generate_description(frame, frame_interval * 1000)
                    
                    if desc_text:
                        logging.info(f"Generated description at {timestamp_sec}s: {desc_text}")
                        
                        # Añadir a la lista de descripciones
                        descriptions.append({
                            "id": str(i),
                            "start_time": timestamp_ms,
                            "end_time": min(timestamp_ms + (frame_interval * 1000), int(video_duration * 1000)),
                            "text": desc_text
                        })
            
            # Guardar descripciones en un archivo JSON
            desc_file = data_dir / "descriptions.json"
            with open(desc_file, 'w', encoding='utf-8') as f:
                json.dump(descriptions, f, ensure_ascii=False, indent=2)
            
            # Generar audio para cada descripción
            self.processing_status[video_id].update({
                "progress": 50,
                "current_step": "Generando archivos de audio"
            })
            
            # Lista para recopilar rutas de audio
            audio_files = []
            
            for i, desc in enumerate(descriptions):
                progress = int(50 + (i / len(descriptions)) * 40)  # Progreso entre 50% y 90%
                self.processing_status[video_id].update({
                    "progress": progress,
                    "current_step": f"Generando audio {i+1} de {len(descriptions)}"
                })
                
                # Generar archivo de audio para esta descripción
                audio_file = f"{video_id}_desc_{desc['id']}.mp3"
                audio_path = audio_dir / audio_file
                
                # Usar gTTS para generar audio
                tts = gTTS(text=desc['text'], lang=voice_type[:2])  # Tomar solo los 2 primeros caracteres (es-ES -> es)
                tts.save(str(audio_path))
                
                # Añadir ruta de audio a la descripción y a la lista
                desc["audio_file"] = str(audio_file)
                audio_files.append(audio_path)
            
            # Actualizar el archivo JSON con las rutas de audio
            with open(desc_file, 'w', encoding='utf-8') as f:
                json.dump(descriptions, f, ensure_ascii=False, indent=2)
            
            # Generar archivo de audio combinado
            self.processing_status[video_id].update({
                "progress": 90,
                "current_step": "Combinando archivos de audio"
            })
            
            combined_audio_path = audio_dir / f"{video_id}_described.mp3"
            
            # Combinamos los archivos de audio (versión simple)
            if audio_files:
                try:
                    # Preparar comando para combinar archivos de audio con ffmpeg
                    audio_inputs = []
                    for audio_file in audio_files:
                        audio_inputs.extend(['-i', str(audio_file)])
                    
                    # Usar filtro concat para unir los archivos
                    filter_complex = f"concat=n={len(audio_files)}:v=0:a=1"
                    
                    command = [
                        'ffmpeg',
                        *audio_inputs,
                        '-filter_complex', filter_complex,
                        '-y',  # Sobrescribir si existe
                        str(combined_audio_path)
                    ]
                    
                    # Ejecutar comando
                    subprocess.run(command, check=True, capture_output=True)
                    
                    logging.info(f"Audio combinado generado en: {combined_audio_path}")
                except Exception as e:
                    logging.error(f"Error al combinar audios: {str(e)}")
                    # Si hay error al combinar, usamos el primer archivo como audio principal
                    if audio_files:
                        try:
                            import shutil
                            shutil.copy2(str(audio_files[0]), str(combined_audio_path))
                            logging.info(f"Usando primer audio como principal: {combined_audio_path}")
                        except Exception as e2:
                            logging.error(f"Error al copiar audio: {str(e2)}")
            
            # Actualizar estado
            self.processing_status[video_id] = {
                "status": "completed",
                "progress": 100,
                "current_step": "Audiodescripción completada"
            }
            
            return {
                "status": "completed",
                "descriptions": descriptions,
                "audio_path": str(combined_audio_path)
            }
            
        except Exception as e:
            logging.error(f"Error generating audio description: {str(e)}")
            self.processing_status[video_id] = {
                "status": "error",
                "progress": 0,
                "current_step": f"Error: {str(e)}"
            }
            raise
    
    async def get_audiodescription(self, video_id: str):
        """Obtiene los datos de audiodescripción generados"""
        try:
            # Buscar archivo de descripciones JSON
            data_dir = Path("data/processed") / video_id
            desc_file = data_dir / "descriptions.json"
            
            if not desc_file.exists():
                logging.warning(f"No description file found for video {video_id}")
                return {
                    "descriptions": [],
                    "audio_path": ""
                }
            
            # Leer descripciones del archivo
            with open(desc_file, 'r', encoding='utf-8') as f:
                descriptions = json.load(f)
            
            # Verificar archivo de audio combinado
            audio_dir = Path("data/audio")
            combined_audio_path = audio_dir / f"{video_id}_described.mp3"
            
            return {
                "descriptions": descriptions,
                "audio_path": str(combined_audio_path) if combined_audio_path.exists() else ""
            }
                
        except Exception as e:
            logging.error(f"Error getting audio description: {str(e)}")
            return {
                "descriptions": [],
                "audio_path": ""
            }
    
    async def update_description(self, video_id: str, desc_id: str, new_text: str):
        """Actualiza una descripción y regenera su audio"""
        try:
            # Obtener descripciones actuales
            audiodesc = await self.get_audiodescription(video_id)
            descriptions = audiodesc.get("descriptions", [])
            
            # Buscar la descripción a actualizar
            updated_desc = None
            for desc in descriptions:
                if desc["id"] == desc_id:
                    desc["text"] = new_text
                    updated_desc = desc
                    break
            
            if not updated_desc:
                raise ValueError(f"Description with ID {desc_id} not found")
            
            # Guardar actualizaciones
            data_dir = Path("data/processed") / video_id
            desc_file = data_dir / "descriptions.json"
            data_dir.mkdir(parents=True, exist_ok=True)
            
            with open(desc_file, 'w', encoding='utf-8') as f:
                json.dump(descriptions, f, ensure_ascii=False, indent=2)
            
            # La regeneración del audio se hará de forma asíncrona
            return updated_desc
            
        except Exception as e:
            logging.error(f"Error updating description: {str(e)}")
            raise
    
    async def regenerate_audio(self, video_id: str, desc_id: str, voice_type: str = "es"):
        """Regenera el audio para una descripción específica"""
        try:
            # Obtener descripciones
            audiodesc = await self.get_audiodescription(video_id)
            descriptions = audiodesc.get("descriptions", [])
            
            # Buscar la descripción específica
            target_desc = None
            for desc in descriptions:
                if desc["id"] == desc_id:
                    target_desc = desc
                    break
            
            if not target_desc:
                raise ValueError(f"Description with ID {desc_id} not found")
            
            # Generar nuevo audio
            audio_dir = Path("data/audio")
            audio_dir.mkdir(parents=True, exist_ok=True)
            audio_file = f"{video_id}_desc_{desc_id}.mp3"
            audio_path = audio_dir / audio_file
            
            # Usar gTTS para generar audio
            tts = gTTS(text=target_desc["text"], lang=voice_type[:2])
            tts.save(str(audio_path))
            
            # Actualizar ruta de audio si es necesario
            if "audio_file" not in target_desc:
                target_desc["audio_file"] = audio_file
                
                # Guardar actualizaciones
                data_dir = Path("data/processed") / video_id
                desc_file = data_dir / "descriptions.json"
                data_dir.mkdir(parents=True, exist_ok=True)
                
                with open(desc_file, 'w', encoding='utf-8') as f:
                    json.dump(descriptions, f, ensure_ascii=False, indent=2)
            
            return {
                "status": "completed",
                "desc_id": desc_id,
                "audio_file": audio_file
            }
            
        except Exception as e:
            logging.error(f"Error regenerating audio: {str(e)}")
            return {
                "status": "error",
                "desc_id": desc_id,
                "error": str(e)
            }
    
    async def get_status(self, video_id: str):
        """Obtiene el estado del procesamiento"""
        if video_id in self.processing_status:
            return self.processing_status[video_id]
        
        # Si no tenemos estado guardado, verificamos si hay archivos
        audio_dir = Path("data/audio")
        combined_audio = audio_dir / f"{video_id}_described.mp3"
        
        data_dir = Path("data/processed") / video_id
        desc_file = data_dir / "descriptions.json"
        
        if desc_file.exists() and combined_audio.exists():
            return {
                "status": "completed",
                "progress": 100,
                "current_step": "Audiodescripción completada"
            }
        elif desc_file.exists():
            return {
                "status": "processing",
                "progress": 90,
                "current_step": "Generando archivo de audio final"
            }
        
        return {
            "status": "not_found",
            "progress": 0,
            "current_step": "No se encontró información de procesamiento"
        }
    
    def _get_video_duration(self, video_path: Path) -> float:
        """Obtiene la duración del video en segundos"""
        try:
            command = [
                'ffprobe',
                '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(video_path)
            ]
            
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                logging.warning(f"Error obteniendo duración del video, usando valor predeterminado: {result.stderr}")
                return 60.0
                
            return float(result.stdout.strip())
        except Exception as e:
            logging.error(f"Error getting video duration: {str(e)}")
            # Valor predeterminado si no podemos obtener la duración
            return 60.0  # Asumimos 1 minuto