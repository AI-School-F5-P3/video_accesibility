from vertexai.generative_models import GenerativeModel
import os
import logging

class GeminiService:
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        self.logger = logging.getLogger(__name__)
        self._initialize_gemini()

    def _initialize_gemini(self):
        self.model = GenerativeModel("gemini-pro")

    async def analyze_content(self, video_path: str, transcript: str) -> dict:
        try:
            prompt = f"""
            Analiza el siguiente contenido y genera:
            1. Una descripción detallada del video
            2. Palabras clave relevantes
            3. Resumen accesible
            
            Transcripción: {transcript}
            """
            
            response = self.model.generate_content(prompt)
            return {
                "description": response.text,
                "keywords": self._extract_keywords(response.text),
                "summary": self._extract_summary(response.text)
            }
        except Exception as e:
            self.logger.error(f"Error en Gemini: {e}")
            raise