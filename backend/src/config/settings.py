from pathlib import Path
from dotenv import load_dotenv
import os

# Cargar .env desde la raíz del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / '.env'
load_dotenv(ENV_PATH)

# Configuraciones generales
DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Rutas
TEMP_DIR = BASE_DIR / os.getenv('TEMP_STORAGE_PATH', 'temp').lstrip('./')
OUTPUT_DIR = BASE_DIR / os.getenv('OUTPUT_STORAGE_PATH', 'output').lstrip('./')

# Crear directorios necesarios
TEMP_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)