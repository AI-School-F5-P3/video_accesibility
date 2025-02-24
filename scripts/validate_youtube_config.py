from app.config.settings import Settings
import logging

logger = logging.getLogger(__name__)

def validate_youtube_config():
    settings = Settings()
    config = settings.get_youtube_config()
    
    required_fields = ['api_key', 'oauth_client_id', 'oauth_client_secret']
    
    for field in required_fields:
        if not config.get(field):
            logger.error(f"Falta configuración requerida: {field}")
            return False
            
    return True