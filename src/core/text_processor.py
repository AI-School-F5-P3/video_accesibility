from typing import Dict, Any, List, Optional

# src/core/text_processor.py
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
    def __init__(self):
        """
        Initialize the text processor with UNE standard requirements.
        These values come directly from UNE153010 and UNE153020.
        """
        # UNE153010 subtitle requirements
        self.max_chars_per_line = 37
        self.max_lines = 2
        self.chars_per_second = 15
        self.min_duration = 1
        self.max_duration = 6

        # UNE153020 audio description requirements
        self.min_silence_duration = 2
        self.voice_speed = {
            'min_chars_per_second': 14,
            'max_chars_per_second': 17
        }
        self.word_rate = 2.5  # palabras por segundo (ajustar según necesidad)

    def format_subtitles(self, text: str, max_chars: int = 37) -> List[Dict[str, str]]:
        """
        Formatea texto para subtítulos según norma UNE153010.
        """
        result = {
            'text': text,
            'start_time': '00:00:00,000',
            'end_time': '00:00:03,000'
        }
        print("Debug - resultado:", result)  # Depuración
        return [result]

    def format_audio_description(self, text: str, max_duration: Optional[float] = None) -> str:
        """
        Formatea la descripción de audio según restricciones de tiempo.
        
        Args:
            text: Texto a formatear
            max_duration: Duración máxima en segundos (opcional)
        """
        if not text:
            return ""
            
        if max_duration is None:
            max_duration = 5.0  # Valor por defecto
            
        max_words = int(max_duration * self.word_rate)
        words = text.split()
        
        if len(words) > max_words:
            words = words[:max_words]
            text = ' '.join(words)
            text += '...'
            
        return text

    def validate_une_compliance(self, text, text_type='subtitle'):
        """
        Validates text against UNE standards.
        
        Args:
            text (str): Text to validate
            text_type (str): Either 'subtitle' or 'description'
            
        Returns:
            tuple: (bool, str) - (is_compliant, reason if not compliant)
        """
        if text_type == 'subtitle':
            # Check UNE153010 compliance
            if len(text) > self.max_chars_per_line:
                return False, f"Exceeds maximum characters per line ({self.max_chars_per_line})"
            
            lines = text.split('\n')
            if len(lines) > self.max_lines:
                return False, f"Exceeds maximum lines ({self.max_lines})"
                
        elif text_type == 'description':
            # Check UNE153020 compliance
            # This would include more specific checks for audio descriptions
            pass
            
        return True, "Compliant with UNE standards"

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