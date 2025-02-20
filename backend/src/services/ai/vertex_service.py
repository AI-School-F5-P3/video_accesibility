from google.cloud import aiplatform
from vertexai.language_models import TextGenerationModel
import os
import logging

class VertexAIService:
    def __init__(self):
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.location = os.getenv('GOOGLE_CLOUD_LOCATION', 'us-central1')
        self.logger = logging.getLogger(__name__)
        self._initialize_vertex()

    def _initialize_vertex(self):
        aiplatform.init(project=self.project_id, location=self.location)
        self.model = TextGenerationModel.from_pretrained("text-bison@001")

    async def generate_description(self, transcript: str) -> str:
        try:
            response = self.model.predict(
                f"Genera una descripción accesible del siguiente texto: {transcript}",
                max_output_tokens=1024,
                temperature=0.2
            )
            return response.text
        except Exception as e:
            self.logger.error(f"Error en Vertex AI: {e}")
            raise