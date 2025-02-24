from pathlib import Path
import uuid
import logging
from typing import Optional, Dict, List
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

    async def analyze_video(self, video_id: str, options: Dict = None) -> Dict:
        """Process video with specified options"""
        try:
            video_path = self._get_video_path(video_id)
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

    def _get_video_path(self, video_id: str) -> Optional[Path]:
        """Get video file path from video_id"""
        video_dir = self.settings.RAW_DIR / video_id
        if not video_dir.exists():
            return None
            
        # Get first video file in directory
        video_files = list(video_dir.glob("*.mp4"))
        return video_files[0] if video_files else None

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

    async def delete_video(self, video_id: str):
        """Delete video and associated files"""
        try:
            video_dir = self.settings.RAW_DIR / video_id
            if video_dir.exists():
                for file in video_dir.glob("*"):
                    file.unlink()
                video_dir.rmdir()
            
            # Clean up processing status
            self._processing_status.pop(video_id, None)
            
        except Exception as e:
            logging.error(f"Error deleting video: {str(e)}")
            raise