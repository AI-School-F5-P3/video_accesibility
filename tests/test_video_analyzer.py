import pytest
import cv2
import numpy as np
from pathlib import Path
import json
from unittest.mock import Mock, patch
from src.core.video_analyzer import FrameExtractor, FrameAnalyzer
import math
import os

@pytest.fixture
def create_test_video(tmp_path):
    """Creates a sample video file for testing"""
    video_path = tmp_path / "test_video.mp4"
    
    # Create a simple video with black frames
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640,480))
    
    # Create 90 frames (3 seconds at 30fps)
    for _ in range(90):
        frame = np.zeros((480,640,3), np.uint8)
        out.write(frame)
    
    out.release()
    return str(video_path)

@pytest.fixture
def output_directory(tmp_path):
    """Creates a temporary directory for output frames"""
    output_dir = tmp_path / "frames"
    return str(output_dir)

class TestFrameExtraction:
    """Tests for the frame extraction functionality only"""
    
    def test_video_loading(self, create_test_video, output_directory):
        """Test that video properties are correctly loaded"""
        with patch('src.core.video_analyzer.FrameAnalyzer'):  # Mock the analyzer
            extractor = FrameExtractor(create_test_video, output_directory)
            assert math.isclose(extractor.fps, 30.0, rel_tol=1e-9)
            assert extractor.frame_count == 90
            assert extractor.duration == pytest.approx(3.0)

    def test_frame_extraction_interval(self, create_test_video, output_directory):
        """Test that frames are extracted at correct intervals"""
        with patch('src.core.video_analyzer.FrameAnalyzer'):
            extractor = FrameExtractor(create_test_video, output_directory, interval=1)
            frames_info = extractor.extract_frames()
            
            # Should have 3 frames for a 3-second video with 1-second interval
            assert len(frames_info) == 3
            
            # Check frame intervals
            timestamps = [t for t, _ in frames_info]
            intervals = np.diff(timestamps)
            assert all(pytest.approx(i) == 1.0 for i in intervals)

    def test_frame_saving(self, create_test_video, output_directory):
        """Test that frames are saved as valid image files"""
        with patch('src.core.video_analyzer.FrameAnalyzer'):
            extractor = FrameExtractor(create_test_video, output_directory)
            frames_info = extractor.extract_frames()
            
            for _, frame_path in frames_info:
                assert Path(frame_path).exists()
                img = cv2.imread(frame_path)
                assert img is not None
                assert img.shape == (480, 640, 3)

    def test_invalid_video_path(self, output_directory):
        """Test handling of invalid video path"""
        with patch('src.core.video_analyzer.FrameAnalyzer'):
            with pytest.raises(ValueError) as exc_info:
                FrameExtractor("nonexistent_video.mp4", output_directory)
            assert "Could not open video" in str(exc_info.value)

@pytest.mark.skipif(
    "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ,
    reason="Google Cloud credentials not configured"
)
class TestCloudVision:
    """Tests that require Google Cloud Vision credentials"""
    
    def test_frame_analysis(self, tmp_path):
        """Test frame analysis with Google Cloud Vision"""
        # This test only runs if credentials are properly configured
        analyzer = FrameAnalyzer()
        
        # Create a simple test image
        test_image = tmp_path / "test.jpg"
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        cv2.imwrite(str(test_image), img)
        
        # Test analysis
        result = analyzer.analyze_frame(str(test_image))
        assert isinstance(result, dict)
        assert 'objects' in result
        assert 'labels' in result
        assert 'text' in result

def test_process_video_output(create_test_video, output_directory):
    """Test the complete video processing pipeline"""
    # Mock the Google Cloud Vision analysis part
    mock_analysis = {
        'objects': [],
        'labels': [{'description': 'Test', 'confidence': 0.9}],
        'text': ''
    }
    
    with patch('src.core.video_analyzer.FrameAnalyzer') as MockAnalyzer:
        mock_instance = MockAnalyzer.return_value
        mock_instance.analyze_frame.return_value = mock_analysis
        
        extractor = FrameExtractor(create_test_video, output_directory)
        results = extractor.process_video()
        
        # Check results structure
        assert isinstance(results, list)
        assert len(results) > 0
        assert all(isinstance(r, dict) for r in results)
        assert all('timestamp' in r for r in results)
        assert all('analysis' in r for r in results)