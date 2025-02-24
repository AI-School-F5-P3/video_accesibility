from functools import lru_cache
import hashlib
import pickle
import os
import time
from typing import Dict, Optional, List, Any
from pathlib import Path
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class CacheChunk:
    def __init__(self, data: Dict[str, Any], timestamp: float):
        self.data = data
        self.timestamp = timestamp

class ResultCache:
    def __init__(self, 
                 cache_dir: str = "cache",
                 max_cache_size_mb: int = 1000,
                 chunk_size_mb: int = 100,
                 max_age_days: int = 7):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.max_cache_size = max_cache_size_mb * 1024 * 1024  # Convertir a bytes
        self.chunk_size = chunk_size_mb * 1024 * 1024  # Convertir a bytes
        self.max_age = timedelta(days=max_age_days)
        self.chunks: Dict[str, List[CacheChunk]] = {}

    def get_video_hash(self, video_path: Path) -> str:
        """Genera un hash único para el video"""
        return hashlib.md5(str(video_path).encode()).hexdigest()

    @lru_cache(maxsize=100)
    def get_cached_analysis(self, video_hash: str) -> Optional[Dict]:
        """Obtiene el análisis completo cacheado"""
        cache_file = self.cache_dir / f"{video_hash}.pkl"
        if cache_file.exists():
            with open(cache_file, 'rb') as f:
                try:
                    data = pickle.load(f)
                    if self._is_cache_valid(data.get('timestamp', 0)):
                        return data.get('analysis')
                    else:
                        self._remove_cache_file(cache_file)
                except Exception as e:
                    logger.error(f"Error leyendo cache: {e}")
                    return None
        return None

    def save_analysis(self, video_hash: str, analysis: Dict):
        """Guarda el análisis completo en cache"""
        cache_file = self.cache_dir / f"{video_hash}.pkl"
        data = {
            'timestamp': time.time(),
            'analysis': analysis
        }
        
        self._ensure_cache_size()
        
        with open(cache_file, 'wb') as f:
            pickle.dump(data, f)

    def save_intermediate_result(self, video_hash: str, chunk_id: str, data: Dict[str, Any]):
        """Guarda resultados intermedios en chunks"""
        if video_hash not in self.chunks:
            self.chunks[video_hash] = []
        
        chunk = CacheChunk(data, time.time())
        self.chunks[video_hash].append(chunk)
        
        # Guardar en disco si superamos el tamaño del chunk
        if self._get_chunks_size(video_hash) > self.chunk_size:
            self._save_chunks_to_disk(video_hash)

    def get_intermediate_result(self, video_hash: str, chunk_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene resultados intermedios"""
        # Primero buscar en memoria
        if video_hash in self.chunks:
            for chunk in self.chunks[video_hash]:
                if self._is_cache_valid(chunk.timestamp):
                    return chunk.data
        
        # Si no está en memoria, buscar en disco
        chunk_file = self.cache_dir / f"{video_hash}_{chunk_id}.chunk"
        if chunk_file.exists():
            with open(chunk_file, 'rb') as f:
                try:
                    data = pickle.load(f)
                    if self._is_cache_valid(data.get('timestamp', 0)):
                        return data.get('chunk_data')
                except Exception as e:
                    logger.error(f"Error leyendo chunk: {e}")
        return None

    def clean_cache(self):
        """Limpia la caché automáticamente"""
        logger.info("Iniciando limpieza de caché...")
        total_cleaned = 0
        
        for cache_file in self.cache_dir.glob("*.pkl"):
            if self._should_clean_file(cache_file):
                self._remove_cache_file(cache_file)
                total_cleaned += 1
        
        for chunk_file in self.cache_dir.glob("*.chunk"):
            if self._should_clean_file(chunk_file):
                self._remove_cache_file(chunk_file)
                total_cleaned += 1
        
        logger.info(f"Limpieza completada: {total_cleaned} archivos eliminados")

    def _is_cache_valid(self, timestamp: float) -> bool:
        """Verifica si la caché aún es válida"""
        cache_age = datetime.now() - datetime.fromtimestamp(timestamp)
        return cache_age < self.max_age

    def _ensure_cache_size(self):
        """Asegura que no superemos el tamaño máximo de caché"""
        current_size = sum(f.stat().st_size for f in self.cache_dir.glob("*"))
        if current_size > self.max_cache_size:
            self._clean_oldest_files(current_size - self.max_cache_size)

    def _clean_oldest_files(self, bytes_to_clean: int):
        """Limpia los archivos más antiguos hasta liberar el espacio necesario"""
        files = [(f, f.stat().st_mtime) for f in self.cache_dir.glob("*")]
        files.sort(key=lambda x: x[1])  # Ordenar por tiempo de modificación
        
        cleaned = 0
        for file_path, _ in files:
            if cleaned >= bytes_to_clean:
                break
            size = file_path.stat().st_size
            self._remove_cache_file(file_path)
            cleaned += size

    def _should_clean_file(self, file_path: Path) -> bool:
        """Determina si un archivo debe ser limpiado"""
        try:
            mtime = file_path.stat().st_mtime
            return not self._is_cache_valid(mtime)
        except Exception:
            return True

    def _remove_cache_file(self, file_path: Path):
        """Elimina un archivo de caché de manera segura"""
        try:
            file_path.unlink()
        except Exception as e:
            logger.error(f"Error eliminando archivo de caché {file_path}: {e}")

    def _get_chunks_size(self, video_hash: str) -> int:
        """Obtiene el tamaño total de los chunks en memoria para un video"""
        if video_hash not in self.chunks:
            return 0
        return sum(len(pickle.dumps(chunk.data)) for chunk in self.chunks[video_hash])

    def _save_chunks_to_disk(self, video_hash: str):
        """Guarda los chunks en disco y libera memoria"""
        if video_hash not in self.chunks:
            return
        
        for i, chunk in enumerate(self.chunks[video_hash]):
            chunk_file = self.cache_dir / f"{video_hash}_{i}.chunk"
            data = {
                'timestamp': chunk.timestamp,
                'chunk_data': chunk.data
            }
            with open(chunk_file, 'wb') as f:
                pickle.dump(data, f)
        
        # Limpiar chunks de memoria
        self.chunks[video_hash] = []