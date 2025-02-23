import pytest
import logging
from pathlib import Path
import sys

def configure_logging():
    """
    Configura el logging para mostrar información detallada durante la ejecución de los tests.
    Esto nos ayuda a entender mejor qué está pasando cuando se ejecutan las pruebas.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def run_all_tests():
    """
    Ejecuta todas las suites de tests y genera un reporte detallado.
    El reporte incluirá información sobre qué tests pasaron, fallaron o fueron saltados.
    """
    # Configuramos el logging
    configure_logging()
    logger = logging.getLogger(__name__)

    # Obtenemos la ruta al directorio de tests
    tests_dir = Path(__file__).parent
    
    logger.info("🚀 Iniciando la ejecución de todos los tests")
    logger.info(f"📁 Directorio de tests: {tests_dir}")

    # Ejecutamos los tests con diferentes marcadores
    test_suites = {
        "Pruebas de Credenciales": "test_credentials.py",
        "Pruebas del Procesador de Audio": "test_audio_processor.py",
        "Pruebas del Procesador de Voz": "test_speech_processor.py",
        "Pruebas del Procesador de Texto": "test_text_processor.py",
        "Pruebas del Analizador de Video": "test_video_analyzer.py"
    }

    results = {}
    
    for suite_name, test_file in test_suites.items():
        logger.info(f"\n📌 Ejecutando {suite_name}...")
        test_path = tests_dir / test_file
        
        if not test_path.exists():
            logger.warning(f"⚠️  Archivo de test no encontrado: {test_file}")
            continue

        # Ejecutamos la suite de tests y capturamos el resultado
        exit_code = pytest.main([
            str(test_path),
            '-v',  # Modo verboso
            '--tb=short',  # Traceback corto para errores
            '--color=yes',  # Colorear la salida
        ])
        
        results[suite_name] = exit_code == 0

    # Mostramos el resumen final
    logger.info("\n📊 Resumen de la ejecución:")
    all_passed = True
    
    for suite_name, passed in results.items():
        status = "✅ PASÓ" if passed else "❌ FALLÓ"
        logger.info(f"{status} - {suite_name}")
        all_passed = all_passed and passed

    # Mensaje final
    if all_passed:
        logger.info("\n🎉 ¡Todos los tests pasaron exitosamente!")
    else:
        logger.error("\n⚠️  Algunos tests fallaron. Por favor, revisa los detalles arriba.")

    return all_passed

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)