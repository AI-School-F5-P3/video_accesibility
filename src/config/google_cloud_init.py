from google.cloud import vision
from google.cloud import texttospeech
from vertexai import init
from typing import Dict, Any

def initialize_google_cloud(config: Dict[str, Any]) -> None:
    """Inicializa servicios de Google Cloud"""
    init(
        project=config['project_id'],
        location=config['location']
    )