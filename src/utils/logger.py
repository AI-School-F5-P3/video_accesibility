import logging
from pathlib import Path

def setup_logging(base_dir: Path):
    log_dir = base_dir / 'logs'
    log_dir.mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_dir / 'video_description.log'),
            logging.StreamHandler()
        ]
    )