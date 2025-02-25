import cv2
import numpy as np
from pathlib import Path
import tempfile
import os
import logging
import subprocess
from pydub import AudioSegment
import whisper

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
                temperature=0.4,
                no_speech_threshold=0.3,  # Make it more sensitive to detecting non-speech
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
    
    def merge_video_audio(self, video_path, audio_path, output_path):
        # Check if output directory exists, if not create it
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
                logging.info(f"Created output directory: {output_dir}")
            except Exception as e:
                logging.error(f"Failed to create output directory: {str(e)}")
                return False
        
        # Check if we have write permission to the output directory
        if not os.access(output_dir, os.W_OK):
            logging.error(f"No write permission for output directory: {output_dir}")
            return False
        
        # Check if output file already exists and if we can write to it
        if os.path.exists(output_path):
            if not os.access(output_path, os.W_OK):
                logging.error(f"Output file exists but no write permission: {output_path}")
                return False
            try:
                # Try to remove the existing file
                os.remove(output_path)
                logging.info(f"Removed existing output file: {output_path}")
            except Exception as e:
                logging.error(f"Failed to remove existing output file: {str(e)}")
                return False
        
        # Sanitize filenames - remove special characters that might cause issues
        safe_output_path = output_path
        if any(c in output_path for c in r'!@#$%^&*()=+[]{};\'"<>,?'):
            # Create a safe filename
            safe_name = ''.join(c if c.isalnum() or c in '._- \\/:' else '_' for c in output_path)
            safe_output_path = safe_name
            logging.warning(f"Using sanitized output path: {safe_output_path}")
        
        try:
            # FFmpeg command to merge video and audio
            merge_command = [
                'ffmpeg',
                '-i', str(video_path),
                '-i', str(audio_path),
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-strict', 'experimental',
                '-map', '0:v:0',
                '-map', '1:a:0',
                '-shortest',
                '-y',  # Overwrite output file if it exists
                safe_output_path
            ]
            
            # Run the command
            result = subprocess.run(merge_command, check=True, capture_output=True, text=True)
            logging.info(f"Successfully merged video and audio to: {safe_output_path}")
            return True
            
        except subprocess.CalledProcessError as e:
            logging.error(f"FFmpeg error during merging: {e.stderr}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error during merging: {str(e)}")
            return False