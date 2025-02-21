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
        """Genera una descripción accesible del texto"""
        try:
            prompt = (
                "Genera una descripción accesible y detallada del siguiente texto, "
                "enfocándote en claridad y contexto para personas con discapacidad visual:\n\n"
                f"{transcript}"
            )
            
            response = await self.text_model.predict_async(
                prompt,
                max_output_tokens=1024,
                temperature=0.2,
                top_p=0.8,
                top_k=40
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Error en Vertex AI text generation: {e}")
            raise

    async def analyze_frame(self, frame: np.ndarray) -> str:
        """Analiza un frame del video usando el modelo de visión"""
        try:
            response = await self.vision_model.predict_async(
                image=frame,
                number_of_results=1,
                language="es"
            )
            return response.caption
        except Exception as e:
            self.logger.error(f"Error en Vertex AI frame analysis: {e}")
            raise