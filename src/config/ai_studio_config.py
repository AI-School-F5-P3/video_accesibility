# src/config/ai_studio_config.py
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, Any

class AIStudioConfig:
    """Configuración para Vertex AI Studio."""
    
    def __init__(self):
        self._config = {
            "model_name": "gemini-pro",
            "generation_config": {
                "temperature": 0.7,
                "max_output_tokens": 1024,
                "top_p": 0.8,
                "top_k": 40
            },
            "processing_config": {
                "enable_speaker_diarization": True,
                "min_silence_duration": 0.5,
                "scene_threshold": 0.3
            }
        }

    def get_config(self) -> Dict[str, Any]:
        """Retorna la configuración actual."""
        return self._config

    def update_config(self, new_config: Dict[str, Any]) -> None:
        """Actualiza la configuración."""
        self._config.update(new_config)

def initialize_ai_studio():
    """
    Initializes connection to Google AI Studio with improved path handling
    and detailed error messages for troubleshooting.
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    
    # Load environment variables
    env_path = project_root / '.env'
    if not env_path.exists():
        raise FileNotFoundError(
            f".env file not found at {env_path}. "
            "Please create it with your Google Cloud credentials configuration."
        )
    
    load_dotenv(env_path)
    
    # Get credentials path
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    if not credentials_path:
        raise ValueError(
            "GOOGLE_APPLICATION_CREDENTIALS not found in .env file. "
            "Please add it with the path to your credentials JSON file."
        )
    
    # Handle relative paths
    if credentials_path.startswith('./'):
        credentials_path = project_root / credentials_path[2:]
    
    # Print debug information
    print(f"Looking for credentials at: {credentials_path}")
    
    if not Path(credentials_path).exists():
        raise FileNotFoundError(
            f"Credentials file not found at: {credentials_path}\n"
            "Please check that:\n"
            "1. The path in .env matches your credentials filename exactly\n"
            "2. The .json extension is included in the path\n"
            "3. The file exists in your credentials directory"
        )
    
    try:
        import vertexai
        from vertexai.generative_models import GenerativeModel
        
        project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        location = os.getenv('VERTEX_LOCATION', 'us-central1')
        
        vertexai.init(project=project_id, location=location)
        return GenerativeModel("gemini-pro-vision")
        
    except Exception as e:
        raise ConnectionError(
            f"Failed to initialize AI Studio: {str(e)}\n"
            "Please verify your Google Cloud project settings and permissions."
        )