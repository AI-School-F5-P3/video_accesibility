# Create a test script: test_ai_setup.py
from src.config.ai_studio_config import initialize_ai_studio

def test_connection():
    try:
        model = initialize_ai_studio()
        print("Successfully connected to Google AI Studio!")
        return True
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_connection()