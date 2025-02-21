from typing import Optional
import logging
from vertexai.generative_models import GenerativeModel
from app.config import Settings
import numpy as np

logger = logging.getLogger(__name__)

class GeminiService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = GenerativeModel("gemini-pro-vision")
        self.prompt_template = """
        Describe la siguiente escena de video en detalle, incluyendo:
        1. Elementos principales visibles
        2. Acciones que ocurren
        3. Contexto emocional
        4. Detalles relevantes para accesibilidad
        
        La descripción debe ser clara y concisa, optimizada para personas con 
        discapacidad visual.
        """
        
    async def generate_scene_description(
        self, 
        frame_data: np.ndarray,
        language: str = "es"
    ) -> str:
        """Genera una descripción detallada de la escena"""
        try:
            response = await self.model.predict_async({
                "image": frame_data,
                "text": self.prompt_template
            })
            return self._format_description(response.text, language)
        except Exception as e:
            logger.error(f"Error generating scene description: {str(e)}")
            return "No se pudo generar la descripción de la escena"
            
    def _format_description(self, raw_text: str, language: str) -> str:
        """Formatea la descripción para que sea más accesible"""
        # Implementación del formato
        return raw_text.strip()