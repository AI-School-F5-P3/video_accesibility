import asyncio
import logging
from app.config.settings import Settings
from app.pipeline.video_pipeline import VideoPipeline
from app.core.error_handler import ProcessingError
from app.models.schemas import ServiceType

# Configurar logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Cargar configuración
        settings = Settings()
        config = settings.get_config()
        logger.debug(f"Configuración cargada: {config}")
        
        # Inicializar pipeline
        pipeline = VideoPipeline(config)
        
        # Verificar que la configuración no esté vacía
        if not config:
            raise ValueError("La configuración está vacía")

        # Solicitar URL y tipo de servicio
        print("\n=== Video Accessibility Service ===")
        youtube_url = input("\nIngresa la URL del video de YouTube: ")
        
        print("\nSelecciona el tipo de servicio:")
        print("1. Audiodescripción")
        print("2. Subtitulado")
        service_choice = input("Ingresa el número (1 o 2): ")
        
        service_type = (
            ServiceType.AUDIODESCRIPCION if service_choice == "1" 
            else ServiceType.SUBTITULADO
        )

        # Procesar video
        result = await pipeline.process_url(youtube_url, service_type)
        
    except ProcessingError as e:
        logger.error(f"Error en el procesamiento: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\nError: {str(e)}")