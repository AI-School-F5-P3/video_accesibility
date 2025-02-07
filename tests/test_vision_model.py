import pytest
import numpy as np
from pathlib import Path
from src.services.vision_service.scene_vision import SceneVisionService
from src.config.constants import CONFIDENCE_THRESHOLD

class TestModelVision:
    @pytest.fixture
    def setup_vision_service(self):
        """Setup vision service and test data"""
        self.vision_service = SceneVisionService()
        
        # Create test directory and sample images
        test_dir = Path("tests/test_data/vision")
        test_dir.mkdir(parents=True, exist_ok=True)
        
        self.test_images = {
            "person": test_dir / "person.jpg",
            "action": test_dir / "action.jpg",
            "complex": test_dir / "complex_scene.jpg"
        }
        
        yield
        
        # Cleanup test files
        for img_path in self.test_images.values():
            if img_path.exists():
                img_path.unlink()

    def test_model_initialization(self, setup_vision_service):
        """Test proper model loading and initialization"""
        assert self.vision_service.model is not None
        assert hasattr(self.vision_service, 'process_frame')
        
        # Verify model configuration
        config = self.vision_service.get_config()
        assert config['confidence_threshold'] == CONFIDENCE_THRESHOLD
        assert config['model_type'] in ['yolo', 'gpt4-vision']

    def test_scene_analysis(self, setup_vision_service):
        """Test scene analysis capabilities"""
        # Test basic scene detection
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        results = self.vision_service.process_frame(frame)
        
        # Validate results structure (UNE153010 6.1)
        assert 'objects' in results
        assert 'actions' in results
        assert 'description' in results
        
        # Verify description format
        description = results['description']
        assert isinstance(description, str)
        assert len(description.split()) <= 20  # UNE153010 max words per description

    def test_object_detection(self, setup_vision_service):
        """Test object detection accuracy"""
        # Process test image with known objects
        results = self.vision_service.process_frame(
            str(self.test_images['person'])
        )
        
        # Validate object detection (UNE153010 6.2)
        objects = results['objects']
        assert len(objects) > 0
        
        for obj in objects:
            assert 'label' in obj
            assert 'confidence' in obj
            assert obj['confidence'] >= CONFIDENCE_THRESHOLD
            
            # Verify position description format
            assert 'position' in obj
            position = obj['position']
            assert position in ['left', 'center', 'right']  # UNE153010 positioning

    def test_action_recognition(self, setup_vision_service):
        """Test action and movement recognition"""
        results = self.vision_service.process_frame(
            str(self.test_images['action'])
        )
        
        # Validate action detection (UNE153010 6.3)
        actions = results['actions']
        assert len(actions) > 0
        
        for action in actions:
            assert 'type' in action
            assert 'confidence' in action
            assert action['confidence'] >= CONFIDENCE_THRESHOLD
            
            # Verify temporal description
            assert 'temporal_context' in action
            assert action['temporal_context'] in ['before', 'during', 'after']

    def test_description_quality(self, setup_vision_service):
        """Test quality and compliance of generated descriptions"""
        results = self.vision_service.process_frame(
            str(self.test_images['complex'])
        )
        
        description = results['description']
        
        # Test description structure (UNE153010 6.4)
        words = description.split()
        assert 5 <= len(words) <= 20  # Length constraints
        
        # Test language quality
        assert description[0].isupper()  # Starts with capital letter
        assert description.endswith('.')  # Ends with period
        
        # Verify present tense usage
        import spacy
        nlp = spacy.load('es_core_news_sm')
        doc = nlp(description)
        for token in doc:
            if token.pos_ == 'VERB':
                assert token.morph.get('Tense') == ['Pres']

    def test_model_performance(self, setup_vision_service):
        """Test model performance metrics"""
        import time
        
        # Test processing speed
        start_time = time.time()
        self.vision_service.process_frame(
            str(self.test_images['complex'])
        )
        processing_time = time.time() - start_time
        
        # Verify performance requirements
        assert processing_time < 1.0  # Max 1 second per frame
        
        # Test batch processing
        frames = [np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
                 for _ in range(5)]
        
        results = self.vision_service.process_batch(frames)
        assert len(results) == len(frames)

    def test_error_handling(self, setup_vision_service):
        """Test error handling and edge cases"""
        # Test invalid input
        with pytest.raises(ValueError):
            self.vision_service.process_frame(None)
        
        # Test low quality image
        low_quality = np.random.randint(0, 255, (48, 64, 3), dtype=np.uint8)
        results = self.vision_service.process_frame(low_quality)
        assert results['confidence'] < CONFIDENCE_THRESHOLD
        
        # Test missing features handling
        results = self.vision_service.process_frame(
            np.zeros((480, 640, 3), dtype=np.uint8)
        )
        assert results['description'] == "No hay elementos significativos en la escena."

if __name__ == "__main__":
    pytest.main([__file__])