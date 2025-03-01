# setup_database.py
import os
import psycopg2
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de la base de datos
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "miresse")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# SQL para crear las tablas
CREATE_TABLES_SQL = """
-- Tabla para almacenar información de los videos
CREATE TABLE IF NOT EXISTS videos (
    id UUID PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    path VARCHAR(255) NOT NULL,
    duration INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed BOOLEAN DEFAULT FALSE
);

-- Tabla para almacenar frames extraídos de los videos
CREATE TABLE IF NOT EXISTS frames (
    id SERIAL PRIMARY KEY,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    frame_number INTEGER NOT NULL,
    timestamp FLOAT NOT NULL,
    path VARCHAR(255) NOT NULL,
    description TEXT,
    UNIQUE(video_id, frame_number)
);

-- Tabla para almacenar subtítulos
CREATE TABLE IF NOT EXISTS subtitles (
    id SERIAL PRIMARY KEY,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    text TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'es'
);

-- Tabla para almacenar audiodescripciones
CREATE TABLE IF NOT EXISTS audio_descriptions (
    id SERIAL PRIMARY KEY,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    frame_id INTEGER REFERENCES frames(id),
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    description TEXT NOT NULL,
    audio_path VARCHAR(255),
    UNIQUE(video_id, start_time)
);

-- Índices para mejorar el rendimiento de las consultas
CREATE INDEX IF NOT EXISTS idx_frames_video_id ON frames(video_id);
CREATE INDEX IF NOT EXISTS idx_subtitles_video_id ON subtitles(video_id);
CREATE INDEX IF NOT EXISTS idx_audio_descriptions_video_id ON audio_descriptions(video_id);
CREATE INDEX IF NOT EXISTS idx_audio_descriptions_frame_id ON audio_descriptions(frame_id);
"""

# Función para obtener todos los elementos asociados a un video
CREATE_FUNCTION_SQL = """
CREATE OR REPLACE FUNCTION get_video_elements(video_uuid UUID)
RETURNS TABLE (
    element_type TEXT,
    element_id INTEGER,
    start_time FLOAT,
    end_time FLOAT,
    content TEXT,
    path VARCHAR
) AS $$
BEGIN
    -- Devolver frames
    RETURN QUERY
    SELECT 'frame', f.id::INTEGER, f.timestamp, f.timestamp, f.description, f.path
    FROM frames f
    WHERE f.video_id = video_uuid
    UNION ALL
    -- Devolver subtítulos
    SELECT 'subtitle', s.id, s.start_time, s.end_time, s.text, NULL
    FROM subtitles s
    WHERE s.video_id = video_uuid
    UNION ALL
    -- Devolver audiodescripciones
    SELECT 'audio_description', ad.id, ad.start_time, ad.end_time, ad.description, ad.audio_path
    FROM audio_descriptions ad
    WHERE ad.video_id = video_uuid
    ORDER BY start_time;
END;
$$ LANGUAGE plpgsql;
"""

def create_database():
    """Crea la base de datos si no existe y configura las tablas."""
    # Primero conectamos a la base de datos PostgreSQL por defecto para crear nuestra base de datos
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname="postgres",
        user=DB_USER,
        password=DB_PASSWORD
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Verificar si la base de datos ya existe
    cursor.execute(f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
    exists = cursor.fetchone()
    
    if not exists:
        try:
            cursor.execute(f"CREATE DATABASE {DB_NAME}")
            print(f"Base de datos '{DB_NAME}' creada correctamente.")
        except Exception as e:
            print(f"Error al crear la base de datos: {e}")
            return False
    else:
        print(f"La base de datos '{DB_NAME}' ya existe.")
    
    cursor.close()
    conn.close()
    
    # Ahora conectamos a nuestra base de datos recién creada para crear las tablas
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Crear tablas
        cursor.execute(CREATE_TABLES_SQL)
        
        # Crear función
        cursor.execute(CREATE_FUNCTION_SQL)
        
        print("Tablas y funciones creadas correctamente.")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error al crear tablas: {e}")
        return False

if __name__ == "__main__":
    create_database()