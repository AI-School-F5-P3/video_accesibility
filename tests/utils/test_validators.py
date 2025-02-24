import pytest
from pathlib import Path
from app.utils.validators import validate_video_format, validate_subtitle_text

def test_validate_video_format_valid_extension(tmp_path):
    """Test para validar formato de video correcto"""
    video_path = tmp_path / "test.mp4"
    # Crear un archivo de video vacío válido
    with open(video_path, 'wb') as f:
        f.write(b'RIFF')  # Encabezado mínimo de archivo MP4
    
    with pytest.raises(ValueError) as exc_info:
        validate_video_format(video_path)
    assert "No se puede abrir el archivo de video" in str(exc_info.value)

def test_validate_video_format_invalid_extension():
    """Test para validar formato de video incorrecto"""
    test_file = Path("test.txt")
    test_file.touch()  # Crear archivo temporal
    
    with pytest.raises(ValueError) as exc_info:
        validate_video_format(test_file)
    assert "Formato de video no soportado" in str(exc_info.value)
    
    test_file.unlink()  # Limpiar archivo temporal