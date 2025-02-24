import logging
import os
import whisper
import tempfile
from pathlib import Path
import subprocess
from pydub import AudioSegment
from ..models.transcript import Transcript


class SpeechProcessor:
    def __init__(self, settings):
        self.settings = settings
        self.whisper_model = whisper.load_model("medium", device="cpu")
        
    def detect_speech_silence(self, video_path: Path, min_silence_len: int = 3000) -> list[tuple[float, float]]:
        temp_wav_path = None
        try:
            # Create temporary file with a unique name
            temp_wav_fd, temp_wav_path = tempfile.mkstemp(suffix='.wav')
            os.close(temp_wav_fd)
            
            # Extract audio from video to WAV format
            extract_command = [
                'ffmpeg',
                '-i', str(video_path),
                '-ac', '1',  # Convert to mono
                '-ar', '16000',  # Set sample rate to 16kHz
                '-y',
                temp_wav_path
            ]
            
            subprocess.run(extract_command, check=True, capture_output=True)
            
            # Load audio for analysis
            audio = AudioSegment.from_wav(temp_wav_path)
            duration = len(audio)
            
            # Transcribe with Whisper using more aggressive settings
            result = self.whisper_model.transcribe(
                temp_wav_path,
                language="es",
                word_timestamps=True,
                condition_on_previous_text=True,
                temperature=0.2,
                no_speech_threshold=0.4,  # Make it more sensitive to detecting non-speech
                logprob_threshold=-1.0    # More strict speech detection
            )
            
            # Process segments to find non-speech gaps
            non_speech_ranges = []
            last_end = 0
            min_confidence = 0.5  # Minimum confidence threshold for speech detection
            
            # Sort segments by start time
            segments = sorted(result["segments"], key=lambda x: x["start"])
            
            for segment in segments:
                start_time = segment["start"] * 1000  # Convert to milliseconds
                end_time = segment["end"] * 1000
                
                # Calculate segment confidence safely
                words = segment.get('words', [])
                if words:
                    # If we have words, calculate average confidence
                    confidence_sum = sum(word.get('probability', 0) for word in words)
                    segment_confidence = confidence_sum / len(words)
                else:
                    # If no words, treat as non-speech
                    segment_confidence = 0
                
                # If we have a significant gap and low confidence, mark as non-speech
                if start_time - last_end >= min_silence_len:
                    non_speech_ranges.append((last_end, start_time))
                
                # Only update last_end if this was a confident speech segment
                if segment_confidence >= min_confidence:
                    last_end = end_time
            
            # Check final segment
            if duration - last_end >= min_silence_len:
                non_speech_ranges.append((last_end, duration))
            
            # Merge overlapping or very close ranges
            merged_ranges = []
            if non_speech_ranges:
                current_start, current_end = non_speech_ranges[0]
                
                for start, end in non_speech_ranges[1:]:
                    if start - current_end <= 1000:  # If gaps are within 1 second
                        current_end = end
                    else:
                        merged_ranges.append((current_start, current_end))
                        current_start, current_end = start, end
                
                merged_ranges.append((current_start, current_end))
            
            # Filter out any ranges that are too short
            return [(start, end) for start, end in merged_ranges if (end - start) >= min_silence_len]
            
        except Exception as e:
            logging.error(f"Error detecting non-speech segments: {str(e)}")
            return []
            
        finally:
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.unlink(temp_wav_path)
                except Exception as e:
                    logging.warning(f"Could not delete temporary file {temp_wav_path}: {str(e)}")

    async def transcribe_video(self, video_path: Path) -> Transcript:
        """Transcribe video audio to text using Whisper"""
        temp_wav_path = None
        try:
            # Create temporary WAV file
            temp_wav_fd, temp_wav_path = tempfile.mkstemp(suffix='.wav')
            os.close(temp_wav_fd)
            
            # Extract audio to WAV
            extract_command = [
                'ffmpeg',
                '-i', str(video_path),
                '-ac', '1',
                '-ar', '16000',
                '-y',
                temp_wav_path
            ]
            
            subprocess.run(extract_command, check=True, capture_output=True)
            
            # Transcribe with Whisper
            result = self.whisper_model.transcribe(
                temp_wav_path,
                language=self.settings.LANGUAGE_CODE[:2],  # Use first 2 chars (e.g., 'es' from 'es-ES')
                word_timestamps=True,
                condition_on_previous_text=True,
                temperature=0.2
            )
            
            # Create Transcript object
            transcript = Transcript()
            
            # Process segments
            for segment in result["segments"]:
                start_ms = int(segment["start"] * 1000)
                end_ms = int(segment["end"] * 1000)
                text = segment["text"].strip()
                
                if text:  # Only add non-empty segments
                    transcript.add_segment(start_ms, end_ms, text)
            
            return transcript
            
        except Exception as e:
            logging.error(f"Error transcribing video: {str(e)}")
            raise
            
        finally:
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.unlink(temp_wav_path)
                except Exception as e:
                    logging.warning(f"Could not delete temporary file {temp_wav_path}: {str(e)}")

    async def get_word_timestamps(self, video_path: Path) -> list[dict]:
        """Get precise word-level timestamps"""
        temp_wav_path = None
        try:
            # Create temporary WAV file
            temp_wav_fd, temp_wav_path = tempfile.mkstemp(suffix='.wav')
            os.close(temp_wav_fd)
            
            # Extract audio to WAV
            extract_command = [
                'ffmpeg',
                '-i', str(video_path),
                '-ac', '1',
                '-ar', '16000',
                '-y',
                temp_wav_path
            ]
            
            subprocess.run(extract_command, check=True, capture_output=True)
            
            # Transcribe with word timestamps
            result = self.whisper_model.transcribe(
                temp_wav_path,
                language=self.settings.LANGUAGE_CODE[:2],
                word_timestamps=True
            )
            
            # Extract word timestamps
            word_times = []
            for segment in result["segments"]:
                for word in segment.get("words", []):
                    word_times.append({
                        "word": word["word"],
                        "start": int(word["start"] * 1000),
                        "end": int(word["end"] * 1000),
                        "probability": word.get("probability", 0)
                    })
            
            return word_times
            
        except Exception as e:
            logging.error(f"Error getting word timestamps: {str(e)}")
            raise
            
        finally:
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.unlink(temp_wav_path)
                except Exception as e:
                    logging.warning(f"Could not delete temporary file {temp_wav_path}: {str(e)}")

    def _extract_audio(self, video_path: Path) -> Path:
        """Extract audio from video to temporary WAV file"""
        temp_wav_fd, temp_wav_path = tempfile.mkstemp(suffix='.wav')
        os.close(temp_wav_fd)
        
        extract_command = [
            'ffmpeg',
            '-i', str(video_path),
            '-ac', '1',
            '-ar', '16000',
            '-y',
            temp_wav_path
        ]
        
        subprocess.run(extract_command, check=True, capture_output=True)
        return Path(temp_wav_path)