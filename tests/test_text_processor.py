import pytest
from src.core.text_processor import TextProcessor

def test_format_audio_description():
    processor = TextProcessor()
    test_description = "Una persona camina por la calle"
    available_time = 3.0
    result = processor.format_audio_description(test_description, max_duration=available_time)
    
    assert isinstance(result, str)
    assert len(result.split()) <= int(available_time * processor.word_rate)

def test_format_subtitles():
    processor = TextProcessor()
    test_text = "Este es un texto de prueba"
    result = processor.format_subtitles(test_text)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert 'text' in result[0]
    assert 'start_time' in result[0]