import shutil
import subprocess
from typing import List, Tuple

def check_dependencies() -> List[Tuple[str, bool]]:
    """Verifica que todas las dependencias estén instaladas."""
    dependencies = [
        ('ffmpeg', 'ffmpeg -version'),
        ('python3', 'python3 --version'),
        ('pip', 'pip --version')
    ]
    
    results = []
    for dep, cmd in dependencies:
        exists = shutil.which(dep) is not None
        results.append((dep, exists))
        
    return results