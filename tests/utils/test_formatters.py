import pytest
from app.utils.formatters import format_timestamp, format_duration, format_subtitle

def test_format_timestamp():
    """
    Test la función format_timestamp con diferentes casos:
    - Tiempo normal
    - Tiempo cero
    - Tiempo con milisegundos
    """
    test_cases = [
        (3661.123, "01:01:01.123"),
        (0, "00:00:00.000"),
        (7200.5, "02:00:00.500")
    ]
    
    for input_time, expected in test_cases:
        assert format_timestamp(input_time) == expected

def test_format_duration():
    """
    Test la función format_duration con diferentes casos:
    - Duración normal
    - Duración cero
    - Duración con milisegundos
    """
    test_cases = [
        ((0, 3661.123), "01:01:01.123"),
        ((1000, 2000), "00:16:40.000"),
        ((0, 7200.5), "02:00:00.500")
    ]
    
    for (start, end), expected in test_cases:
        assert format_duration(start, end) == expected

def test_format_subtitle():
    """
    Test la función format_subtitle:
    - Formato correcto SRT
    - Tiempos correctos
    - Texto multilinea
    """
    cases = [
        {
            "text": "Texto de prueba",
            "start": 1.0,
            "end": 4.0,
            "expected": "00:00:01.000 --> 00:00:04.000\nTexto de prueba\n"
        },
        {
            "text": "Línea 1\nLínea 2",
            "start": 5.5,
            "end": 8.5,
            "expected": "00:00:05.500 --> 00:00:08.500\nLínea 1\nLínea 2\n"
        }
    ]
    
    for case in cases:
        result = format_subtitle(case["text"], case["start"], case["end"])
        assert result == case["expected"]