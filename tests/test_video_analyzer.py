import pytest
import os
from pathlib import Path
import numpy as np
from src.core.video_processor.frame_extractor import FrameExtractor
from src.core.video_processor.video_manager import VideoManager
from src.utils.validators import VideoValidator
from src.config.constants import (
    MIN_SILENCE_DURATION,
    MAX_DESCRIPTION_DURATION,
    ALLOWED_VIDEO_FORMATS,
)


class TestVideoProcessor:
    @pytest.fixture
    def setup_test_files(self):
        # Setup test video paths
        test_dir = Path("tests/test_data")
        test_dir.mkdir(exist_ok=True)

        self.valid_video = test_dir / "valid_test.mp4"
        self.invalid_video = test_dir / "invalid_test.txt"
        self.test_output = test_dir / "output"

        yield

        # Cleanup
        if self.valid_video.exists():
            self.valid_video.unlink()
        if self.invalid_video.exists():
            self.invalid_video.unlink()

    def test_video_validation(self, setup_test_files):
        """Test video format and content validation according to UNE153010"""
        validator = VideoValidator()

        # Test format validation
        assert validator.validate_format(self.valid_video)
        assert not validator.validate_format(self.invalid_video)

        # Test duration validation (UNE153010 4.2.1)
        video_manager = VideoManager(str(self.valid_video))
        duration = video_manager.get_duration()
        assert MIN_SILENCE_DURATION <= duration <= MAX_DESCRIPTION_DURATION

        # Test frame rate validation (UNE153010 4.2.2)
        fps = video_manager.get_fps()
        assert 24 <= fps <= 30, "Frame rate must be between 24-30 fps"

    def test_frame_extraction(self, setup_test_files):
        """Test frame extraction functionality"""
        extractor = FrameExtractor(str(self.valid_video))

        # Test frame extraction at specific timestamps
        frame = extractor.extract_frame(timestamp=1.0)
        assert frame is not None
        assert isinstance(frame, np.ndarray)

        # Test batch frame extraction
        frames = extractor.extract_frames(start_time=0, end_time=5, interval=1.0)
        assert len(frames) == 6  # 0 to 5 seconds, inclusive

        # Test frame quality (UNE153010 4.3.1)
        assert frame.shape[2] == 3  # RGB channels
        assert frame.dtype == np.uint8  # 8-bit color depth

    def test_scene_detection(self, setup_test_files):
        """Test scene detection and transition analysis"""
        video_manager = VideoManager(str(self.valid_video))

        # Test scene detection
        scenes = video_manager.detect_scenes()
        assert isinstance(scenes, list)

        # Validate scene transitions (UNE153010 4.4)
        for scene in scenes:
            start, end = scene
            # Ensure minimum scene duration for description
            assert end - start >= MIN_SILENCE_DURATION

            # Verify no overlap with critical audio segments
            assert not video_manager.has_critical_audio(start, end)

    def test_audio_silence_detection(self, setup_test_files):
        """Test detection of suitable silence gaps for audio description"""
        video_manager = VideoManager(str(self.valid_video))

        # Test silence detection
        silences = video_manager.detect_silences(
            min_duration=MIN_SILENCE_DURATION, threshold_db=-40
        )

        # Validate silence segments (UNE153010 4.5)
        for start, end in silences:
            duration = end - start
            assert duration >= MIN_SILENCE_DURATION
            assert duration <= MAX_DESCRIPTION_DURATION

            # Verify audio level in silence segment
            audio_level = video_manager.get_audio_level(start, end)
            assert audio_level <= -40  # dB threshold

    def test_integration_components(self, setup_test_files):
        """Test integration between video processing components"""
        video_manager = VideoManager(str(self.valid_video))
        frame_extractor = FrameExtractor(str(self.valid_video))

        # Test complete processing pipeline
        scenes = video_manager.detect_scenes()
        silences = video_manager.detect_silences()

        # Validate scene-silence alignment
        for scene_start, scene_end in scenes:
            # Find matching silence for scene
            matching_silence = next(
                (
                    silence
                    for silence in silences
                    if silence[0] >= scene_start and silence[1] <= scene_end
                ),
                None,
            )

            if matching_silence:
                # Extract frame from silence period
                frame = frame_extractor.extract_frame(matching_silence[0])
                assert frame is not None

                # Verify frame quality
                assert frame.shape[2] == 3
                assert frame.dtype == np.uint8

    def test_output_generation(self, setup_test_files):
        """Test generation of output files and formats"""
        video_manager = VideoManager(str(self.valid_video))

        # Test SRT generation (UNE153010 5.1)
        srt_content = video_manager.generate_description_srt()
        assert srt_content is not None

        # Validate SRT format
        srt_lines = srt_content.split("\n")
        assert len(srt_lines) > 0

        # Test timing format
        import re

        time_pattern = r"\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}"
        assert re.match(time_pattern, srt_lines[1])


if __name__ == "__main__":
    pytest.main([__file__])
