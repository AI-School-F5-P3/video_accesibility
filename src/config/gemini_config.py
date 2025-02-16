import os
import logging
from pathlib import Path
import google.generativeai as genai
from dotenv import load_dotenv

def setup_gemini_api():
    """
    Configura la API de Gemini usando credenciales desde un archivo .env
    o variables de entorno. Esta función centraliza toda la configuración
    relacionada con la API.
    
    Returns:
        bool: True si la configuración fue exitosa, False en caso contrario
    """
    logger = logging.getLogger(__name__)
    
    try:
        # Primero, intentamos cargar las variables desde .env si existe
        env_path = Path(__file__).parent.parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
        
        # Intentamos obtener la API key
        api_key = os.getenv('GEMINI_API_KEY')
        
        if not api_key:
            logger.error("No se encontró GEMINI_API_KEY en las variables de entorno o archivo .env")
            return False
            
        # Configuramos Gemini con la API key
        genai.configure(api_key=api_key)
        logger.info("API de Gemini configurada exitosamente")
        
        return True
        
    except Exception as e:
        logger.error(f"Error configurando la API de Gemini: {str(e)}")
        return False

if __name__ == "__main__":
    # Configuración básica de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Probamos la configuración
    if setup_gemini_api():
        print("✅ Configuración exitosa de la API de Gemini")
    else:
        print("❌ Error en la configuración de la API de Gemini")