import psutil
import gc
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class MemoryManager:
    def __init__(self, max_memory_percent: float = 80.0):
        self.max_memory = max_memory_percent
        self.warning_threshold = 70.0
        
    def check_memory(self) -> bool:
        current_memory = psutil.Process().memory_percent()
        if current_memory > self.max_memory:
            logger.warning(f"Memoria crítica: {current_memory}%")
            gc.collect()
            return False
        elif current_memory > self.warning_threshold:
            logger.warning(f"Memoria alta: {current_memory}%")
            gc.collect()
        return True

    def get_available_memory(self) -> float:
        return psutil.virtual_memory().available / (1024 * 1024 * 1024)  # GB