from pathlib import Path
import logging
from typing import Dict

def get_root_directory() -> Path:
    """Get the root directory of the project."""
    return Path(__file__).parent.parent.parent

def setup_directories() -> Dict[str, Path]:
    """
    Create and return all necessary project directories.
    
    Returns:
        Dict[str, Path]: Dictionary containing all project directory paths
    """
    root_dir = get_root_directory()
    
    directories = {
        'data': root_dir / 'data',
        'raw': root_dir / 'data' / 'raw',
        'processed': root_dir / 'data' / 'processed',
        'transcripts': root_dir / 'data' / 'transcripts',
        'audio': root_dir / 'data' / 'audio',
        'temp': root_dir / 'data' / 'temp'
    }
    
    for dir_path in directories.values():
        dir_path.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {dir_path}")
    
    return directories