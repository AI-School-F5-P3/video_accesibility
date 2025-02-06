import pytest
import os

def pytest_addoption(parser):
    parser.addoption("--run-real", action="store_true", help="Ejecutar pruebas reales")

@pytest.fixture
def run_real_tests(request):
    return request.config.getoption("--run-real")

@pytest.fixture
def real_channel_id(request):
    """ Obtiene el ID de un canal real para pruebas """
    marker = request.node.get_closest_marker("channel_id")
    if marker:
        return marker.args[0]
    return os.getenv("TEST_CHANNEL_ID", "UCZLl7vfqlRjVL4YBHGmLVvQ")  # Canal por defecto

@pytest.fixture
def real_video_id(request):
    """ Obtiene el ID de un video real para pruebas """
    marker = request.node.get_closest_marker("video_id")
    if marker:
        return marker.args[0]
    return os.getenv("TEST_VIDEO_ID", "dQw4w9WgXcQ")  # Video por defecto
