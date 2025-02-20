import logging
from datetime import datetime
from pathlib import Path
from ...config.settings import Settings

class LoggerSetup:
    @staticmethod
    def setup(name: str = 'video_accessibility') -> logging.Logger:
        """Configura y retorna un logger"""
        settings = Settings()
        log_dir = settings.project_root / "logs"
        log_dir.mkdir(exist_ok=True)

        logger = logging.getLogger(name)
        
        # Evitar duplicación de handlers
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.INFO)

        # Handler para archivo
        file_handler = logging.FileHandler(
            log_dir / f"processing_{datetime.now().strftime('%Y%m%d')}.log"
        )
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )

        # Handler para consola
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(
            logging.Formatter('%(levelname)s: %(message)s')
        )

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        return logger