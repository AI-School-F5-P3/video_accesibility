import cv2
import os
import google.generativeai as genai
from PIL import Image
import json
from pathlib import Path
import logging
from ..utils.formatters import format_timecode

class TextProcessor:
    def __init__(self, settings):
        self.settings = settings
        genai.configure(api_key=settings.GOOGLE_AI_STUDIO_API_KEY)
        self.vision_model = genai.GenerativeModel('gemini-1.5-flash')
        
    def generate_description(self, image: Image.Image, max_duration_ms: int) -> str:
        try:
            if image is None:
                return ""

            prompt = """Actúa como un experto en audiodescripción siguiendo la norma UNE 153020. 
                Describe la escena siguiente en lenguaje claro y fluido considerando estas pautas:
                - Usa lenguaje sencillo, fluido y directo
                - Describe solo lo que se ve, sin interpretar
                - Utiliza presente de indicativo
                - Sé preciso en la descripción
                - No uses "se ve", "aparece" o "podemos ver"
                - Comienza con "En esta escena"
                - Prioriza: Qué, Quién, Cómo, Dónde
                - Máximo 2 frases
                - Evita redundancias
                - No uses metáforas"""

            response = self.vision_model.generate_content([prompt, image])
            
            if response and response.text:
                description = response.text.strip()
                words = description.split()
                max_words = int((max_duration_ms / 1000) * 3)

                if len(words) > max_words:
                    description = " ".join(words[:max_words]) + "."

                return description

            return ""

        except Exception as e:
            logging.error(f"Error generating description: {str(e)}")
            return ""
            
    def save_script(self, descriptions: list) -> Path:
        try:
            script = [{
                'timestamp': desc['start_time'] / 1000,  # Convert to seconds
                'duration': (desc['end_time'] - desc['start_time']) / 1000,
                'text': desc['description']
            } for desc in descriptions]
            
            output_path = self.settings.TRANSCRIPTS_DIR / "script.json"
            self.save_formatted_script(script, output_path)
            return output_path
            
        except Exception as e:
            logging.error(f"Error saving script: {str(e)}")
            raise
            
    def create_script(self, video_path: Path) -> list:
        try:
            # Get video duration and fps
            cap = cv2.VideoCapture(str(video_path))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps
            cap.release()

            # Create intervals every 5 seconds
            interval = 5  # seconds
            timestamps = list(range(0, int(duration), interval))
            script = []

            for timestamp in timestamps:
                # Extract frame at timestamp
                frame = self.video_analyzer.extract_frame(video_path, timestamp * 1000)
                
                if frame:
                    # Generate description for the frame
                    description = self.generate_description(frame, interval * 1000)
                    
                    if description:
                        timecode = format_timecode(timestamp)
                        script_entry = {
                            "timecode": timecode,
                            "text": description
                        }
                        script.append(script_entry)

            output_path = self.settings.TRANSCRIPTS_DIR / f"{video_path.stem}_script.json"
            self.save_formatted_script(script, output_path)
            return script

        except Exception as e:
            logging.error(f"Error creating script: {str(e)}")
            raise
            
    def save_formatted_script(self, script: list, output_path: Path):
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(script, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logging.error(f"Error saving formatted script: {str(e)}")
            raise