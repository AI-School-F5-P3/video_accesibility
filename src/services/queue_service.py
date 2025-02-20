import asyncio
from typing import Dict, Any, Callable
import logging
from datetime import datetime
from ..config.settings import Settings
from ..pipeline.utils.logger_config import LoggerSetup

class QueueService:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.active_tasks: Dict[str, Dict[str, Any]] = {}
        self.logger = LoggerSetup.setup()
        self.results: Dict[str, Any] = {}
        self.settings = Settings().get_config()
        self.processing_config = self.settings['processing_config']

    async def enqueue_task(
        self, 
        task_id: str, 
        processor: Callable, 
        **kwargs
    ) -> Dict[str, str]:
        """Encola una nueva tarea de procesamiento"""
        task_info = {
            'id': task_id,
            'status': 'pending',
            'start_time': datetime.now().isoformat(),
            'processor': processor,
            'params': kwargs
        }
        
        self.active_tasks[task_id] = task_info
        await self.queue.put(task_info)
        self.logger.info(f"Tarea {task_id} encolada con parámetros: {kwargs}")
        
        return {'task_id': task_id, 'status': 'enqueued'}

    async def process_queue(self):
        """Procesa las tareas en la cola"""
        while True:
            try:
                task = await self.queue.get()
                task_id = task['id']
                self.active_tasks[task_id]['status'] = 'processing'
                
                try:
                    result = await self._execute_with_retry(
                        task['processor'],
                        **task['params']
                    )
                    self.results[task_id] = result
                    self.active_tasks[task_id]['status'] = 'completed'
                    self.active_tasks[task_id]['end_time'] = datetime.now().isoformat()
                except Exception as e:
                    self.active_tasks[task_id]['status'] = 'failed'
                    self.active_tasks[task_id]['error'] = str(e)
                    self.logger.error(f"Error en tarea {task_id}: {str(e)}")
                
                self.queue.task_done()
            except Exception as e:
                self.logger.error(f"Error en el procesamiento de cola: {str(e)}")

    async def _execute_with_retry(self, processor: Callable, **kwargs) -> Any:
        """Ejecuta una tarea con reintentos"""
        for attempt in range(self.processing_config['MAX_RETRIES']):
            try:
                return await processor(**kwargs)
            except Exception as e:
                if attempt == self.processing_config['MAX_RETRIES'] - 1:
                    raise e
                await asyncio.sleep(2 ** attempt)

    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Obtiene el estado actual de una tarea"""
        if task_id not in self.active_tasks:
            return {'error': 'Tarea no encontrada'}
        return self.active_tasks[task_id]

    async def cancel_task(self, task_id: str) -> Dict[str, str]:
        """Cancela una tarea pendiente"""
        if task_id not in self.active_tasks:
            return {'error': 'Tarea no encontrada'}
        
        if self.active_tasks[task_id]['status'] == 'processing':
            self.active_tasks[task_id]['status'] = 'cancelled'
            return {'status': 'cancelled'}
        
        return {'error': 'La tarea no puede ser cancelada'}