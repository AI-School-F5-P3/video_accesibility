import asyncio
import httpx
import time
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

# Configuración base
BASE_URL = "http://localhost:8000/api/v1"
TEST_VIDEO_URL = "https://www.youtube.com/watch?v=YOUR_TEST_VIDEO_ID"  # Cambiar por una URL real

async def test_video_processing():
    """Prueba el proceso completo de procesamiento de video"""
    async with httpx.AsyncClient() as client:
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
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

                # 2. Esperar y monitorear el estado del procesamiento
                processing_task = progress.add_task("Monitorizando procesamiento...", total=None)
                while True:
                    status_response = await client.get(f"{BASE_URL}/videos/{video_id}/status")
                    status = status_response.json()
                    
                    if status["status"] == "completed":
                        console.print(f"\n[green]✓[/green] Procesamiento completado")
                        break
                    elif status["status"] == "error":
                        raise Exception(f"Error en procesamiento: {status['error']}")
                    
                    progress.update(processing_task, description=f"Estado: {status['current_step']}")
                    await asyncio.sleep(5)

                # 3. Obtener resultados
                progress.add_task("Obteniendo resultados...", total=None)
                results = await client.get(f"{BASE_URL}/videos/{video_id}/result")
                results_data = results.json()
                console.print("\n[bold]Resultados del procesamiento:[/bold]")
                console.print(results_data)

                # 4. Probar obtención de subtítulos
                if "subtitles" in results_data["outputs"]:
                    progress.add_task("Probando acceso a subtítulos...", total=None)
                    subtitle_response = await client.get(
                        f"{BASE_URL}/subtitles/{video_id}",
                        params={"format": "srt"}
                    )
                    subtitle_data = subtitle_response.json()
                    console.print("\n[bold]Preview de subtítulos:[/bold]")
                    for segment in subtitle_data["segments"][:3]:
                        console.print(f"[{segment['start']} -> {segment['end']}] {segment['text']}")

                # 5. Probar obtención de audiodescripción
                if "audio_description" in results_data["outputs"]:
                    progress.add_task("Probando acceso a audiodescripción...", total=None)
                    audiodesc_response = await client.get(
                        f"{BASE_URL}/audiodesc/{video_id}",
                        params={"format": "json"}
                    )
                    audiodesc_data = audiodesc_response.json()
                    console.print("\n[bold]Preview de audiodescripción:[/bold]")
                    for desc in audiodesc_data["descriptions"][:3]:
                        console.print(f"[{desc['start_time']}ms] {desc['text']}")

                console.print("\n[green]✓[/green] Todas las pruebas completadas exitosamente")

        except httpx.HTTPError as e:
            console.print(f"\n[red]✗[/red] Error en la petición HTTP: {str(e)}")
        except Exception as e:
            console.print(f"\n[red]✗[/red] Error inesperado: {str(e)}")

async def test_individual_endpoints():
    """Prueba endpoints individuales"""
    async with httpx.AsyncClient() as client:
        try:
            console.print("\n[bold]Probando endpoints individuales:[/bold]")

            # 1. Probar estado de un video no existente
            response = await client.get(f"{BASE_URL}/videos/nonexistent/status")
            console.print(f"Estado de video no existente: {response.status_code}")

            # 2. Probar formato de subtítulos inválido
            response = await client.get(
                f"{BASE_URL}/subtitles/test",
                params={"format": "invalid"}
            )
            console.print(f"Formato de subtítulos inválido: {response.status_code}")

            # 3. Probar actualización de segmento de subtítulos
            response = await client.put(
                f"{BASE_URL}/subtitles/test/segments/1",
                json={"text": "Texto de prueba"}
            )
            console.print(f"Actualización de subtítulos: {response.status_code}")

        except Exception as e:
            console.print(f"[red]✗[/red] Error en pruebas individuales: {str(e)}")

if __name__ == "__main__":
    # Instalar dependencias si no están instaladas:
    # pip install httpx rich

    console.print("[bold]Iniciando pruebas de la API...[/bold]")
    
    asyncio.run(test_video_processing())
    asyncio.run(test_individual_endpoints())