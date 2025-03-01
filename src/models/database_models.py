# src/models/database_models.py
import uuid
from datetime import datetime
from src.config.database import execute_query

class Video:
    @staticmethod
    def create(filename, path, duration=None):
        """Crea un nuevo registro de video en la base de datos."""
        video_id = str(uuid.uuid4())
        query = """
        INSERT INTO videos (id, filename, path, duration, created_at)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """
        result = execute_query(query, (video_id, filename, path, duration, datetime.now()))
        return result[0]['id'] if result else None

    @staticmethod
    def get_by_id(video_id):
        """Obtiene un video por su ID."""
        query = "SELECT * FROM videos WHERE id = %s;"
        result = execute_query(query, (video_id,))
        return result[0] if result else None

    @staticmethod
    def update_processed_status(video_id, processed=True):
        """Actualiza el estado de procesamiento de un video."""
        query = "UPDATE videos SET processed = %s WHERE id = %s;"
        execute_query(query, (processed, video_id), False)
    @staticmethod
    def get_all():
  
        query = "SELECT * FROM videos ORDER BY created_at DESC;"
        return execute_query(query)

class Frame:
    @staticmethod
    def create(video_id, frame_number, timestamp, path, description=None):
        """Crea un nuevo registro de frame en la base de datos."""
        query = """
        INSERT INTO frames (video_id, frame_number, timestamp, path, description)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """
        result = execute_query(query, (video_id, frame_number, timestamp, path, description))
        return result[0]['id'] if result else None

    @staticmethod
    def get_by_video_id(video_id):
        """Obtiene todos los frames de un video."""
        query = "SELECT * FROM frames WHERE video_id = %s ORDER BY frame_number;"
        return execute_query(query, (video_id,))

    @staticmethod
    def update_description(frame_id, description):
        """Actualiza la descripción de un frame."""
        query = "UPDATE frames SET description = %s WHERE id = %s;"
        execute_query(query, (description, frame_id), False)

class Subtitle:
    @staticmethod
    def create(video_id, start_time, end_time, text, language='es'):
        """Crea un nuevo registro de subtítulo en la base de datos."""
        query = """
        INSERT INTO subtitles (video_id, start_time, end_time, text, language)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """
        result = execute_query(query, (video_id, start_time, end_time, text, language))
        return result[0]['id'] if result else None

    @staticmethod
    def get_by_video_id(video_id):
        """Obtiene todos los subtítulos de un video."""
        query = "SELECT * FROM subtitles WHERE video_id = %s ORDER BY start_time;"
        return execute_query(query, (video_id,))

    @staticmethod
    def bulk_insert(video_id, subtitles, language='es'):
        """Inserta múltiples subtítulos a la vez."""
        conn = get_connection()
        try:
            with conn.cursor() as cursor:
                for subtitle in subtitles:
                    cursor.execute(
                        "INSERT INTO subtitles (video_id, start_time, end_time, text, language) VALUES (%s, %s, %s, %s, %s)",
                        (video_id, subtitle['start_time'], subtitle['end_time'], subtitle['text'], language)
                    )
                conn.commit()
        except Exception as e:
            conn.rollback()
            raise
        finally:
            conn.close()

class AudioDescription:
    @staticmethod
    def create(video_id, start_time, end_time, description, audio_path=None, frame_id=None):
        """Crea un nuevo registro de audiodescripción en la base de datos."""
        query = """
        INSERT INTO audio_descriptions (video_id, frame_id, start_time, end_time, description, audio_path)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id;
        """
        result = execute_query(query, (video_id, frame_id, start_time, end_time, description, audio_path))
        return result[0]['id'] if result else None

    @staticmethod
    def get_by_video_id(video_id):
        """Obtiene todas las audiodescripciones de un video."""
        query = "SELECT * FROM audio_descriptions WHERE video_id = %s ORDER BY start_time;"
        return execute_query(query, (video_id,))

    @staticmethod
    def update_audio_path(desc_id, audio_path):
        """Actualiza la ruta del archivo de audio de una audiodescripción."""
        query = "UPDATE audio_descriptions SET audio_path = %s WHERE id = %s;"
        execute_query(query, (audio_path, desc_id), False)
    
    