import pytest
from app.core.text_processor import TextProcessor
from app.config.une_config import UNE153010Config

@pytest.fixture
def text_processor():
    return TextProcessor()

def test_format_audio_description(text_processor):
    test_description = "Una persona camina por la calle"
    available_time = 3.0
    result = text_processor.format_audio_description(test_description, max_duration=available_time)
    
    assert isinstance(result, str)
    assert len(result.split()) <= int(available_time * text_processor.word_rate)

def test_format_subtitles(text_processor):
    test_text = "Este es un texto de prueba"
    result = text_processor.format_subtitles(test_text)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert 'text' in result[0]
    assert 'start_time' in result[0]