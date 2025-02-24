from typing import Dict, Any, Optional, List
import asyncio
from collections import deque
import logging
from pathlib import Path
from .error_handler import ProcessingError
from .memory_manager import MemoryManager

logger = logging.getLogger(__name__)

class VideoQueue:
    def __init__(self, max_concurrent: int = 3):
        self.queue = deque()
        self.processing = set()
        self.results = {}
        self.max_concurrent = max_concurrent
        self.memory_manager = MemoryManager()

    async def add_task(self, video_path: Path, config: Dict[str, Any]) -> str:
        """Añade un video a la cola de procesamiento"""
        task_id = str(hash(str(video_path)))
        self.queue.append((task_id, video_path, config))
        logger.info(f"Tarea {task_id} añadida a la cola. Total en cola: {len(self.queue)}")
        
        if len(self.processing) < self.max_concurrent:
            asyncio.create_task(self.process_queue())
        
        return task_id

    async def process_queue(self):
        """Procesa la cola de videos"""
        while self.queue and len(self.processing) < self.max_concurrent:
            if not self.memory_manager.check_memory():
                logger.warning("Memoria insuficiente, esperando...")
                await asyncio.sleep(5)
                continue

            task_id, video_path, config = self.queue.popleft()
            self.processing.add(task_id)
            
            try:
                result = await self._process_video(video_path, config)
                self.results[task_id] = {
                    'status': 'completed',
                    'result': result
                }
            except Exception as e:
                logger.error(f"Error procesando tarea {task_id}: {e}")
                self.results[task_id] = {
                    'status': 'failed',
                    'error': str(e)
                }
            finally:
                self.processing.remove(task_id)

    async def _process_video(self, video_path: Path, config: Dict[str, Any]) -> Dict[str, Any]:
        """Procesa un video individual"""
        try:
            # Aquí implementar el procesamiento real del video
            return {'path': str(video_path), 'processed': True}
        except Exception as e:
            raise ProcessingError("PROCESSING_ERROR", str(e))

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Obtiene el estado de una tarea"""
        if task_id in self.processing:
            return {'status': 'processing'}
        elif task_id in self.results:
            return self.results[task_id]
        elif any(t[0] == task_id for t in self.queue):
            return {'status': 'queued'}
        return {'status': 'not_found'}

    def get_queue_status(self) -> Dict[str, Any]:
        """Obtiene el estado general de la cola"""
        return {
            'queued': len(self.queue),
            'processing': len(self.processing),
            'completed': len([r for r in self.results.values() if r['status'] == 'completed']),
            'failed': len([r for r in self.results.values() if r['status'] == 'failed'])
        }