import cv2
import numpy as np
from pathlib import Path
import tempfile
import os
import logging
import subprocess
from pydub import AudioSegment
from ..models.transcript import Transcript
import whisper
import shutil


class SpeechProcessor:
    def __init__(self, settings):
        self.settings = settings
        self.whisper_model = whisper.load_model("medium", device="cpu")
    
    def detect_scenes(self, video_path: Path, threshold: float = 30.0) -> list[float]:
        try:
            # Open the video file
            video = cv2.VideoCapture(str(video_path))
            if not video.isOpened():
                logging.error(f"Could not open video file: {video_path}")
                return []
            
            # Get video properties
            fps = video.get(cv2.CAP_PROP_FPS)
            if fps <= 0:
                logging.error(f"Invalid FPS value: {fps}")
                return []
            
            # Initialize variables
            prev_frame = None
            scene_changes = []
            frame_count = 0
            
            # Process the video frame by frame
            while True:
                # Read a frame
                ret, frame = video.read()
                if not ret:
                    break
                
                # Convert to grayscale for faster processing
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                
                # Apply Gaussian blur to reduce noise
                blurred = cv2.GaussianBlur(gray, (5, 5), 0)
                
                if prev_frame is not None:
                    # Calculate frame difference
                    frame_diff = cv2.absdiff(blurred, prev_frame)
                    
                    # Calculate mean difference
                    mean_diff = np.mean(frame_diff)
                    
                    # Detect scene change if difference exceeds threshold
                    if mean_diff > threshold:
                        # Convert frame number to timestamp in milliseconds
                        timestamp = (frame_count * 1000) / fps
                        scene_changes.append(timestamp)
                        logging.debug(f"Scene change detected at {timestamp}ms (frame {frame_count})")
                
                # Save current frame for next comparison
                prev_frame = blurred
                frame_count += 1
            
            # Release the video
            video.release()
            
            return scene_changes
            
        except Exception as e:
            logging.error(f"Error detecting scenes: {str(e)}")
            return []
    
    def detect_speech_silence(self, video_path: Path, min_silence_len: int = 3000) -> list[tuple[float, float]]:
        temp_wav_path = None
        try:
            # Verificar que el archivo existe y es accesible
            if not video_path.exists():
                logging.error(f"Video file does not exist: {video_path}")
                return []
                
            # Verificar que el archivo tiene un tamaño válido
            if video_path.stat().st_size == 0:
                logging.error(f"Video file is empty: {video_path}")
                return []
                
            # Extract audio from video to WAV format
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
                
                try:
                    # Primero verificar si el video tiene un stream de audio usando ffprobe
                    probe_command = [
                        'ffprobe',
                        '-v', 'error',
                        '-select_streams', 'a:0',
                        '-show_entries', 'stream=codec_type',
                        '-of', 'csv=p=0',
                        str(video_path)
                    ]
                    
                    result = subprocess.run(probe_command, capture_output=True, text=True)
                    if result.returncode != 0 or not result.stdout.strip():
                        logging.warning(f"No audio stream found in video: {video_path}")
                        return []
                        
                    # Si hay un stream de audio, proceder con la extracción
                    extract_command = [
                        'ffmpeg',
                        '-i', str(video_path),
                        '-ac', '1',  # Convert to mono
                        '-ar', '16000',  # Set sample rate to 16kHz
                        '-y',
                        temp_wav_path
                    ]
                    
                    result = subprocess.run(extract_command, capture_output=True, text=True)
                    if result.returncode != 0:
                        logging.error(f"Error extracting audio: {result.stderr}")
                        return []
                        
                except Exception as e:
                    logging.error(f"Error in ffmpeg call: {str(e)}")
                    return []
                
                # Verificar que el archivo de salida existe y tiene tamaño
                if not os.path.exists(temp_wav_path) or os.path.getsize(temp_wav_path) == 0:
                    logging.error(f"Failed to extract audio to {temp_wav_path}")
                    return []
                
                # Load audio for analysis
                try:
                    audio = AudioSegment.from_wav(temp_wav_path)
                    duration = len(audio)
                except Exception as e:
                    logging.error(f"Error loading audio with pydub: {str(e)}")
                    return []
                
                # Transcribe with Whisper using more aggressive settings
                try:
                    result = self.whisper_model.transcribe(
                        temp_wav_path,
                        language="es",
                        word_timestamps=True,
                        condition_on_previous_text=True,
                        temperature=0.4,
                        no_speech_threshold=0.3,  # Make it more sensitive to detecting non-speech
                        logprob_threshold=-1.0    # More strict speech detection
                    )
                except Exception as e:
                    logging.error(f"Error transcribing with whisper: {str(e)}")
                    return []
                
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
                
                # Get scene changes from video analysis
                scene_changes = self.detect_scenes(video_path)
                
                # Use scene changes to refine non-speech segments
                refined_ranges = []
                
                for start, end in non_speech_ranges:
                    # Find scene changes within this non-speech range
                    scene_breaks = [sc for sc in scene_changes if start <= sc <= end]
                    
                    if not scene_breaks:
                        # No scene changes in this range, keep it as is
                        refined_ranges.append((start, end))
                    else:
                        # Add scene breaks to split the non-speech range
                        prev_point = start
                        for break_point in scene_breaks:
                            # Only create a segment if it's long enough
                            if break_point - prev_point >= min_silence_len / 2:  # Allow slightly shorter segments at scene boundaries
                                refined_ranges.append((prev_point, break_point))
                            prev_point = break_point
                        
                        # Add the final segment if long enough
                        if end - prev_point >= min_silence_len / 2:
                            refined_ranges.append((prev_point, end))
                
                # Also analyze volume changes for segments that don't have scene changes
                volume_refined_ranges = []
                
                for start, end in refined_ranges:
                    # Skip short segments
                    if end - start < min_silence_len * 1.5:
                        volume_refined_ranges.append((start, end))
                        continue
                    
                    # Check if this segment contains any scene changes
                    has_scene_change = any(start < sc < end for sc in scene_changes)
                    if has_scene_change:
                        volume_refined_ranges.append((start, end))
                        continue
                    
                    # Extract this non-speech segment for volume analysis
                    segment = audio[start:end]
                    
                    # Analyze volume changes using a sliding window
                    window_size = 1000  # 1 second windows
                    step_size = 250     # 250ms steps for more precise detection
                    
                    volume_profile = []
                    for window_start in range(0, len(segment) - window_size, step_size):
                        window_end = window_start + window_size
                        window = segment[window_start:window_end]
                        volume_profile.append((window_start + start, window.dBFS))
                    
                    # Look for significant volume jumps
                    volume_breaks = []
                    for i in range(1, len(volume_profile)):
                        curr_vol = volume_profile[i][1]
                        prev_vol = volume_profile[i-1][1]
                        
                        # Detect significant volume change (adjust threshold as needed)
                        if abs(curr_vol - prev_vol) > 3:  # 3dB threshold
                            volume_break_time = volume_profile[i][0]
                            volume_breaks.append(volume_break_time)
                    
                    # Filter out closely spaced breaks (keep only the most significant in each cluster)
                    filtered_breaks = []
                    if volume_breaks:
                        filtered_breaks.append(volume_breaks[0])
                        for break_point in volume_breaks[1:]:
                            # Only add if it's at least 2 seconds from the previous break
                            if break_point - filtered_breaks[-1] >= 2000:
                                filtered_breaks.append(break_point)
                    
                    # If we found volume breaks, split the segment
                    if not filtered_breaks:
                        volume_refined_ranges.append((start, end))
                    else:
                        prev_point = start
                        for break_point in filtered_breaks:
                            # Only add if the resulting segment is long enough
                            if break_point - prev_point >= min_silence_len / 2:
                                volume_refined_ranges.append((prev_point, break_point))
                            prev_point = break_point
                        
                        # Add the final segment if it's long enough
                        if end - prev_point >= min_silence_len / 2:
                            volume_refined_ranges.append((prev_point, end))
                
                return volume_refined_ranges
                
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
            # Verificar que el archivo existe y es accesible
            if not video_path.exists():
                raise FileNotFoundError(f"Video file does not exist: {video_path}")
                
            # Verificar que el archivo tiene un tamaño válido
            if video_path.stat().st_size == 0:
                raise ValueError(f"Video file is empty: {video_path}")
            
            # Extract audio to WAV
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
                
                # Primero verificar si el video tiene un stream de audio usando ffprobe
                try:
                    probe_command = [
                        'ffprobe',
                        '-v', 'error',
                        '-select_streams', 'a:0',
                        '-show_entries', 'stream=codec_type',
                        '-of', 'csv=p=0',
                        str(video_path)
                    ]
                    
                    result = subprocess.run(probe_command, capture_output=True, text=True)
                    logging.info(f"ffprobe result: {result.stdout.strip()}")
                    
                    if result.returncode != 0 or not result.stdout.strip():
                        logging.warning(f"No audio stream found in video: {video_path}")
                        # Crear un transcript vacío en caso de no haber audio
                        transcript = Transcript()
                        transcript.add_segment(0, 1000, "No se detectó audio en este video")
                        return transcript
                
                    # Si hay un stream de audio, proceder con la extracción
                    extract_command = [
                        'ffmpeg',
                        '-i', str(video_path),
                        '-ac', '1',
                        '-ar', '16000',
                        '-y',
                        temp_wav_path
                    ]
                    
                    process = subprocess.run(extract_command, capture_output=True, text=True)
                    
                    if process.returncode != 0:
                        logging.error(f"Error executing ffmpeg: {process.stderr}")
                        raise RuntimeError(f"Failed to extract audio: {process.stderr}")
                        
                except subprocess.CalledProcessError as e:
                    logging.error(f"ffmpeg error: {e.stderr if hasattr(e, 'stderr') else str(e)}")
                    raise
                except Exception as e:
                    logging.error(f"Error extracting audio: {str(e)}")
                    raise
                
                # Verificar que el archivo de salida existe y tiene tamaño
                if not os.path.exists(temp_wav_path) or os.path.getsize(temp_wav_path) == 0:
                    logging.error(f"Failed to extract audio to {temp_wav_path}")
                    raise RuntimeError(f"Failed to extract audio from video")
                
                # Transcribe with Whisper
                try:
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
                    logging.error(f"Error in whisper transcription: {str(e)}")
                    raise
            
        except Exception as e:
            logging.error(f"Error transcribing video: {str(e)}")
            # Crear un transcript mínimo para no fallar completamente
            transcript = Transcript()
            transcript.add_segment(0, 1000, f"Error al transcribir el video: {str(e)}")
            return transcript
        finally:
            # Limpiar el archivo temporal
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
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
                temp_wav_path = temp_wav.name
                
                # Extract audio to WAV
                try:
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
                    logging.error(f"Error processing word timestamps: {str(e)}")
                    return []
            
        except Exception as e:
            logging.error(f"Error getting word timestamps: {str(e)}")
            return []
        finally:
            if temp_wav_path and os.path.exists(temp_wav_path):
                try:
                    os.unlink(temp_wav_path)
                except Exception as e:
                    logging.warning(f"Could not delete temporary file {temp_wav_path}: {str(e)}")