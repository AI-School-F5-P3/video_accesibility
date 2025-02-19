import os
from dotenv import load_dotenv
import logging
from google.cloud import storage
from google.oauth2 import service_account
import vertexai

load_dotenv()

class GoogleCloudInitializer:
    @staticmethod
    def initialize():
        """Initialize Google Cloud authentication and Vertex AI"""
        try:
            # Load credentials from service account JSON
            credentials_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                                         'service-account.json')
            
            if not os.path.exists(credentials_path):
                raise FileNotFoundError(f"Service account JSON not found at {credentials_path}")
            
            # Set Google Cloud credentials environment variable
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
            
            # Load credentials
            credentials = service_account.Credentials.from_service_account_file(
                credentials_path,
                scopes=['https://www.googleapis.com/auth/cloud-platform']
            )
            
            # Get project ID from .env
            project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
            if not project_id:
                raise ValueError("GOOGLE_CLOUD_PROJECT environment variable not set in .env")
            
            # Initialize Vertex AI
            vertexai.init(
                project=project_id,
                location="europe-west1",
                credentials=credentials
            )
            
            logging.info("Successfully initialized Google Cloud and Vertex AI")
            return credentials
            
        except Exception as e:
            logging.error(f"Failed to initialize Google Cloud: {str(e)}")
            raise
