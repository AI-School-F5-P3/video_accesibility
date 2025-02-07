import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from src.utils.directory_utils import get_root_directory, setup_directories

@pytest.fixture
def mock_project_structure(tmp_path):
    """Create a temporary project structure for testing."""
    return tmp_path

def test_get_root_directory():
    """Test that get_root_directory returns a Path object."""
    root_dir = get_root_directory()
    assert isinstance(root_dir, Path)
    assert root_dir.exists()

@patch('src.utils.directory_utils.get_root_directory')
def test_setup_directories(mock_get_root, mock_project_structure):
    """Test that setup_directories creates all required directories."""
    mock_get_root.return_value = mock_project_structure
    
    directories = setup_directories()
    
    # Verify all expected directories are created
    expected_dirs = ['data', 'raw', 'processed', 'transcripts', 'audio', 'temp']
    for dir_name in expected_dirs:
        assert directories[dir_name].exists()
        assert directories[dir_name].is_dir()

def test_setup_directories_handles_existing(tmp_path):
    """Test that setup_directories handles existing directories gracefully."""
    with patch('src.utils.directory_utils.get_root_directory', return_value=tmp_path):
        # Create a directory that already exists
        (tmp_path / 'data').mkdir()
        
        # Should not raise an exception
        directories = setup_directories()
        assert directories['data'].exists()