from google.cloud import vision
from google.cloud import texttospeech
from vertexai import init
from typing import Dict, Any
import vertexai
import os
from google.oauth2 import service_account
from pathlib import Path

def initialize_google_cloud(config: Dict[str, Any]) -> None:
    """Inicializa servicios de Google Cloud"""
    init(
        project=config['project_id'],
        location=config['location']
    )

def initialize_vertex_ai():
    """Inicializa Vertex AI con las credenciales correctas"""
    credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
    location = os.getenv('VERTEX_LOCATION', 'us-central1')

    if not all([credentials_path, project_id]):
        raise ValueError(
            "Se requieren las variables de entorno: "
            "GOOGLE_APPLICATION_CREDENTIALS, GOOGLE_CLOUD_PROJECT"
        )

    try:
        credentials = service_account.Credentials.from_service_account_file(
            credentials_path
        )
        
        vertexai.init(
            project=project_id,
            location=location,
            credentials=credentials
        )
    except Exception as e:
        raise RuntimeError(f"Error inicializando Vertex AI: {str(e)}")