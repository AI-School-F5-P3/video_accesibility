import pytest
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock
from google.cloud import texttospeech_v1
from src.core.audio_processor import AudioProcessor, VoiceSynthesizer

@pytest.fixture
def voice_synthesizer():
    """Create a VoiceSynthesizer instance for testing."""
    return VoiceSynthesizer()

@pytest.fixture
def audio_processor():
    """Create an AudioProcessor instance for testing."""
    return AudioProcessor()

@pytest.fixture
def mock_tts_client():
    """Create a mock TTS client."""
    with patch('google.cloud.texttospeech_v1.TextToSpeechClient') as mock:
        yield mock

@pytest.fixture
def sample_audio_content():
    """Create sample audio content for testing."""
    return b'dummy audio content'

class TestAudioProcessor:
    """Tests for the AudioProcessor class functionality."""
    
    def test_silence_detection(self, audio_processor, une_standards):
        """
        Tests detection of silence periods suitable for audio descriptions,
        ensuring they meet UNE153020 duration requirements.
        """
        mock_audio = np.zeros(44100 * 5)
        result = audio_processor.find_silences(mock_audio)
        
        assert len(result) > 0
        for period in result:
            duration = period["end"] - period["start"]
            assert duration >= une_standards['UNE153020']['silence_gap']

    def test_audio_quality_assessment(self, audio_processor, mocker):
        """Tests the audio quality assessment functionality."""
        quality_metrics = {
            "signal_to_noise": 25.5,
            "clarity_score": 0.85,
            "background_noise_level": -45.0,
            "issues": []
        }
        
        mocker.patch.object(
            audio_processor,
            'assess_quality',
            return_value=quality_metrics
        )
        
        result = audio_processor.assess_quality(np.zeros(1000))
        assert result["clarity_score"] >= 0.8

class TestVoiceSynthesizer:
    """Tests for the VoiceSynthesizer class functionality."""

    def test_voice_synthesizer_initialization(self, voice_synthesizer):
        """Test that VoiceSynthesizer initializes correctly."""
        assert isinstance(voice_synthesizer.tts_client, texttospeech_v1.TextToSpeechClient)
        assert isinstance(voice_synthesizer.voice_params, texttospeech_v1.VoiceSelectionParams)
        assert isinstance(voice_synthesizer.audio_config, texttospeech_v1.AudioConfig)

    def test_voice_synthesizer_custom_language(self):
        """Test VoiceSynthesizer initialization with custom language settings."""
        synthesizer = VoiceSynthesizer(language_code='en-US', voice_name='en-US-Wavenet-A')
        assert synthesizer.voice_params.language_code == 'en-US'
        assert synthesizer.voice_params.name == 'en-US-Wavenet-A'

    @pytest.mark.parametrize('text,expected_result', [
        ('', None),  # Empty text should return None
        ('Test text', True),  # Valid text should succeed
    ])
    def test_generate_audio_validation(self, voice_synthesizer, text, expected_result, tmp_path):
        """Test generate_audio input validation."""
        output_path = tmp_path / 'test_audio.wav'
        if expected_result is None:
            assert voice_synthesizer.generate_audio(text, output_path) is None
        else:
            with patch.object(voice_synthesizer.tts_client, 'synthesize_speech') as mock_synthesize:
                mock_synthesize.return_value = MagicMock(audio_content=b'test audio content')
                result = voice_synthesizer.generate_audio(text, output_path)
                assert result == output_path
                assert result.exists()

    def test_generate_audio_full_process(self, voice_synthesizer, mock_tts_client, 
                                       sample_audio_content, tmp_path):
        """Test the complete audio generation process."""
        output_path = tmp_path / 'test_output.wav'
        mock_response = MagicMock()
        mock_response.audio_content = sample_audio_content
        mock_tts_client.return_value.synthesize_speech.return_value = mock_response
        
        result = voice_synthesizer.generate_audio("Test text", output_path)
        
        assert result == output_path
        assert result.exists()
        with open(result, 'rb') as f:
            assert f.read() == sample_audio_content

    def test_generate_audio_handles_errors(self, voice_synthesizer, mock_tts_client, tmp_path):
        """Test error handling in generate_audio."""
        output_path = tmp_path / 'test_error.wav'
        mock_tts_client.return_value.synthesize_speech.side_effect = Exception("TTS Error")
        
        result = voice_synthesizer.generate_audio("Test text", output_path)
        assert result is None
        assert not output_path.exists()