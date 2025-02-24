import logging
import logging.config
from pathlib import Path
import json
from datetime import datetime

def setup_logging(log_level: str = "INFO"):
    """Configura el sistema de logging"""
    log_dir = Path(__file__).parent.parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Nombre del archivo de log con timestamp
    timestamp = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"app_{timestamp}.log"
    
    config = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'detailed': {
                'format': '%(asctime)s | %(name)-12s | %(levelname)-8s | %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'simple': {
                'format': '%(levelname)s | %(message)s'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'simple',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'DEBUG',
                'formatter': 'detailed',
                'filename': str(log_file),
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            },
            'error_file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': 'ERROR',
                'formatter': 'detailed',
                'filename': str(log_dir / f"error_{timestamp}.log"),
                'maxBytes': 10485760,
                'backupCount': 5
            }
        },
        'loggers': {
            'app': {
                'level': log_level,
                'handlers': ['console', 'file', 'error_file'],
                'propagate': False
            }
        }
    }
    
    logging.config.dictConfig(config)
    return logging.getLogger('app')