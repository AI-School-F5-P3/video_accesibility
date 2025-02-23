import logging
from pathlib import Path
import sys
from os import path

# Añadir la raíz del proyecto al path de Python
root_dir = path.dirname(path.dirname(path.abspath(__file__)))
sys.path.append(root_dir)

from src.config.env_setup import setup_credentials
from src.core.video_analyzer import FrameExtractor

def main():
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    try:
        # Configurar credenciales antes de cualquier operación
        logger.info("🔑 Configurando credenciales...")
        setup_credentials()

        # Definir rutas usando Path para mejor compatibilidad
        project_root = Path(root_dir)
        video_path = project_root / "data" / "videoplayback.mp4"
        output_dir = project_root / "data" / "extracted_frames"

        logger.info("🎬 Starting frame extraction process...")
        logger.info(f"Video to process: {video_path}")
        logger.info(f"Output directory: {output_dir}")
        
        # Crear extractor y procesar video
        extractor = FrameExtractor(str(video_path), str(output_dir))
        results = extractor.process_video()
        
        # Mostrar resumen del análisis
        logger.info("\n✨ Analysis completed successfully!")
        logger.info(f"📊 Processed frames: {len(results)}")
        logger.info(f"💾 Results saved to: {output_dir}/video_analysis.json")
        
        # Mostrar ejemplo del primer frame analizado
        if results:
            first_frame = results[0]
            logger.info("\n🔍 First frame analysis example:")
            logger.info(f"⏱️ Time: {first_frame['timestamp']:.2f} seconds")
            
            # Mostrar objetos detectados
            logger.info("\n📦 Detected objects:")
            for obj in first_frame['analysis']['objects']:
                logger.info(f"  • {obj['name']} ({obj['confidence']:.1%}) {obj['position']}")
            
            # Mostrar etiquetas generales
            logger.info("\n🏷️ Scene labels:")
            for label in first_frame['analysis']['labels'][:5]:
                logger.info(f"  • {label['description']} ({label['confidence']:.1%})")
            
            # Mostrar texto detectado si existe
            if first_frame['analysis']['text']:
                logger.info(f"\n📝 Detected text: {first_frame['analysis']['text'][:100]}...")

    except Exception as e:
        logger.error(f"❌ Error during analysis: {str(e)}")
        logger.error("Please verify that:")
        logger.error("  1. The video file exists and is accessible")
        logger.error("  2. Google Cloud credentials are properly configured")
        logger.error("  3. You have enough disk space")

if __name__ == "__main__":
    main()