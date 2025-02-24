import os
import json
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

def verify_credentials_file():
    """Verifica el archivo de credenciales"""
    cred_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
    
    if not os.path.exists(cred_path):
        print(f"❌ Archivo no encontrado: {cred_path}")
        return False
        
    try:
        with open(cred_path, 'r') as f:
            cred_json = json.load(f)
            
        required_fields = ['type', 'project_id', 'private_key', 'client_email']
        for field in required_fields:
            if field not in cred_json:
                print(f"❌ Campo requerido faltante: {field}")
                return False
                
        if cred_json['type'] != 'service_account':
            print("❌ Tipo de cuenta incorrecto. Debe ser 'service_account'")
            return False
            
        print("✅ Estructura del archivo de credenciales válida")
        return True
        
    except json.JSONDecodeError:
        print("❌ Archivo de credenciales no es un JSON válido")
        return False
    except Exception as e:
        print(f"❌ Error al verificar credenciales: {e}")
        return False

if __name__ == "__main__":
    verify_gcp_setup()
    verify_credentials_file()