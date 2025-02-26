from pathlib import Path
import json
import logging
from typing import Dict, List
from ..core.speech_processor import SpeechProcessor
from ..models.transcript import Transcript

class SubtitleService:
    def __init__(self, settings):
        self.settings = settings
        self.speech_processor = SpeechProcessor(settings)
        self._subtitle_cache = {}
        self._processing_status = {}  # Estado de procesamiento por video_id
        
        # Crear directorio de subtítulos si no existe
        subtitle_dir = Path(self.settings.TRANSCRIPTS_DIR)
        subtitle_dir.mkdir(parents=True, exist_ok=True)

    async def generate_subtitles(self, video_id: str, video_path: Path, target_language: str = "es", format: str = "srt"):
        """Generar subtítulos para un video usando Whisper"""
        try:
            self._processing_status[video_id] = {
                "status": "processing",
                "progress": 10,
                "current_step": "Transcribiendo audio"
            }
            
            transcript = await self.speech_processor.transcribe_video(video_path)
            
            self._processing_status[video_id].update({
                "progress": 70,
                "current_step": "Generando subtítulos"
            })
            
            subtitle_id = await self.create_subtitles(video_id, transcript, format)
            
            self._processing_status[video_id].update({
                "status": "completed",
                "progress": 100,
                "current_step": "Subtítulos generados"
            })
            
            return await self.get_subtitles(video_id, format)
            
        except Exception as e:
            logging.error(f"Error generating subtitles: {str(e)}")
            self._processing_status[video_id] = {
                "status": "error",
                "progress": 0,
                "current_step": f"Error: {str(e)}"
            }
            raise
    
    async def create_subtitles(self, video_id: str, transcript: Transcript, format: str = "srt") -> str:
        """Crear y guardar subtítulos a partir de la transcripción"""
        try:
            subtitle_id = f"{video_id}_{format}"
            output_path = self.settings.TRANSCRIPTS_DIR / f"{subtitle_id}.{format}"
            
            subtitle_content = transcript.to_srt() if format == "srt" else transcript.to_json()
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(subtitle_content)
            
            segments = []
            if hasattr(transcript, 'segments') and transcript.segments:
                if isinstance(transcript.segments[0], dict):
                    for i, seg in enumerate(transcript.segments):
                        segments.append({
                            "id": str(i+1),
                            "start": seg["start"], 
                            "end": seg["end"],     
                            "text": seg["text"]
                        })
                else:
                    for i, seg in enumerate(transcript.segments):
                        segments.append({
                            "id": str(i+1),
                            "start": seg.start,    
                            "end": seg.end,        
                            "text": seg.text
                        })
            
            self._subtitle_cache[subtitle_id] = {
                "video_id": video_id,
                "format": format,
                "path": str(output_path),
                "segments": segments
            }
            
            return subtitle_id
        
        except Exception as e:
            logging.error(f"Error creating subtitles: {str(e)}")
            raise

    async def get_subtitles(self, video_id: str, format: str = "srt") -> Dict:
        """Obtener subtítulos para un video"""
        try:
            subtitle_id = f"{video_id}_{format}"
            
            if subtitle_id in self._subtitle_cache:
                return self._subtitle_cache[subtitle_id]
            
            subtitle_path = self.settings.TRANSCRIPTS_DIR / f"{subtitle_id}.{format}"
            
            if not subtitle_path.exists():
                raise FileNotFoundError(f"Subtitles not found for video: {video_id}")
            
            with open(subtitle_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            segments = self._parse_srt(content) if format == "srt" else json.loads(content)
            
            subtitle_data = {
                "video_id": video_id,
                "format": format,
                "path": str(subtitle_path),
                "segments": segments
            }
            self._subtitle_cache[subtitle_id] = subtitle_data
            
            return subtitle_data
            
        except Exception as e:
            logging.error(f"Error getting subtitles: {str(e)}")
            raise

    def _parse_srt(self, content: str) -> List[Dict]:
        """Convertir subtítulos en formato SRT a una lista de segmentos"""
        segments = []
        blocks = content.strip().split("\n\n")
        
        for block in blocks:
            parts = block.split("\n")
            if len(parts) < 3:
                continue
                
            segment_id = parts[0].strip()
            time_line = parts[1].strip()
            
            if "-->" not in time_line:
                continue
                
            times = time_line.split(" --> ")
            start_ms = self._parse_timestamp(times[0])
            end_ms = self._parse_timestamp(times[1])
            
            text_lines = parts[2:]
            text = "\n".join(text_lines)
            
            segments.append({
                "id": segment_id,
                "start": start_ms,
                "end": end_ms,
                "text": text
            })
            
        return segments

    def _parse_timestamp(self, timestamp: str) -> int:
        """Convertir timestamps de SRT a milisegundos"""
        timestamp = timestamp.replace(",", ".")
        h, m, s = timestamp.split(":")
        return int(float(h) * 3600000 + float(m) * 60000 + float(s) * 1000)

    async def get_status(self, video_id: str):
        """Obtener el estado del procesamiento de subtítulos"""
        return self._processing_status.get(video_id, {
            "status": "not_found",
            "progress": 0,
            "current_step": "No se encontró información de procesamiento"
        })

    async def delete_subtitles(self, video_id: str):
        """Eliminar todos los subtítulos asociados con un video"""
        try:
            for format in ["srt", "json", "vtt"]:
                subtitle_id = f"{video_id}_{format}"
                subtitle_path = self.settings.TRANSCRIPTS_DIR / f"{subtitle_id}.{format}"
                
                if subtitle_path.exists():
                    subtitle_path.unlink()
                
                self._subtitle_cache.pop(subtitle_id, None)
            
        except Exception as e:
            logging.error(f"Error deleting subtitles: {str(e)}")
            raise
            
    async def update_subtitle(self, video_id: str, segment_id: str, updates: Dict):
        """Actualizar un segmento de subtítulos específico"""
        try:
            subtitle_data = await self.get_subtitles(video_id, "srt")
            segments = subtitle_data["segments"]
            
            # Buscar el segmento por ID
            updated_segment = None
            for segment in segments:
                if segment["id"] == segment_id:
                    # Aplicar actualizaciones
                    for key, value in updates.items():
                        segment[key] = value
                    updated_segment = segment
                    break
            
            if not updated_segment:
                raise ValueError(f"Segment with ID {segment_id} not found")
            
            # Reconstruir el archivo SRT
            subtitle_path = Path(subtitle_data["path"])
            srt_content = self._segments_to_srt(segments)
            
            with open(subtitle_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            
            # Actualizar caché
            subtitle_data["segments"] = segments
            self._subtitle_cache[f"{video_id}_srt"] = subtitle_data
            
            return updated_segment
            
        except Exception as e:
            logging.error(f"Error updating subtitle: {str(e)}")
            raise
    
    def _segments_to_srt(self, segments: List[Dict]) -> str:
        """Convertir segmentos a formato SRT"""
        srt_lines = []
        
        for segment in segments:
            # Formatear tiempos
            start_time = self._format_time(segment["start"])
            end_time = self._format_time(segment["end"])
            
            # Añadir bloque
            srt_lines.append(segment["id"])
            srt_lines.append(f"{start_time} --> {end_time}")
            srt_lines.append(segment["text"])
            srt_lines.append("")  # Línea vacía entre bloques
        
        return "\n".join(srt_lines)
    
    def _format_time(self, ms: int) -> str:
        """Convertir milisegundos a formato de tiempo SRT (HH:MM:SS,mmm)"""
        seconds, ms = divmod(ms, 1000)
        minutes, seconds = divmod(seconds, 60)
        hours, minutes = divmod(minutes, 60)
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"
    
    async def realign_subtitles(self, video_id: str, offset_ms: int):
        """Realinear subtítulos aplicando un desplazamiento en milisegundos"""
        try:
            subtitle_data = await self.get_subtitles(video_id, "srt")
            segments = subtitle_data["segments"]
            
            # Aplicar offset a todos los segmentos
            for segment in segments:
                segment["start"] = max(0, segment["start"] + offset_ms)
                segment["end"] = max(0, segment["end"] + offset_ms)
            
            # Reconstruir el archivo SRT
            subtitle_path = Path(subtitle_data["path"])
            srt_content = self._segments_to_srt(segments)
            
            with open(subtitle_path, "w", encoding="utf-8") as f:
                f.write(srt_content)
            
            # Actualizar caché
            subtitle_data["segments"] = segments
            self._subtitle_cache[f"{video_id}_srt"] = subtitle_data
            
            return {
                "video_id": video_id,
                "segments_updated": len(segments),
                "offset_ms": offset_ms
            }
            
        except Exception as e:
            logging.error(f"Error realigning subtitles: {str(e)}")
            raise