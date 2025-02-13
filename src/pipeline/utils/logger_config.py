import logging
from pathlib import Path
from typing import Optional

def setup_logger(
    log_file: Optional[Path] = None,
    level: int = logging.INFO
) -> logging.Logger:
    """Configura un logger centralizado para el pipeline."""
    
    logger = logging.getLogger('video_pipeline')
    logger.setLevel(level)
    
    # Formato del log
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Handler para consola
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler para archivo si se especifica
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger