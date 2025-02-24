from typing import List, Dict, Optional
from pydantic import BaseModel

class Scene(BaseModel):
    """Modelo que representa una escena o segmento de video"""
    id: str
    start_time: int  # Tiempo de inicio en milisegundos
    end_time: int    # Tiempo de fin en milisegundos
    frame_path: Optional[str] = None  # Ruta a un frame representativo de la escena
    description: Optional[str] = None  # Descripción generada de la escena
    confidence: Optional[float] = None  # Confianza de la detección/descripción
    
    def duration_ms(self) -> int:
        """Obtener la duración de la escena en milisegundos"""
        return self.end_time - self.start_time
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario"""
        return {
            "id": self.id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "frame_path": self.frame_path,
            "description": self.description,
            "confidence": self.confidence,
            "duration_ms": self.duration_ms()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Scene':
        """Crear escena desde diccionario"""
        return cls(**data)

class SceneCollection(BaseModel):
    """Colección de escenas de un video"""
    video_id: str
    scenes: List[Scene] = []
    
    def add_scene(self, scene: Scene) -> None:
        """Añadir una escena a la colección"""
        self.scenes.append(scene)
    
    def get_scene_at_time(self, timestamp_ms: int) -> Optional[Scene]:
        """Obtener la escena en un timestamp específico"""
        for scene in self.scenes:
            if scene.start_time <= timestamp_ms <= scene.end_time:
                return scene
        return None
    
    def to_dict(self) -> Dict:
        """Convertir a diccionario"""
        return {
            "video_id": self.video_id,
            "scenes": [scene.to_dict() for scene in self.scenes]
        }