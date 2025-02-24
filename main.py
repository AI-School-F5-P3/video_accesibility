import asyncio
import logging
from app.pipeline.video_pipeline import VideoPipeline
from app.config.settings import Settings
from app.models.schemas import ServiceType

# Configurar logging detallado
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    try:
        # Inicializar configuración
        settings = Settings()
        config = settings.get_config()
        logger.debug(f"Configuración cargada: {config}")

        # Verificar que la configuración no esté vacía
        if not config:
            raise ValueError("La configuración está vacía")

        # Inicializar pipeline con configuración por defecto
        pipeline = VideoPipeline(config)
        
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
        
    except Exception as e:
        logger.error(f"Error en el procesamiento: {str(e)}")
        print(f"\nError: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())