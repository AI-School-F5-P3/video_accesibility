from typing import List, Dict, Tuple, Optional
from app.config.une_config import UNE153010Config  # Corrección aquí
from app.models.schemas import SubtitleConfig

class TextProcessor:
    """
    Handles text processing for accessibility features, ensuring compliance 
    with UNE153010 (subtitles) and UNE153020 (audio descriptions) standards.
    
    This class is responsible for:
    - Formatting subtitles within character limits
    - Structuring audio descriptions
    - Ensuring reading speed compliance
    - Managing text timing
    """
    def __init__(self, config: Optional[SubtitleConfig] = None):
        """
        Initialize the text processor with UNE standard requirements.
        These values come directly from UNE153010 and UNE153020.
        """
        self.config = config or SubtitleConfig()
        self.une_config = UNE153010Config()
        self.max_chars_per_line = 37
        self.max_lines = 2
        self.chars_per_second = 15  # Añadido
        self.word_rate = 3.0

    def _initialize_config(self):
        """Inicializa configuración desde UNE153010"""
        self.max_chars_per_line = self.config.MAX_CHARS_PER_LINE
        self.max_lines = self.config.MAX_LINES
        self.word_rate = self.config.WORDS_PER_SECOND
        self.min_duration = self.config.MIN_DURATION

    def format_subtitles(self, text: str) -> List[Dict[str, str]]:
        """
        Formatea texto para subtítulos según norma UNE153010.
        """
        if not text:
            return []
            
        words = text.split()
        chunks = []
        current_chunk = []
        
        for word in words:
            if len(' '.join(current_chunk + [word])) <= self.max_chars_per_line:
                current_chunk.append(word)
            else:
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                
        if current_chunk:
            chunks.append(' '.join(current_chunk))
            
        return [
            {
                'text': chunk,
                'start_time': f'00:00:{i*3:02d},000',
                'end_time': f'00:00:{(i+1)*3:02d},000'
            }
            for i, chunk in enumerate(chunks)
        ]

    def format_audio_description(self, text: str, max_duration: Optional[float] = None) -> str:
        """
        Formatea el texto para audiodescripción
        Args:
            text: Texto a formatear
            max_duration: Duración máxima en segundos
        Returns:
            str: Texto formateado
        """
        if not text:
            return ""
            
        if max_duration:
            words = text.split()
            max_words = int(max_duration * self.word_rate)
            return ' '.join(words[:max_words])
            
        return text

    def validate_une_compliance(self, text: str, text_type: str = 'subtitle') -> Tuple[bool, str]:
        """Valida el texto según estándares UNE"""
        if not text:
            return True, ""
            
        if text_type == 'subtitle':
            # Verificar longitud máxima por línea
            if len(text) > self.max_chars_per_line:
                return False, f"Excede máximo de {self.max_chars_per_line} caracteres"
                
            # Verificar número de líneas
            lines = text.split('\n')
            if len(lines) > self.max_lines:
                return False, f"Excede máximo de {self.max_lines} líneas"
                
            # Verificar caracteres por segundo
            duration = len(text) / self.chars_per_second
            if duration < 1.0:  # Mínimo 1 segundo
                return False, "Duración muy corta"
                
            return True, ""
        return False, "Tipo de texto no válido"

    def optimize_text_timing(self, text, available_time):
        """
        Optimizes text to fit within available time while maintaining readability.
        
        Args:
            text (str): Text to optimize
            available_time (float): Available time in seconds
            
        Returns:
            dict: Optimized text with timing information
        """
        chars_per_second = len(text) / available_time
        
        # Check if the text fits within UNE standard limits
        return {
            'text': text,
            'duration': available_time,
            'is_optimal': chars_per_second <= self.chars_per_second
        }

    def _format_time(self, seconds: float) -> str:
        """
        Convierte segundos a formato de tiempo SRT (HH:MM:SS,mmm)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f'{hours:02d}:{minutes:02d}:{seconds:02d},000'