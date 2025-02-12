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

    def format_subtitles(self, text):
        """
        Formats text into UNE153010-compliant subtitles.
        
        Args:
            text (str): Raw text to be formatted into subtitles
            
        Returns:
            list: List of subtitle dictionaries with text and timing
                 Each subtitle follows UNE153010 character and line limits
        """
        # This is a placeholder implementation
        # The actual implementation will split text properly
        return [{
            'text': text[:self.max_chars_per_line],
            'start_time': 0.0,
            'end_time': 2.0
        }]

    def format_audio_description(self, description, available_time):
        """
        Formats text for audio descriptions following UNE153020 standards.
        
        Args:
            description (str): Description to be formatted
            available_time (float): Available time slot in seconds
            
        Returns:
            dict: Formatted description with timing information
                 Ensures speaking speed meets UNE153020 requirements
        """
        # This is a placeholder implementation
        # The actual implementation will verify timing constraints
        return {
            'text': description,
            'duration': available_time,
            'chars_per_second': len(description) / available_time
        }

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