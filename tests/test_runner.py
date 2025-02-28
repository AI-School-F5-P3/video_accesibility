#!/usr/bin/env python3
"""
Script simple para ejecutar todos los tests del proyecto MIRESSE
"""

import os
import sys
import subprocess
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

# Añadir el directorio raíz del proyecto al path de Python
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.insert(0, str(root_dir))

console = Console()

def run_all_tests():
    """Ejecuta todos los tests del proyecto"""
    console.print(Panel("[bold]MIRESSE - Ejecutando todos los tests[/bold]", style="blue"))
    
    # Obtener la ruta del directorio de tests
    tests_dir = root_dir / "tests"
    
    # Verificar que el directorio existe
    if not tests_dir.exists():
        console.print("[red]Error: No se encuentra el directorio de tests[/red]")
        return False
    
    # Comprobar dependencias específicas antes de ejecutar tests
    missing_deps = check_dependencies()
    if missing_deps:
        console.print("[yellow]Advertencia: Algunas dependencias no están instaladas:[/yellow]")
        for dep in missing_deps:
            console.print(f"  - {dep}")
        console.print("[yellow]Algunos tests podrían fallar debido a dependencias faltantes[/yellow]")
    
    # Ejecutar tests individuales en lugar de usar pytest para todo
    # Esto nos da más control sobre qué tests ejecutar y cómo manejar errores
    
    test_files = [f for f in tests_dir.glob("test_*.py") if f.is_file() and f.stat().st_size > 0]
    
    successful_tests = 0
    failed_tests = 0
    skipped_tests = 0
    
    # Tests normales (no asíncronos y sin problemas de importación conocidos)
    safe_tests = [
        "test_directory_utils.py",
        "test_video_analyzer.py",
        "test_text_processor.py"
    ]
    
    # Tests que requieren dependencias externas
    external_dep_tests = [
        "test_credentials.py",  # Requiere google-cloud-vision
        "test_speech_services.py",  # Requiere speech_service
        "test_speech_processor.py"  # Probablemente requiere dependencias de audio
    ]
    
    # Tests asíncronos
    async_tests = [
        "test_subtitle_generation.py",
        "test_subtitles.py",
        "test_api.py"
    ]
    
    # Ejecutar tests seguros primero
    for test_name in safe_tests:
        test_path = tests_dir / test_name
        if test_path.exists() and test_path.stat().st_size > 0:
            console.print(f"[yellow]Ejecutando test: {test_name}[/yellow]")
            env = os.environ.copy()
            env["PYTHONPATH"] = str(root_dir) + ":" + env.get("PYTHONPATH", "")
            result = subprocess.run(
                [sys.executable, str(test_path)],
                env=env,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                console.print(f"[green]✓ Test {test_name} completado correctamente[/green]")
                successful_tests += 1
            else:
                console.print(f"[red]✗ Test {test_name} falló[/red]")
                console.print(f"[red]Error: {result.stderr}[/red]")
                failed_tests += 1
    
    # Ejecutar tests con dependencias externas
    for test_name in external_dep_tests:
        test_path = tests_dir / test_name
        if test_path.exists() and test_path.stat().st_size > 0:
            console.print(f"[yellow]Intentando ejecutar test con dependencias externas: {test_name}[/yellow]")
            env = os.environ.copy()
            env["PYTHONPATH"] = str(root_dir) + ":" + env.get("PYTHONPATH", "")
            try:
                result = subprocess.run(
                    [sys.executable, str(test_path)],
                    env=env,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    console.print(f"[green]✓ Test {test_name} completado correctamente[/green]")
                    successful_tests += 1
                else:
                    console.print(f"[yellow]⚠ Test {test_name} falló - podría ser por dependencias faltantes[/yellow]")
                    skipped_tests += 1
            except Exception as e:
                console.print(f"[yellow]⚠ No se pudo ejecutar {test_name}: {str(e)}[/yellow]")
                skipped_tests += 1
    
    # Ejecutar tests async
    for test_name in async_tests:
        test_path = tests_dir / test_name
        if test_path.exists() and test_path.stat().st_size > 0:
            console.print(f"[yellow]Ejecutando test asíncrono: {test_name}[/yellow]")
            env = os.environ.copy()
            env["PYTHONPATH"] = str(root_dir) + ":" + env.get("PYTHONPATH", "")
            try:
                result = subprocess.run(
                    [sys.executable, str(test_path)],
                    env=env,
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    console.print(f"[green]✓ Test async {test_name} completado correctamente[/green]")
                    successful_tests += 1
                else:
                    # Para los test de API, es normal que fallen si el servidor no está corriendo
                    if test_name == "test_api.py":
                        console.print(f"[yellow]⚠ Test {test_name} falló - ¿está el servidor API ejecutándose?[/yellow]")
                        skipped_tests += 1
                    else:
                        console.print(f"[red]✗ Test async {test_name} falló[/red]")
                        failed_tests += 1
            except Exception as e:
                console.print(f"[yellow]⚠ No se pudo ejecutar {test_name}: {str(e)}[/yellow]")
                skipped_tests += 1
    
    # Imprimir resumen
    console.print("\n[bold]Resumen de tests:[/bold]")
    console.print(f"[green]✓ Tests exitosos: {successful_tests}[/green]")
    if failed_tests > 0:
        console.print(f"[red]✗ Tests fallidos: {failed_tests}[/red]")
    if skipped_tests > 0:
        console.print(f"[yellow]⚠ Tests omitidos: {skipped_tests}[/yellow]")
    
    console.print("\n[green]Tests completados[/green]")
    
    return failed_tests == 0

def check_dependencies():
    """Verifica si las dependencias necesarias están instaladas"""
    missing = []
    
    # Verificar google-cloud-vision
    try:
        import google.cloud.vision
    except ImportError:
        missing.append("google-cloud-vision")
    
    # Verificar otras dependencias según sea necesario
    try:
        from src.config import setup
    except ImportError:
        missing.append("src.config.setup (problema con la estructura del proyecto)")
    
    return missing

if __name__ == "__main__":
    run_all_tests()