# filepath: /app/__init__.py
from pathlib import Path

APP_DIR = Path(__file__).parent
ROOT_DIR = APP_DIR.parent

__version__ = "1.0.0"