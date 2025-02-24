from typing import Optional, Dict, Any, List, Union
import logging
import time
import asyncio
from functools import wraps
from tenacity import retry, stop_after_attempt, wait_exponential
import google.generativeai as genai
import numpy as np
import cv2
from PIL import Image
from io import BytesIO
import base64
from pathlib import Path
from ...core.error_handler import ProcessingError, ErrorType, ErrorDetails

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, max_requests: int = 60, time_window: int = 60):
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []

    async def acquire(self):
        now = time.time()
        # Limpiar solicitudes antiguas
        self.requests = [req for req in self.requests if now - req < self.time_window]
        
        if len(self.requests) >= self.max_requests:
            wait_time = self.requests[0] + self.time_window - now
            if wait_time > 0:
                logger.warning(f"Rate limit alcanzado, esperando {wait_time:.2f} segundos")
                await asyncio.sleep(wait_time)
        
        self.requests.append(now)

class GeminiService:
    # Plantillas de prompts optimizadas
    PROMPT_TEMPLATES = {
        'scene_description': """Analiza esta imagen y proporciona una descripción detallada y accesible:
        - Describe la escena principal
        - Menciona personas, objetos y acciones importantes
        - Incluye detalles relevantes para la accesibilidad
        - Usa lenguaje claro y conciso
        - Longitud máxima: 100 palabras""",
        
        'accessibility_analysis': """Evalúa la accesibilidad de esta escena:
        - Contraste y visibilidad
        - Elementos importantes
        - Información contextual necesaria
        - Recomendaciones de audio descripción""",
    }

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.rate_limiter = RateLimiter(
            max_requests=config.get('max_requests_per_minute', 60),
            time_window=60
        )
        self._init_model()

    def _init_model(self):
        try:
            genai.configure(api_key=self.config.get('api_key'))
            self.model = genai.GenerativeModel("gemini-pro-vision")
            self.generation_config = genai.types.GenerationConfig(
                temperature=self.config.get('temperature', 0.7),
                top_p=self.config.get('top_p', 0.8),
                top_k=self.config.get('top_k', 40),
                max_output_tokens=self.config.get('max_tokens', 1024)
            )
        except Exception as e:
            raise ProcessingError("MODEL_INIT_ERROR", str(e))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry_error_callback=lambda retry_state: logger.error(f"Retry {retry_state.attempt_number} failed")
    )
    async def analyze_image(self, image: bytes) -> Dict[str, Any]:
        """Analiza una imagen con retry mechanism y rate limiting"""
        await self.rate_limiter.acquire()
        
        try:
            response = await self.model.generate_content(
                {
                    "image": image,
                    "prompt": self.PROMPT_TEMPLATES['scene_description']
                },
                generation_config=self.generation_config
            )
            return await self._process_response(response)
        except Exception as e:
            logger.error(f"Error en análisis de imagen: {str(e)}")
            raise ProcessingError("ANALYSIS_ERROR", str(e))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def generate_scene_description(
        self, 
        frame_data: np.ndarray,
        language: str = "es"
    ) -> str:
        """Genera descripción de escena con optimizaciones"""
        await self.rate_limiter.acquire()
        
        try:
            # Asegurarse de que el frame está en el formato correcto
            if not isinstance(frame_data, np.ndarray):
                raise ProcessingError(
                    ErrorType.VALIDATION_ERROR,
                    ErrorDetails(
                        component="GeminiService",
                        message="El frame debe ser un array de numpy",
                        code="INVALID_FRAME_FORMAT"
                    )
                )
            
            prompt = self._get_optimized_prompt(frame_data, language)
            response = await self.model.generate_content(prompt)
            return await self._process_response(response)
            
        except Exception as e:
            logger.error(f"Error en generación de descripción: {str(e)}")
            raise ProcessingError(
                ErrorType.AI_SERVICE_ERROR,
                ErrorDetails(
                    component="GeminiService",
                    message=f"Error generando descripción: {str(e)}",
                    code="GENERATION_ERROR"
                )
            )

    def _get_optimized_prompt(self, frame_data: np.ndarray, language: str) -> Dict[str, Any]:
        """Genera un prompt optimizado basado en el contexto"""
        return {
            "image": frame_data,
            "prompt": self.PROMPT_TEMPLATES['scene_description'],
            "context": {
                "language": language,
                "purpose": "accessibility",
                "max_length": 100
            }
        }

    async def _process_response(self, response: Any) -> Dict[str, Any]:
        """Procesa la respuesta del modelo con validación"""
        if not response or not response.text:
            raise ProcessingError("EMPTY_RESPONSE", "El modelo no generó respuesta")
            
        return {
            "text": response.text,
            "confidence": response.candidates[0].likelihood if hasattr(response, 'candidates') else None,
            "safety_ratings": response.safety_ratings if hasattr(response, 'safety_ratings') else None
        }

    async def _process_description(self, response: Any, language: str) -> str:
        """Procesa y valida la descripción generada"""
        if not response or not response.text:
            return "No se pudo generar una descripción válida"
            
        description = response.text.strip()
        if len(description.split()) > 100:
            description = ' '.join(description.split()[:100]) + '...'
            
        return description

    def _format_description(self, raw_text: str, language: str) -> str:
        """Formatea la descripción para que sea más accesible"""
        # Implementación del formato
        return raw_text.strip()

    def _prepare_image(self, frame: np.ndarray) -> Union[Image.Image, bytes]:
        """Prepara la imagen para Gemini"""
        try:
            # Convertir frame de OpenCV a formato PIL
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(frame_rgb)
            
            # Optimizar tamaño si es necesario
            max_size = 1024
            if max(image.size) > max_size:
                image.thumbnail((max_size, max_size))
                
            return image
            
        except Exception as e:
            logger.error(f"Error preparando imagen: {str(e)}")
            raise ProcessingError(
                ErrorType.PROCESSING_ERROR,
                ErrorDetails(
                    component="GeminiService",
                    message=f"Error preparando imagen: {str(e)}",
                    code="IMAGE_PREPARATION_ERROR"
                )
            )