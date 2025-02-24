from typing import Dict, Any, Optional, List
from pathlib import Path
import logging
import asyncio
import numpy as np  # Añadida esta importación
from vertexai.generative_models import (
    GenerativeModel,
    GenerationConfig,
    GenerationResponse
)
from app.config.google_cloud_init import initialize_vertex_ai
from app.models.schemas import AIResponse, GenerationParameters

logger = logging.getLogger(__name__)

class AIService:
    """Servicio para interactuar con modelos de IA"""
    
    def __init__(self, settings: Dict[str, Any]):
        """
        Inicializa el servicio de IA
        
        Args:
            settings: Configuración del servicio
        """
        self.settings = settings
        try:
            initialize_vertex_ai()
            self.model = GenerativeModel("gemini-pro-vision")
            self.generation_config = GenerationConfig(
                temperature=0.7,
                top_p=0.8,
                top_k=40,
                max_output_tokens=1024
            )
            logger.info("Servicio AI inicializado correctamente")
        except Exception as e:
            logger.error(f"Error inicializando AI Service: {str(e)}")
            raise RuntimeError(f"No se pudo inicializar AI Service: {str(e)}")

    async def generate_description(
        self,
        image_data: bytes,
        context: str,
        parameters: Optional[GenerationParameters] = None
    ) -> AIResponse:
        """
        Genera descripción para una imagen
        
        Args:
            image_data (bytes): Datos binarios de la imagen
            context (str): Contexto para la generación
            parameters (Optional[GenerationParameters]): Parámetros adicionales
            
        Returns:
            AIResponse: Respuesta del modelo
            
        Raises:
            RuntimeError: Si hay error en la generación
        """
        try:
            response = await self.model.generate_content(
                [image_data, context],
                generation_config=self._get_generation_config(parameters)
            )
            return AIResponse(
                text=response.text,
                confidence=self._get_confidence(response),
                metadata=self._get_metadata(response)
            )
        except Exception as e:
            logger.error(f"Error en generación: {str(e)}")
            raise RuntimeError(f"Error generando descripción: {str(e)}")

    def _get_generation_config(
        self,
        parameters: Optional[GenerationParameters]
    ) -> GenerationConfig:
        """Obtiene configuración de generación"""
        if not parameters:
            return self.model.generation_config
        return GenerationConfig(
            temperature=parameters.temperature,
            top_p=parameters.top_p,
            top_k=parameters.top_k,
            max_output_tokens=parameters.max_tokens
        )

    def _get_confidence(self, response: GenerationResponse) -> float:
        """Extrae nivel de confianza de la respuesta"""
        try:
            return response.candidates[0].safety_ratings[0].probability
        except (IndexError, AttributeError):
            return 0.0

    def _get_metadata(self, response: GenerationResponse) -> Dict[str, Any]:
        """Extrae metadata de la respuesta"""
        return {
            "model": self.model.model_name,
            "tokens": len(response.text.split()),
            "finish_reason": getattr(response, "finish_reason", None)
        }

    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """
        Analiza contenido textual
        
        Args:
            content: Texto a analizar
            
        Returns:
            Dict[str, Any]: Resultado del análisis
        """
        try:
            prompt = f"Analiza el siguiente contenido y extrae información clave: {content}"
            response = await self.model.generate_content(prompt)
            return {
                "analysis": response.text,
                "confidence": response.candidates[0].safety_ratings[0].probability
            }
        except Exception as e:
            logger.error(f"Error analizando contenido: {str(e)}")
            raise RuntimeError(f"Error en análisis de contenido: {str(e)}")

    def _initialize_models(self):
        """Inicializa los modelos de IA necesarios"""
        try:
            self.vision_model = self.model.get_vision_model()
            logger.info("AI models initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing AI models: {str(e)}")
            raise

    async def analyze_emotion(self, frame_data: np.ndarray) -> str:
        """
        Analiza la emoción en un frame de video
        
        Args:
            frame_data: Frame del video como array numpy
            
        Returns:
            str: Emoción detectada
        """
        try:
            # Implementación del análisis de emoción
            return "neutral"
        except Exception as e:
            logger.error(f"Error en análisis de emoción: {str(e)}")
            return "unknown"

    async def analyze_scene_context(self, frame_data: np.ndarray) -> Dict[str, Any]:
        """Analiza el contexto completo de una escena"""
        try:
            response = await self.vision_model.predict_async({
                "image": frame_data,
                "task": "scene_understanding"
            })
            return self._parse_scene_context(response.text)
        except Exception as e:
            logger.error(f"Error in scene context analysis: {str(e)}")
            return {}

    def _parse_scene_context(self, raw_response: str) -> Dict[str, Any]:
        """Parsea la respuesta del modelo a un formato estructurado"""
        # Implementación del parsing
        return {}