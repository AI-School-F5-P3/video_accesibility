import asyncio
import httpx
import time
from pathlib import Path
import sys
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

# Añadir el directorio raíz al path
current_dir = Path(__file__).parent
root_dir = current_dir.parent
sys.path.insert(0, str(root_dir))

console = Console()

# Configuración base
BASE_URL = "http://localhost:8000/api/v1"
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=YOUR_TEST_VIDEO_ID"  # Cambiar por una URL real

async def test_video_processing():
    """Prueba el proceso completo de procesamiento de video"""
    # Configurar timeout más largo para evitar fallos prematuros
    timeout = httpx.Timeout(60.0, connect=10.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                # Verificar primero que el servidor esté en funcionamiento
                try:
                    health_check = await client.get(f"{BASE_URL}/health", timeout=5.0)
                    if health_check.status_code != 200:
                        console.print("[yellow]⚠️ El servidor API no parece estar respondiendo correctamente[/yellow]")
                except Exception:
                    console.print("[yellow]⚠️ No se puede conectar al servidor API. ¿Está corriendo la aplicación?[/yellow]")
                    return False
                
                # 1. Iniciar procesamiento del video
                progress.add_task("Iniciando procesamiento de video...", total=None)
                response = await client.post(
                    f"{BASE_URL}/videos/process",
                    data={
                        "youtube_url": TEST_VIDEO_URL,
                        "generate_audiodesc": True,
                        "generate_subtitles": True,
                        "voice_type": "es-ES-F",
                        "subtitle_format": "srt",
                        "output_quality": "high",
                        "target_language": "es"
                    }
                )
                response.raise_for_status()
                data = response.json()
                video_id = data["video_id"]
                console.print(f"\n[green]✓[/green] Procesamiento iniciado. Video ID: {video_id}")

                # Resto del código como antes...
                
        except httpx.HTTPError as e:
            console.print(f"\n[red]✗[/red] Error en la petición HTTP: {str(e)}")
            return False
        except Exception as e:
            console.print(f"\n[red]✗[/red] Error inesperado: {str(e)}")
            return False
        
        return True

async def test_individual_endpoints():
    """Prueba endpoints individuales"""
    # Configurar timeout más corto para estas pruebas
    timeout = httpx.Timeout(5.0)
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            console.print("\n[bold]Probando endpoints individuales:[/bold]")

            # Verificar primero que el servidor esté en funcionamiento
            try:
                health_check = await client.get(f"{BASE_URL}/health", timeout=2.0)
                if health_check.status_code != 200:
                    console.print("[yellow]⚠️ El servidor API no parece estar respondiendo correctamente[/yellow]")
                    return False
            except Exception:
                console.print("[yellow]⚠️ No se puede conectar al servidor API. ¿Está corriendo la aplicación?[/yellow]")
                return False
            
            # Resto del código como antes...
                
        except Exception as e:
            console.print(f"[red]✗[/red] Error en pruebas individuales: {str(e)}")
            return False
        
        return True

if __name__ == "__main__":
    console.print("[bold]Iniciando pruebas de la API...[/bold]")
    
    try:
        asyncio.run(test_video_processing())
        asyncio.run(test_individual_endpoints())
    except KeyboardInterrupt:
        console.print("[yellow]Pruebas canceladas por el usuario[/yellow]")
    except Exception as e:
        console.print(f"[red]Error durante la ejecución de pruebas: {str(e)}[/red]")