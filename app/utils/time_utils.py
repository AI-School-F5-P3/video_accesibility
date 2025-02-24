from typing import List, Tuple, Optional
import numpy as np
from datetime import datetime, timedelta

class TimeSegment:
    """Clase para manejar segmentos de tiempo"""
    def __init__(self, start: float, end: float):
        if start > end:
            raise ValueError("El tiempo de inicio no puede ser mayor al tiempo final")
        self.start = start
        self.end = end
        
    @property
    def duration(self) -> float:
        return self.end - self.start
        
    def overlaps_with(self, other: 'TimeSegment') -> bool:
        return (self.start < other.end and self.end > other.start)

def calculate_overlap(
    segment1: Tuple[float, float], 
    segment2: Tuple[float, float]
) -> float:
    """
    Calcula el solapamiento entre dos segmentos de tiempo
    
    Args:
        segment1: Tupla (inicio, fin) del primer segmento
        segment2: Tupla (inicio, fin) del segundo segmento
        
    Returns:
        float: Duración del solapamiento en segundos
    """
    start1, end1 = segment1
    start2, end2 = segment2
    
    if start1 > end1 or start2 > end2:
        raise ValueError("Los tiempos de inicio no pueden ser mayores que los de fin")
    
    overlap_start = max(start1, start2)
    overlap_end = min(end1, end2)
    
    return max(0, overlap_end - overlap_start)

def find_gaps(segments: List[Tuple[float, float]], min_gap: float = 1.0) -> List[Tuple[float, float]]:
    """Encuentra huecos en la línea temporal que superen min_gap"""
    if not segments:
        return []
        
    sorted_segments = sorted(segments, key=lambda x: x[0])
    gaps = []
    
    for i in range(len(sorted_segments) - 1):
        gap_start = sorted_segments[i][1]
        gap_end = sorted_segments[i + 1][0]
        
        if gap_end - gap_start >= min_gap:
            gaps.append((gap_start, gap_end))
            
    return gaps

def time_to_frames(time_seconds: float, fps: float) -> int:
    """Convierte tiempo en segundos a número de frames"""
    return int(round(time_seconds * fps))

def frames_to_time(frame_number: int, fps: float) -> float:
    """Convierte número de frame a tiempo en segundos"""
    return frame_number / fps