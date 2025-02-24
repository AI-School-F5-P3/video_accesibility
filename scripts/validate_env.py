import os
from pathlib import Path
from dotenv import load_dotenv

def validate_env():
    """Valida las variables de entorno requeridas"""
    load_dotenv()
    
    required_vars = [
        'GOOGLE_APPLICATION_CREDENTIALS',
        'GOOGLE_CLOUD_PROJECT',
        'YOUTUBE_API_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables requeridas faltantes: {', '.join(missing_vars)}")
        return False
        
    # Validar rutas
    paths_to_check = [
        os.getenv('TEMP_STORAGE_PATH'),
        os.getenv('OUTPUT_STORAGE_PATH'),
        os.getenv('CACHE_DIR'),
        os.getenv('LOG_PATH')
    ]
    
    for path in paths_to_check:
        Path(path).mkdir(parents=True, exist_ok=True)
        
    return True

if __name__ == "__main__":
    if validate_env():
        print("✅ Configuración válida")
    else:
        print("❌ Errores en la configuración")