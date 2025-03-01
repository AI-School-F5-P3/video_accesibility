import os
import sys
import uuid
import logging
from pathlib import Path

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Añadir el directorio raíz al path para poder importar los módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Importar los modelos
from src.models.database_models import Video, Frame, Subtitle, AudioDescription
from src.config.database import check_connection

def test_database_connection():
    """Prueba la conexión a la base de datos."""
    if check_connection():
        logging.info("✅ Conexión a la base de datos exitosa")
        return True
    else:
        logging.error("❌ Error al conectar a la base de datos")
        return False

def test_video_crud():
    """Prueba operaciones CRUD con la tabla videos."""
    # Generar un ID único para el video de prueba
    test_video_id = str(uuid.uuid4())
    
    # Insertar un video de prueba
    try:
        Video.create(
            filename="test_video.mp4",
            path=f"/data/raw/{test_video_id}/test_video.mp4",
            duration=120
        )
        logging.info(f"✅ Video creado con ID: {test_video_id}")
        
        # Recuperar el video
        video = Video.get_by_id(test_video_id)
        if video and video['id'] == test_video_id:
            logging.info(f"✅ Video recuperado correctamente: {video['filename']}")
        else:
            logging.error("❌ Error al recuperar el video")
            return False
        
        # Actualizar el estado del video
        Video.update_processed_status(test_video_id, True)
        logging.info("✅ Estado del video actualizado correctamente")
        
        return True
    except Exception as e:
        logging.error(f"❌ Error en la prueba de video: {e}")
        return False

def test_frame_crud(video_id):
    """Prueba operaciones CRUD con la tabla frames."""
    try:
        # Insertar un frame de prueba
        frame_id = Frame.create(
            video_id=video_id,
            frame_number=1,
            timestamp=10.5,
            path=f"/data/processed/{video_id}/frame_1.jpg",
            description="Frame de prueba"
        )
        logging.info(f"✅ Frame creado con ID: {frame_id}")
        
        # Recuperar frames del video
        frames = Frame.get_by_video_id(video_id)
        if frames and len(frames) > 0:
            logging.info(f"✅ Frames recuperados correctamente: {len(frames)}")
        else:
            logging.error("❌ Error al recuperar frames")
            return False
        
        return True
    except Exception as e:
        logging.error(f"❌ Error en la prueba de frames: {e}")
        return False

def test_subtitle_crud(video_id):
    """Prueba operaciones CRUD con la tabla subtitles."""
    try:
        # Insertar un subtítulo de prueba
        subtitle_id = Subtitle.create(
            video_id=video_id,
            start_time=5.0,
            end_time=10.0,
            text="Este es un subtítulo de prueba"
        )
        logging.info(f"✅ Subtítulo creado con ID: {subtitle_id}")
        
        # Recuperar subtítulos del video
        subtitles = Subtitle.get_by_video_id(video_id)
        if subtitles and len(subtitles) > 0:
            logging.info(f"✅ Subtítulos recuperados correctamente: {len(subtitles)}")
        else:
            logging.error("❌ Error al recuperar subtítulos")
            return False
        
        return True
    except Exception as e:
        logging.error(f"❌ Error en la prueba de subtítulos: {e}")
        return False

def test_audio_description_crud(video_id):
    """Prueba operaciones CRUD con la tabla audio_descriptions."""
    try:
        # Insertar una audiodescripción de prueba
        audiodesc_id = AudioDescription.create(
            video_id=video_id,
            start_time=15.0,
            end_time=20.0,
            description="Esta es una audiodescripción de prueba",
            audio_path=f"/data/audio/{video_id}_desc_0.mp3"
        )
        logging.info(f"✅ Audiodescripción creada con ID: {audiodesc_id}")
        
        # Recuperar audiodescripciones del video
        audiodescs = AudioDescription.get_by_video_id(video_id)
        if audiodescs and len(audiodescs) > 0:
            logging.info(f"✅ Audiodescripciones recuperadas correctamente: {len(audiodescs)}")
        else:
            logging.error("❌ Error al recuperar audiodescripciones")
            return False
        
        return True
    except Exception as e:
        logging.error(f"❌ Error en la prueba de audiodescripciones: {e}")
        return False

def run_all_tests():
    """Ejecuta todas las pruebas."""
    logging.info("Iniciando pruebas de la base de datos...")
    
    # Probar conexión
    if not test_database_connection():
        return False
    
    # Crear un video para las pruebas
    test_video_id = str(uuid.uuid4())
    try:
        video_id = Video.create(
            filename="video_prueba_completa.mp4",
            path=f"/data/raw/{test_video_id}/video_prueba_completa.mp4",
            duration=300
        )
        logging.info(f"✅ Video de prueba creado con ID: {video_id}")
        
        # Probar operaciones con frames
        if not test_frame_crud(video_id):
            return False
        
        # Probar operaciones con subtítulos
        if not test_subtitle_crud(video_id):
            return False
        
        # Probar operaciones con audiodescripciones
        if not test_audio_description_crud(video_id):
            return False
        
        logging.info("✅ Todas las pruebas completadas exitosamente")
        return True
    except Exception as e:
        logging.error(f"❌ Error durante las pruebas: {e}")
        return False

if __name__ == "__main__":
    run_all_tests()