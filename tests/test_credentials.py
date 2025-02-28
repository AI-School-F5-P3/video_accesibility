import logging
import sys

def test_credentials():
    try:
        # Intentar importar vision con manejo de excepciones
        try:
            from google.cloud import vision
            client = vision.ImageAnnotatorClient()
            print("✅ ¡Credenciales configuradas correctamente!")
            return True
        except ImportError:
            print("❌ Error: No se encuentra el paquete google-cloud-vision. Por favor, instálalo con 'pip install google-cloud-vision'")
            return False
        except Exception as e:
            print(f"❌ Error con las credenciales: {str(e)}")
            return False
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        return False

if __name__ == "__main__":
    test_credentials()