import os
import sys
from pathlib import Path

# Get the absolute path to the project root directory
project_root = Path(__file__).parent.parent

# Add the src directory to PYTHONPATH
src_path = os.path.join(project_root, "src")
sys.path.append(str(src_path))
