from google.cloud import aiplatform
from vertexai.language_models import TextGenerationModel
from vertexai.vision_models import ImageCaptioningModel
import os
import logging
from typing import Optional, Dict
import numpy as np

class VertexAIService:
    def __init__(self, settings: Optional[Dict] = None):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        self.logger = logging.getLogger(__name__)
        self._initialize_vertex()
        
    def _initialize_vertex(self):
        """Inicializa los servicios de Vertex AI"""
        try:
            aiplatform.init(project=self.project_id, location=self.location)
            self.text_model = TextGenerationModel.from_pretrained("text-bison@001")
            self.vision_model = ImageCaptioningModel.from_pretrained("imagetext@001")
        except Exception as e:
            self.logger.error(f"Error inicializando Vertex AI: {e}")
            raise

    async def generate_description(self, transcript: str) -> str:
        """Genera una descripción del texto usando VertexAI"""
        try:
            prompt = f"Genera una descripción accesible del siguiente texto: {transcript}"
            response = await self.text_model.predict_async(prompt)
            return response.text
        except Exception as e:
            self.logger.error(f"Error generando descripción: {e}")
            raise

    async def analyze_frame(self, frame_data: np.ndarray) -> str:
        """Analiza un frame usando VertexAI Vision"""
        try:
            response = await self.vision_model.predict_async(frame_data)
            return response.caption
        except Exception as e:
            self.logger.error(f"Error analizando frame: {e}")
            raise