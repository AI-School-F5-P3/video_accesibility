from pathlib import Path
import logging
from ..core.video_analyzer import VideoAnalyzer
from ..core.speech_processor import SpeechProcessor
from ..core.text_processor import TextProcessor
from ..core.audio_processor import AudioProcessor
from ..utils.validators import VideoValidator
import yt_dlp

class VideoService:
    def __init__(self, settings):
        self.settings = settings
        self.video_analyzer = VideoAnalyzer(settings)
        self.speech_processor = SpeechProcessor(settings)
        self.text_processor = TextProcessor(settings)
        self.audio_processor = AudioProcessor(settings)
        self.validator = VideoValidator(settings)
        
    def process_youtube_video(self, url: str) -> dict:
        try:
            # Download video
            video_path = self._download_youtube_video(url)
            
            # Process video
            return self.process_video(video_path)
            
        except Exception as e:
            logging.error(f"Error processing YouTube video: {str(e)}")
            raise
            
    def process_video(self, video_path: Path) -> dict:
        try:
            # Validate video
            self.validator.validate_video(video_path)
            
            # Analyze video for silent segments
            silent_ranges = self.speech_processor.detect_speech_silence(video_path)
            
            # Generate descriptions for each segment
            descriptions = []
            for start_time, end_time in silent_ranges:
                frame = self.video_analyzer.extract_frame(video_path, start_time)
                if frame:
                    description = self.text_processor.generate_description(
                        frame, 
                        end_time - start_time
                    )
                    if description:
                        descriptions.append({
                            'start_time': start_time,
                            'end_time': end_time,
                            'description': description
                        })
            
            # Generate audio descriptions
            audio_files = self.audio_processor.generate_audio_descriptions(descriptions)
            
            # Merge audio descriptions
            final_audio = self.audio_processor.merge_audio_descriptions(
                video_path, 
                descriptions, 
                audio_files
            )
            
            # Create final video
            final_video = self.audio_processor.merge_video_audio(
                video_path, 
                final_audio
            )
            
            return {
                'video_path': str(final_video),
                'audio_path': str(final_audio),
                'script_path': str(self.text_processor.save_script(descriptions))
            }
            
        except Exception as e:
            logging.error(f"Error processing video: {str(e)}")
            raise
            
    def _download_youtube_video(self, url: str) -> Path:
        try:
            ydl_opts = {
                'format': 'best[ext=mp4]',
                'outtmpl': str(self.settings.RAW_DIR / '%(title)s.%(ext)s'),
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                return Path(ydl.prepare_filename(info))
                
        except Exception as e:
            logging.error(f"Error downloading YouTube video: {str(e)}")
            raise