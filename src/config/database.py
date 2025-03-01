
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)

# Example usage
logging.info("This is an info message")
logging.error("This is an error message")


# Configuración de la base de datos
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "miresse")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

def get_connection():
    """Establece conexión con la base de datos PostgreSQL."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Error al conectar a la base de datos: {e}")
        raise

def check_connection():
    """
    Verifica si la conexión a la base de datos está funcionando.
    
    Returns:
        bool: True si la conexión es exitosa, False en caso contrario
    """
    try:
        conn = get_connection()
        conn.close()
        return True
    except Exception as e:
        logging.error(f"Error al verificar la conexión a la base de datos: {e}")
        return False

def execute_query(query, params=None, fetch=True):
    """Ejecuta una consulta en la base de datos."""
    conn = get_connection()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params or ())
            conn.commit()
            if fetch:
                return cursor.fetchall()
            return None
    except Exception as e:
        conn.rollback()
        print(f"Error al ejecutar la consulta: {e}")
        raise
    finally:
        conn.close()

