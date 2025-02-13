import argparse
import sys
import logging
from typing import Dict, Any
from pathlib import Path
from .video_pipeline import VideoPipeline
from src.config.ai_studio_config import AIStudioConfig
from vertexai import init
from vertexai.generative_models import GenerativeModel

def setup_logging(verbose: bool):
    """Configura el nivel de logging basado en el modo verbose"""
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

class PipelineRunner:
    """Manages the execution of the video accessibility pipeline."""
    
    VALID_REGIONS = {
        'europe-west4',
        'europe-west1',
        'europe-west2',
        # ... otras regiones válidas
    }
    
    def __init__(self, 
                 project_id: str = "videoaccesibility",
                 location: str = "europe-west4"):
        # Validar región
        if location not in self.VALID_REGIONS:
            raise ValueError(f"Región no válida. Por favor, use una de: {self.VALID_REGIONS}")
        
        # Initialize Vertex AI
        init(project=project_id, location=location)
        
        # Load configuration
        self.config = AIStudioConfig().get_config()
        self.model = GenerativeModel(
            model_name=self.config["model_name"],
            generation_config=self.config["generation_config"]
        )
        
    def run(self, 
            video_path: str, 
            output_dir: str = "output", 
            add_subtitles: bool = True) -> Dict[str, Any]:
        """Execute the complete video processing pipeline."""
        pipeline = VideoPipeline(
            model=self.model,
            output_dir=output_dir,
            add_subtitles=add_subtitles,
            config=self.config
        )
        
        return pipeline.process_video(video_path)

def main():
    parser = argparse.ArgumentParser(description='Procesa videos para hacerlos accesibles')
    parser.add_argument("video_path", help="Ruta al archivo de video")
    parser.add_argument("--output-dir", default="output/processed", help="Directorio de salida")
    parser.add_argument("--add-subtitles", action="store_true", help="Añadir subtítulos")
    parser.add_argument(
        "--project-id", 
        default="videoaccesibility",  # Usar tu proyecto por defecto
        help="ID del proyecto de Google Cloud"
    )
    parser.add_argument(
        "--location", 
        default="europe-west4",     # Cambiado de europe-west4-a a europe-west4
        help="Ubicación de Google Cloud (región)"
    )
    parser.add_argument("--verbose", action="store_true", help="Mostrar logs detallados")
    
    args = parser.parse_args()
    
    # Configurar logging
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        runner = PipelineRunner(
            project_id=args.project_id,
            location=args.location
        )
        result = runner.run(
            args.video_path,
            output_dir=args.output_dir,
            add_subtitles=args.add_subtitles
        )
        logger.info(f"✅ Video procesado exitosamente: {result}")
        
    except Exception as e:
        logger.error(f"❌ Error processing video: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()