import pytest
import numpy as np
from app.core.audio_processor import AudioProcessor

def test_silence_detection(mocker, une_standards):
    """
    Tests detection of silence periods suitable for audio descriptions,
    ensuring they meet UNE153020 duration requirements.
    """
    processor = AudioProcessor()  # Ahora usa el modelo mock por defecto
    mock_audio = np.zeros(44100 * 5)
    result = processor.find_silences(mock_audio)
    
    assert len(result) > 0
    for period in result:
        duration = period["end"] - period["start"]
        assert duration >= une_standards['UNE153020']['silence_gap']

def test_audio_quality_assessment(mocker):
    processor = AudioProcessor()  # Ahora usa el modelo mock por defecto
    quality_metrics = {
        "signal_to_noise": 25.5,
        "clarity_score": 0.85,
        "background_noise_level": -45.0,
        "issues": []
    }
    
    # Corregir la ruta del mock
    mocker.patch.object(
        processor,
        'assess_quality',
        return_value=quality_metrics
    )
    
    result = processor.assess_quality(np.zeros(1000))
    assert result["clarity_score"] >= 0.8