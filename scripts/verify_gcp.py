import os
from google.cloud import storage
from google.cloud import vision_v1

def verify_gcp_setup():
    """Verifica la configuración completa de GCP"""
    results = {
        "storage": False,
        "vision": False
    }
    
    try:
        # Verificar Storage
        storage_client = storage.Client()
        buckets = list(storage_client.list_buckets(max_results=1))
        results["storage"] = True
        print("✅ Storage API configurada correctamente")
        
        # Verificar Vision API
        vision_client = vision_v1.ImageAnnotatorClient()
        results["vision"] = True
        print("✅ Vision API configurada correctamente")
        
        return all(results.values())
        
    except Exception as e:
        print(f"❌ Error en la configuración: {str(e)}")
        return False

if __name__ == "__main__":
    verify_gcp_setup()