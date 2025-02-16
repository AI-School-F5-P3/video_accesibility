from google.cloud import vision
import logging

def test_credentials():
    try:
        client = vision.ImageAnnotatorClient()
        print("✅ ¡Credenciales configuradas correctamente!")
        return True
    except Exception as e:
        print(f"❌ Error con las credenciales: {str(e)}")
        return False

if __name__ == "__main__":
    test_credentials()