import json
from pathlib import Path
from app.config.settings import settings

def validate_credentials():
    try:
        creds = settings.get_credentials_dict()
        required_fields = [
            'type',
            'project_id',
            'private_key_id',
            'private_key',
            'client_email',
            'client_id'
        ]
        
        # Validar campos requeridos
        missing_fields = [field for field in required_fields if field not in creds]
        if missing_fields:
            print(f"❌ Campos faltantes en credenciales: {', '.join(missing_fields)}")
            return False
            
        # Validar tipo de cuenta
        if creds['type'] != 'service_account':
            print(f"❌ Tipo de cuenta incorrecto: {creds['type']}")
            return False
            
        # Validar project_id
        if creds['project_id'] != settings.GOOGLE_CLOUD_PROJECT:
            print(f"⚠️ Project ID en credenciales ({creds['project_id']}) no coincide con .env ({settings.GOOGLE_CLOUD_PROJECT})")
            
        print("✅ Credenciales válidas")
        return True
        
    except Exception as e:
        print(f"❌ Error validando credenciales: {str(e)}")
        return False

if __name__ == "__main__":
    validate_credentials()