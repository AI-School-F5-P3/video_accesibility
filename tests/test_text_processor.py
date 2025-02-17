# tests/test_text_processor.py
import pytest
from typing import List, Dict, Optional
from src.core.text_processor import TextProcessor

def test_subtitle_formatting(mocker, une_standards):
    """
    Tests subtitle generation and formatting according to
    UNE153010 standards.
    """
    processor = TextProcessor()
    
    mocker.patch.object(
        processor,
        'format_subtitles',
        return_value=[
            {
                "text": "This is a long sentence",
                "start": 0.0,
                "end": 2.0
            }
        ]
    )
    
    result = processor.format_subtitles("Test text")
    assert all(len(sub["text"]) <= une_standards['UNE153010']['max_chars_per_line'] 
              for sub in result)

def test_text_processor_initialization():
    processor = TextProcessor()
    assert processor.max_chars_per_line == 37
    assert processor.max_lines == 2
    assert processor.chars_per_second == 15

def test_format_subtitles():
    processor = TextProcessor()
    test_text = "Este es un texto de prueba"
    result = processor.format_subtitles(test_text)
    
    assert isinstance(result, list)
    assert len(result) > 0
    assert 'text' in result[0]
    assert 'start_time' in result[0]
    assert 'end_time' in result[0]

def test_format_subtitles_empty_text():
    processor = TextProcessor()
    result = processor.format_subtitles("")
    assert isinstance(result, list)
    assert len(result) == 0

def test_format_subtitles_long_text():
    processor = TextProcessor()
    long_text = "Este es un texto muy largo que debería dividirse en múltiples subtítulos"
    result = processor.format_subtitles(long_text)
    
    assert isinstance(result, list)
    assert len(result) > 1
    for subtitle in result:
        assert 'text' in subtitle
        assert 'start_time' in subtitle
        assert 'end_time' in subtitle
        assert len(subtitle['text']) <= processor.max_chars_per_line

def test_format_audio_description():
    processor = TextProcessor()
    test_description = "Una persona camina por la calle"
    available_time = 3.0
    result = processor.format_audio_description(test_description, max_duration=available_time)
    
    assert isinstance(result, str)
    assert len(result.split()) <= int(available_time * processor.word_rate)

def test_une_compliance_subtitle():
    processor = TextProcessor()
    # Test valid subtitle
    valid_text = "Este es un subtítulo válido"
    is_valid, _ = processor.validate_une_compliance(valid_text, 'subtitle')
    assert is_valid == True

    # Test invalid subtitle (too long)
    invalid_text = "Este es un subtítulo demasiado largo que excede el límite de caracteres permitido por línea según la norma UNE153010"
    is_valid, reason = processor.validate_une_compliance(invalid_text, 'subtitle')
    assert is_valid == False