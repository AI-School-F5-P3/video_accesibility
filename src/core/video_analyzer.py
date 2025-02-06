import cv2
import numpy as np
from pathlib import Path
import logging
from typing import List, Tuple, Dict
from google.cloud import vision
import io
import json

class FrameAnalyzer:
    """
    Analyzes individual frames using Google Cloud Vision API.
    Think of it as having a visual expert examining each frame of your video.
    """
    def __init__(self):
        # Initialize the Google Vision client
        self.client = vision.ImageAnnotatorClient()
        self.logger = logging.getLogger(__name__)

    def analyze_frame(self, frame_path: str) -> Dict:
        """
        Analyzes a single frame and returns all the information it finds.
        """
        try:
            # Read the frame image
            with io.open(frame_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)
            
            # Request multiple types of analysis from Google Vision
            response = self.client.annotate_image({
                'image': image,
                'features': [
                    {'type_': vision.Feature.Type.OBJECT_LOCALIZATION},
                    {'type_': vision.Feature.Type.LABEL_DETECTION},
                    {'type_': vision.Feature.Type.TEXT_DETECTION},
                ]
            })

            # Organize results in an easy-to-understand dictionary
            analysis = {
                'objects': [
                    {
                        'name': obj.name,
                        'confidence': obj.score,
                        'position': self._get_position_description(obj.bounding_poly)
                    }
                    for obj in response.localized_object_annotations
                ],
                'labels': [
                    {
                        'description': label.description,
                        'confidence': label.score
                    }
                    for label in response.label_annotations
                ],
                'text': response.text_annotations[0].description if response.text_annotations else ''
            }

            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analyzing frame {frame_path}: {str(e)}")
            return {
                'objects': [],
                'labels': [],
                'text': '',
                'error': str(e)
            }

    def _get_position_description(self, bounding_poly) -> str:
        """Converts mathematical coordinates into natural position descriptions."""
        vertices = [(vertex.x, vertex.y) for vertex in bounding_poly.normalized_vertices]
        center_x = sum(x for x, _ in vertices) / len(vertices)
        
        if center_x < 0.33:
            return "on the left"
        elif center_x < 0.66:
            return "in the center"
        else:
            return "on the right"

class FrameExtractor:
    def __init__(self, video_path: str, output_dir: str, interval: int = 3):
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.interval = interval
        self.analyzer = FrameAnalyzer()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Open the video
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
            
        # Get basic video information
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.frame_count / self.fps
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Video loaded: {self.duration:.2f} seconds, {self.fps} FPS")

    def process_video(self) -> List[Dict]:
        """Processes the entire video: extracts frames and analyzes them."""
        results = []
        frames_info = self.extract_frames()
        
        for timestamp, frame_path in frames_info:
            try:
                # Analyze each frame
                analysis = self.analyzer.analyze_frame(frame_path)
                
                frame_result = {
                    'timestamp': timestamp,
                    'frame_path': frame_path,
                    'analysis': analysis
                }
                
                results.append(frame_result)
                self.logger.info(f"Processed frame at {timestamp:.2f}s")
                
            except Exception as e:
                self.logger.error(f"Error processing frame at {timestamp:.2f}s: {str(e)}")
        
        # Save all results to a JSON file
        if results:  # Only save if we have results
            output_path = self.output_dir / 'video_analysis.json'
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Analysis results saved to {output_path}")
        
        return results

    def extract_frames(self) -> List[Tuple[float, str]]:
        """Extracts frames from the video at regular intervals."""
        frames_info = []
        frame_interval = int(self.fps * self.interval)
        current_frame = 0
        
        while True:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, current_frame)
            ret, frame = self.cap.read()
            
            if not ret:
                break
                
            timestamp = current_frame / self.fps
            frame_path = self.output_dir / f"frame_{timestamp:.2f}.jpg"
            
            cv2.imwrite(str(frame_path), frame)
            frames_info.append((timestamp, str(frame_path)))
            
            current_frame += frame_interval
            
        self.cap.release()
        return frames_info