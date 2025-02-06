import os
from pathlib import Path
import logging

def setup_credentials():
    """
    Configura las credenciales de Google Cloud y otras variables de entorno necesarias.
    Esta función asegura que las credenciales estén correctamente configuradas antes
    de ejecutar cualquier operación que requiera autenticación.
    """
    logger = logging.getLogger(__name__)
    
    # Obtener la ruta raíz del proyecto
    project_root = Path(__file__).parent.parent.parent
    
    # Ruta al archivo de credenciales
    credentials_path = project_root / "src" / "config" / "credentials" / "google_credentials.json"
    
    if not credentials_path.exists():
        logger.error(f"❌ Archivo de credenciales no encontrado en: {credentials_path}")
        logger.error("Por favor, asegúrate de:")
        logger.error("1. Haber descargado las credenciales de Google Cloud Console")
        logger.error("2. Haber colocado el archivo en la ubicación correcta")
        logger.error("3. Que el archivo se llame 'google_credentials.json'")
        raise FileNotFoundError(f"Credenciales no encontradas en {credentials_path}")
    
    # Configurar la variable de entorno
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = str(credentials_path)
    logger.info(f"✅ Credenciales configuradas correctamente en: {credentials_path}")
    
    return str(credentials_path)

if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Probar la configuración
    try:
        credentials_path = setup_credentials()
        print(f"\nCredenciales configuradas en:\n{credentials_path}")
    except Exception as e:
        print(f"\nError configurando credenciales: {str(e)}")