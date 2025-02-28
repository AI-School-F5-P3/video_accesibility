from typing import List, Dict
import json
from datetime import timedelta

class Transcript:
    def __init__(self, segments: List[Dict] = None):
        """
        Initialize a transcript with optional segments.
        Each segment should have:
        - id: unique identifier
        - start: start time in milliseconds
        - end: end time in milliseconds
        - text: transcript text
        """
        self.segments = segments or []

    def add_segment(self, start: int, end: int, text: str) -> None:
        """Add a new segment to the transcript"""
        segment_id = str(len(self.segments) + 1)
        self.segments.append({
            "id": segment_id,
            "start": start,
            "end": end,
            "text": text
        })

    def get_segment(self, segment_id: str) -> Dict:
        """Get a specific segment by ID"""
        for segment in self.segments:
            if segment["id"] == segment_id:
                return segment
        return None

    def update_segment(self, segment_id: str, text: str = None, 
                      start: int = None, end: int = None) -> bool:
        """Update a segment's content"""
        for segment in self.segments:
            if segment["id"] == segment_id:
                if text is not None:
                    segment["text"] = text
                if start is not None:
                    segment["start"] = start
                if end is not None:
                    segment["end"] = end
                return True
        return False

    def to_srt(self) -> str:
        """Convert transcript to SRT format"""
        srt_parts = []
        for i, segment in enumerate(self.segments, 1):
            # Convert milliseconds to SRT timestamp format
            start = self._ms_to_srt_timestamp(segment["start"])
            end = self._ms_to_srt_timestamp(segment["end"])
            
            srt_parts.extend([
                str(i),
                f"{start} --> {end}",
                segment["text"],
                ""  # Empty line between entries
            ])
        
        return "\n".join(srt_parts)

    def to_json(self) -> str:
        """Convert transcript to JSON format"""
        return json.dumps({
            "segments": self.segments
        }, ensure_ascii=False, indent=2)

    def from_json(self, json_str: str) -> None:
        """Load transcript from JSON string"""
        data = json.loads(json_str)
        self.segments = data.get("segments", [])

    def from_srt(self, srt_content: str) -> None:
        """Load transcript from SRT format"""
        self.segments = []
        blocks = srt_content.strip().split("\n\n")
        
        for block in blocks:
            if not block.strip():
                continue
                
            lines = block.split("\n")
            if len(lines) < 3:
                continue
                
            # Parse timestamps
            timestamp_line = lines[1]
            start_str, end_str = timestamp_line.split(" --> ")
            
            # Convert SRT timestamps to milliseconds
            start_ms = self._srt_timestamp_to_ms(start_str)
            end_ms = self._srt_timestamp_to_ms(end_str)
            
            # Join all remaining lines as the text
            text = "\n".join(lines[2:])
            
            self.add_segment(start_ms, end_ms, text)

    def _ms_to_srt_timestamp(self, ms: int) -> str:
        """Convert milliseconds to SRT timestamp format"""
        hours = ms // 3600000
        ms = ms % 3600000
        minutes = ms // 60000
        ms = ms % 60000
        seconds = ms // 1000
        ms = ms % 1000
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{ms:03d}"

    def _srt_timestamp_to_ms(self, timestamp: str) -> int:
        """Convert SRT timestamp to milliseconds"""
        timestamp = timestamp.replace(",", ".")
        h, m, s = timestamp.split(":")
        hours = int(h)
        minutes = int(m)
        seconds = float(s)
        
        total_ms = (hours * 3600 + minutes * 60 + seconds) * 1000
        return int(total_ms)

    def get_duration(self) -> int:
        """Get total duration in milliseconds"""
        if not self.segments:
            return 0
        return max(segment["end"] for segment in self.segments)

    def get_word_count(self) -> int:
        """Get total word count"""
        return sum(len(segment["text"].split()) for segment in self.segments)

    @property
    def is_empty(self) -> bool:
        """Check if transcript has any content"""
        return len(self.segments) == 0