from typing import Union, Dict, Any
from datetime import timedelta
import json

def format_timestamp(seconds: Union[float, int]) -> str:
    """
    Formatea tiempo en segundos a formato HH:MM:SS.mmm
    
    Args:
        seconds (Union[float, int]): Tiempo en segundos
        
    Returns:
        str: Tiempo formateado en HH:MM:SS.mmm
    """
    td = timedelta(seconds=float(seconds))
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    seconds = td.seconds % 60
    milliseconds = td.microseconds // 1000
    
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}.{milliseconds:03d}"

def format_duration(start: float, end: float) -> str:
    """
    Calcula y formatea la duración entre dos tiempos
    
    Args:
        start (float): Tiempo inicial en segundos
        end (float): Tiempo final en segundos
        
    Returns:
        str: Duración formateada en HH:MM:SS.mmm
    """
    duration = end - start
    return format_timestamp(duration)

def format_json_response(data: Dict[str, Any]) -> str:
    """
    Formatea una respuesta JSON para mejor legibilidad
    
    Args:
        data (Dict[str, Any]): Datos a formatear
        
    Returns:
        str: JSON formateado
    """
    return json.dumps(data, indent=2, ensure_ascii=False)

def format_subtitle(text: str, start: float, end: float) -> str:
    """
    Formatea un subtítulo en formato SRT
    
    Args:
        text (str): Texto del subtítulo
        start (float): Tiempo inicial en segundos
        end (float): Tiempo final en segundos
        
    Returns:
        str: Subtítulo formateado en formato SRT
    """
    return f"{format_timestamp(start)} --> {format_timestamp(end)}\n{text}\n"