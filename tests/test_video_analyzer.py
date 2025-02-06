import pytest
import cv2
import numpy as np
from pathlib import Path
import json
from src.core.video_analyzer import FrameExtractor, FrameAnalyzer

@pytest.fixture
def create_test_video(tmp_path):
    """
    Crea un video de prueba simple para usar en los tests.
    Genera un video de 3 segundos con frames negros y blancos alternados.
    """
    video_path = tmp_path / "test_video.mp4"
    
    # Configuración del video: 30 FPS, 3 segundos = 90 frames
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(str(video_path), fourcc, 30.0, (640,480))
    
    # Crear frames alternando entre negro y blanco
    for i in range(90):  # 3 segundos a 30 FPS
        # Crear frame negro o blanco dependiendo de si i es par o impar
        color = 255 if i % 2 == 0 else 0
        frame = np.full((480, 640, 3), color, dtype=np.uint8)
        out.write(frame)
    
    out.release()
    return str(video_path)

@pytest.fixture
def output_directory(tmp_path):
    """
    Crea un directorio temporal para los frames extraídos.
    """
    output_dir = tmp_path / "frames"
    return str(output_dir)

def test_frame_extractor_initialization(create_test_video, output_directory):
    """
    Verifica que el FrameExtractor se inicializa correctamente y
    obtiene las propiedades correctas del video.
    """
    extractor = FrameExtractor(create_test_video, output_directory)
    
    # Verificar propiedades básicas del video
    assert extractor.fps == 30.0  # El video se creó a 30 FPS
    assert extractor.frame_count == 90  # 3 segundos * 30 FPS
    assert extractor.duration == pytest.approx(3.0)  # Duración total en segundos
    assert Path(output_directory).exists()  # El directorio de salida debe existir

def test_frame_extraction_interval(create_test_video, output_directory):
    """
    Verifica que los frames se extraen en los intervalos correctos.
    """
    interval = 1  # Extraer un frame cada segundo
    extractor = FrameExtractor(create_test_video, output_directory, interval=interval)
    frames_info = extractor.extract_frames()
    
    # Verificar el número de frames extraídos
    expected_frames = int(extractor.duration / interval)
    assert len(frames_info) == expected_frames
    
    # Verificar que los timestamps están espaciados correctamente
    timestamps = [t for t, _ in frames_info]
    intervals = np.diff(timestamps)
    assert all(pytest.approx(i) == interval for i in intervals)

def test_frame_saving(create_test_video, output_directory):
    """
    Verifica que los frames se guardan correctamente como archivos de imagen.
    """
    extractor = FrameExtractor(create_test_video, output_directory)
    frames_info = extractor.extract_frames()
    
    # Verificar que cada archivo existe y es una imagen válida
    for _, frame_path in frames_info:
        assert Path(frame_path).exists()
        img = cv2.imread(frame_path)
        assert img is not None
        assert img.shape == (480, 640, 3)

def test_invalid_video_path(output_directory):
    """
    Verifica que se maneja correctamente un archivo de video inválido.
    """
    with pytest.raises(ValueError) as exc_info:
        FrameExtractor("nonexistent_video.mp4", output_directory)
    assert "Could not open video" in str(exc_info.value)

def test_process_video_output(create_test_video, output_directory):
    """
    Verifica que el procesamiento del video genera el archivo JSON esperado
    y que tiene la estructura correcta.
    """
    extractor = FrameExtractor(create_test_video, output_directory)
    results = extractor.process_video()
    
    # Verificar que el archivo JSON existe
    json_path = Path(output_directory) / 'video_analysis.json'
    assert json_path.exists()
    
    # Verificar la estructura del JSON
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        assert isinstance(data, list)
        if data:  # Si hay resultados
            first_frame = data[0]
            assert 'timestamp' in first_frame
            assert 'frame_path' in first_frame
            assert 'analysis' in first_frame
            assert isinstance(first_frame['analysis'], dict)

def test_frame_analyzer_error_handling(tmp_path):
    """
    Verifica que el FrameAnalyzer maneja correctamente los errores
    cuando no puede analizar una imagen.
    """
    analyzer = FrameAnalyzer()
    
    # Crear una imagen inválida para probar
    invalid_image = tmp_path / "invalid.jpg"
    invalid_image.write_text("not an image")
    
    # El análisis debería devolver un diccionario con campos vacíos
    result = analyzer.analyze_frame(str(invalid_image))
    assert isinstance(result, dict)
    assert 'objects' in result
    assert 'labels' in result
    assert 'text' in result
    assert len(result['objects']) == 0
    assert len(result['labels']) == 0
    assert result['text'] == ''

if __name__ == '__main__':
    pytest.main([__file__, '-v'])