from pathlib import Path
import json
import logging
from typing import Dict, List, Optional
from ..core.speech_processor import SpeechProcessor
from ..models.transcript import Transcript

class SubtitleService:
    def __init__(self, settings):
        self.settings = settings
        self.speech_processor = SpeechProcessor(settings)
        self._subtitle_cache = {}

    async def create_subtitles(
        self,
        video_id: str,
        transcript: Transcript,
        format: str = "srt"
    ) -> str:
        """Create and save subtitles from transcript"""
        try:
            subtitle_id = f"{video_id}_{format}"
            output_path = self.settings.TRANSCRIPTS_DIR / f"{subtitle_id}.{format}"
            
            # Format and save subtitles
            subtitle_content = transcript.to_srt() if format == "srt" else transcript.to_json()
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(subtitle_content)
            
            # Cache subtitle data
            self._subtitle_cache[subtitle_id] = {
                "video_id": video_id,
                "format": format,
                "path": str(output_path),
                "segments": transcript.segments
            }
            
            return subtitle_id
            
        except Exception as e:
            logging.error(f"Error creating subtitles: {str(e)}")
            raise

    async def get_subtitles(
        self,
        video_id: str,
        format: str = "srt"
    ) -> Dict:
        """Get subtitles for a video"""
        try:
            subtitle_id = f"{video_id}_{format}"
            
            # Check cache first
            if subtitle_id in self._subtitle_cache:
                return self._subtitle_cache[subtitle_id]
            
            # Look for subtitle file
            subtitle_path = self.settings.TRANSCRIPTS_DIR / f"{subtitle_id}.{format}"
            if not subtitle_path.exists():
                raise FileNotFoundError(f"Subtitles not found for video: {video_id}")
            
            # Read and parse subtitles
            with open(subtitle_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Parse based on format
            if format == "srt":
                segments = self._parse_srt(content)
            else:
                segments = json.loads(content)
            
            # Cache results
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

    async def update_subtitle(
        self,
        video_id: str,
        subtitle_id: str,
        updates: Dict
    ) -> Dict:
        """Update specific subtitle segment"""
        try:
            if subtitle_id not in self._subtitle_cache:
                raise ValueError(f"Subtitle not found: {subtitle_id}")
            
            subtitle_data = self._subtitle_cache[subtitle_id]
            
            # Update segments
            segment_id = updates.get("segment_id")
            new_text = updates.get("text")
            
            if segment_id is not None and new_text:
                for segment in subtitle_data["segments"]:
                    if segment["id"] == segment_id:
                        segment["text"] = new_text
                        break
                
                # Save updated subtitles
                await self._save_subtitles(subtitle_data)
            
            return subtitle_data
            
        except Exception as e:
            logging.error(f"Error updating subtitle: {str(e)}")
            raise

    async def _save_subtitles(self, subtitle_data: Dict):
        """Save subtitle data to file"""
        try:
            output_path = Path(subtitle_data["path"])
            format = subtitle_data["format"]
            
            content = self._format_subtitles(
                subtitle_data["segments"],
                format
            )
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(content)
                
        except Exception as e:
            logging.error(f"Error saving subtitles: {str(e)}")
            raise

    def _format_subtitles(self, segments: List[Dict], format: str) -> str:
        """Format subtitle segments based on format"""
        if format == "srt":
            return self._format_srt(segments)
        else:
            return json.dumps(segments, ensure_ascii=False, indent=2)

    def _format_srt(self, segments: List[Dict]) -> str:
        """Format segments as SRT"""
        srt_lines = []
        for i, segment in enumerate(segments, 1):
            start = self._format_timestamp(segment["start"])
            end = self._format_timestamp(segment["end"])
            srt_lines.extend([
                str(i),
                f"{start} --> {end}",
                segment["text"],
                ""
            ])
        return "\n".join(srt_lines)

    def _parse_srt(self, content: str) -> List[Dict]:
        """Parse SRT content into segments"""
        segments = []
        lines = content.strip().split("\n\n")
        
        for block in lines:
            if not block.strip():
                continue
                
            parts = block.split("\n")
            if len(parts) < 3:
                continue
                
            times = parts[1].split(" --> ")
            segments.append({
                "id": parts[0],
                "start": self._parse_timestamp(times[0]),
                "end": self._parse_timestamp(times[1]),
                "text": "\n".join(parts[2:])
            })
            
        return segments

    def _format_timestamp(self, ms: int) -> str:
        """Format milliseconds as SRT timestamp"""
        seconds = ms / 1000
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}".replace(".", ",")

    def _parse_timestamp(self, timestamp: str) -> int:
        """Parse SRT timestamp to milliseconds"""
        timestamp = timestamp.replace(",", ".")
        h, m, s = timestamp.split(":")
        return int(float(h) * 3600000 + float(m) * 60000 + float(s) * 1000)

    async def delete_subtitles(self, video_id: str):
        """Delete all subtitles associated with a video"""
        try:
            # Find and delete all subtitle files
            for format in ["srt", "json"]:
                subtitle_id = f"{video_id}_{format}"
                subtitle_path = self.settings.TRANSCRIPTS_DIR / f"{subtitle_id}.{format}"
                
                if subtitle_path.exists():
                    subtitle_path.unlink()
                
                # Remove from cache
                self._subtitle_cache.pop(subtitle_id, None)
                
        except Exception as e:
            logging.error(f"Error deleting subtitles: {str(e)}")
            raise