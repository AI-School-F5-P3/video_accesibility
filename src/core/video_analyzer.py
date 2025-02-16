import cv2
import numpy as np
from pathlib import Path
import logging
from typing import List, Tuple, Dict
import google.generativeai as genai
import json
from PIL import Image
import os
from src.config.api_config import setup_gemini_api

class FrameAnalyzer:
    """
    Analiza frames de video usando el modelo Gemini Vision.
    Esta clase actúa como nuestro 'experto visual' que puede entender y describir
    lo que está sucediendo en cada frame del video.
    """
    def __init__(self):
        
        api_key = os.getenv('GEMINI_API_KEY')
        if not api_key:
            self.logger.warning("No se encontró GEMINI_API_KEY en las variables de entorno")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-pro-vision')
        self.logger = logging.getLogger(__name__)

    def analyze_frame(self, frame_path: str) -> Dict:
        """
        Analiza un frame individual usando Gemini Vision.
        
        Args:
            frame_path: Ruta al archivo de imagen del frame
            
        Returns:
            Dict con el análisis estructurado del frame
        """
        try:
            # Cargamos la imagen usando PIL para compatibilidad con Gemini
            image = Image.open(frame_path)
            
            # Creamos un prompt específico para audiodescripción
            prompt = """
            Analiza este frame de video y proporciona una descripción detallada 
            pensada para audiodescripción. Enfócate en:
            1. Objetos y personas principales en la escena
            2. Acciones o actividades que están ocurriendo
            3. Ambiente y entorno
            4. Cualquier texto visible
            5. Colores, iluminación y atmósfera notable
            
            Estructura la respuesta como un JSON con estos campos:
            - objects: lista de objetos principales
            - actions: lista de actividades
            - setting: descripción del entorno
            - text: texto visible
            - atmosphere: descripción del ambiente/iluminación
            """

            # Obtenemos la respuesta de Gemini
            response = self.model.generate_content([prompt, image])
            
            try:
                # Intentamos parsear la respuesta como datos estructurados
                analysis = self._parse_gemini_response(response.text)
            except Exception as e:
                self.logger.warning(f"No se pudo parsear la respuesta estructurada: {str(e)}")
                # Si falla el parseo, usamos la respuesta en bruto
                analysis = {
                    'raw_description': response.text,
                    'objects': [],
                    'actions': [],
                    'setting': '',
                    'text': '',
                    'atmosphere': ''
                }

            return analysis
            
        except Exception as e:
            self.logger.error(f"Error analizando frame {frame_path}: {str(e)}")
            return {
                'objects': [],
                'labels': [],
                'text': '',
                'error': str(e)
            }

    def _parse_gemini_response(self, response_text: str) -> Dict:
        """
        Convierte la respuesta en lenguaje natural de Gemini en datos estructurados.
        
        Args:
            response_text: Texto de respuesta de Gemini
            
        Returns:
            Dict con la información estructurada
        """
        parsed = {
            'objects': [],
            'actions': [],
            'setting': '',
            'text': '',
            'atmosphere': ''
        }
        
        # Procesamos la respuesta línea por línea
        lines = response_text.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Identificamos las secciones por sus encabezados
            if 'objects:' in line.lower():
                current_section = 'objects'
            elif 'actions:' in line.lower():
                current_section = 'actions'
            elif 'setting:' in line.lower():
                current_section = 'setting'
            elif 'text:' in line.lower():
                current_section = 'text'
            elif 'atmosphere:' in line.lower():
                current_section = 'atmosphere'
            elif current_section:
                # Añadimos el contenido a la sección correspondiente
                if current_section in ['objects', 'actions']:
                    items = line.strip('- ').split(',')
                    parsed[current_section].extend([item.strip() for item in items])
                else:
                    parsed[current_section] += line.strip('- ')

        return parsed

class FrameExtractor:
    """
    Extrae frames de un video y coordina su análisis.
    Esta clase maneja todo el proceso de extraer frames del video
    y organizarlos para su análisis.
    """
    def __init__(self, video_path: str, output_dir: str, interval: int = 3):
        """
        Inicializa el extractor de frames.
        
        Args:
            video_path: Ruta al archivo de video
            output_dir: Directorio donde guardar los frames
            interval: Intervalo en segundos entre frames
        """
        self.video_path = video_path
        self.output_dir = Path(output_dir)
        self.interval = interval
        self.analyzer = FrameAnalyzer()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Inicializamos la captura de video
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            raise ValueError(f"No se pudo abrir el video: {video_path}")
            
        # Obtenemos las propiedades del video
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
        self.frame_count = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.duration = self.frame_count / self.fps
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Video cargado: {self.duration:.2f} segundos, {self.fps} FPS")

    def process_video(self) -> List[Dict]:
        """
        Procesa el video completo: extrae frames y los analiza.
        
        Returns:
            Lista de diccionarios con los resultados del análisis
        """
        results = []
        frames_info = self.extract_frames()
        
        for timestamp, frame_path in frames_info:
            try:
                # Analizamos cada frame
                analysis = self.analyzer.analyze_frame(frame_path)
                
                frame_result = {
                    'timestamp': timestamp,
                    'frame_path': frame_path,
                    'analysis': analysis
                }
                
                results.append(frame_result)
                self.logger.info(f"Frame procesado en {timestamp:.2f}s")
                
            except Exception as e:
                self.logger.error(f"Error procesando frame en {timestamp:.2f}s: {str(e)}")
        
        # Guardamos los resultados en un archivo JSON
        if results:
            output_path = self.output_dir / 'video_analysis.json'
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                self.logger.info(f"Resultados guardados en {output_path}")
        
        return results

    def extract_frames(self) -> List[Tuple[float, str]]:
        """
        Extrae frames del video a intervalos regulares.
        
        Returns:
            Lista de tuplas (timestamp, ruta_del_frame)
        """
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

if __name__ == "__main__":
    # Configuración de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Ejemplo de uso
    video_path = "ruta/a/tu/video.mp4"
    output_dir = "ruta/para/guardar/frames"
    
    try:
        extractor = FrameExtractor(video_path, output_dir)
        results = extractor.process_video()
        print(f"Procesados {len(results)} frames exitosamente")
    except Exception as e:
        print(f"Error durante el procesamiento: {str(e)}")