import os
from google.cloud import storage
from google.auth import default

def verify_gcp_setup():
    """Verifica la configuración de GCP"""
    try:
        credentials, project = default()
        client = storage.Client(project=project)
        buckets = list(client.list_buckets(max_results=1))
        print(f"✅ Credenciales válidas para proyecto: {project}")
        return True
    except Exception as e:
        print(f"❌ Error de configuración GCP: {e}")
        return False

if __name__ == "__main__":
    verify_gcp_setup()