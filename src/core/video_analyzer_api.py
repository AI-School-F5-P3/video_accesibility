import os
from dotenv import load_dotenv
import tempfile
import cv2
import numpy as np
import yt_dlp
from typing import List, Dict, Optional
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Cargar variables de entorno
load_dotenv()

# Obtener API Key desde .env
API_KEY = os.getenv('YOUTUBE_API_KEY')
if not API_KEY:
    raise ValueError("YOUTUBE_API_KEY no encontrada en el archivo .env")

class YouTubeAPI:
    """Maneja la autenticación de la API de YouTube y la obtención de videos"""

    def __init__(self):
        try:
            self.service = self.authenticate()
        except Exception as e:
            raise ValueError(f"Error en la autenticación de YouTube API: {e}")

    def authenticate(self):
        """Autenticación usando la API Key"""
        try:
            return build("youtube", "v3", developerKey=API_KEY)
        except Exception as e:
            raise ValueError(f"Error en la construcción del servicio de YouTube: {e}")

    def get_uploaded_videos(self, channel_id: str) -> List[Dict]:
        """Obtiene los videos de un canal público"""
        try:
            # Verificar que el channel_id no esté vacío
            if not channel_id:
                raise ValueError("El ID del canal no puede estar vacío")

            # Obtener detalles del canal
            playlist_request = self.service.channels().list(
                part="contentDetails",
                id=channel_id
            )
            playlist_response = playlist_request.execute()

            # Verificar si se encontró el canal
            if not playlist_response.get("items"):
                raise ValueError(f"No se encontró el canal con ID: {channel_id}")

            # Obtener la lista de videos subidos
            playlist_id = playlist_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            video_request = self.service.playlistItems().list(
                part="snippet",
                playlistId=playlist_id,
                maxResults=10
            )
            video_response = video_request.execute()

            return [
                {
                    "title": v["snippet"]["title"],
                    "video_id": v["snippet"]["resourceId"]["videoId"],
                    "thumbnail": v["snippet"]["thumbnails"]["high"]["url"],
                    "description": v["snippet"].get("description", ""),
                    "published_at": v["snippet"]["publishedAt"]
                }
                for v in video_response.get("items", [])
            ]
        except HttpError as e:
            if "API key not valid" in str(e):
                raise ValueError("La API key no es válida. Verifica tu archivo .env")
            raise ValueError(f"Error al obtener videos: {e}")
        except Exception as e:
            raise ValueError(f"Error inesperado: {e}")

class VideoDownloader:
    """Maneja la descarga de videos de YouTube usando yt-dlp"""

    def __init__(self, video_id: str):
        if not video_id:
            raise ValueError("El ID del video no puede estar vacío")
        self.video_id = video_id
        self.video_path = os.path.join(tempfile.gettempdir(), f"{video_id}.mp4")

    def download_video(self) -> str:
        """Descarga el video y devuelve la ruta del archivo"""
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "outtmpl": self.video_path,
            "quiet": True
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={self.video_id}"])
            if not os.path.exists(self.video_path):
                raise FileNotFoundError("El video no se descargó correctamente")
            return self.video_path
        except Exception as e:
            raise ValueError(f"Error al descargar el video: {e}")

class VideoProcessor:
    """Procesa los frames del video y detecta cambios de escena"""

    @staticmethod
    def extract_frames(video_path: str, interval: int = 5) -> List[np.ndarray]:
        """Extrae frames cada X segundos"""
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"No se encontró el archivo de video: {video_path}")

        frames = []
        video = cv2.VideoCapture(video_path)
        
        if not video.isOpened():
            raise ValueError("No se pudo abrir el video")

        fps = video.get(cv2.CAP_PROP_FPS) or 30
        frame_interval = int(fps * interval)

        try:
            frame_count = 0
            while True:
                ret, frame = video.read()
                if not ret:
                    break
                if frame_count % frame_interval == 0:
                    frames.append(frame)
                frame_count += 1
        finally:
            video.release()

        return frames

    @staticmethod
    def detect_scene_changes(frames: List[np.ndarray], threshold: float = 0.1) -> List[int]:
        """Detecta cambios de escena basados en las diferencias entre los frames"""
        if not frames:
            return []

        scene_changes = []
        for i in range(1, len(frames)):
            try:
                diff = cv2.absdiff(
                    cv2.cvtColor(frames[i-1], cv2.COLOR_BGR2GRAY),
                    cv2.cvtColor(frames[i], cv2.COLOR_BGR2GRAY)
                )
                if np.mean(diff) > (threshold * 255):
                    scene_changes.append(i)
            except Exception as e:
                print(f"Error al procesar frames {i-1} y {i}: {e}")
                continue

        return scene_changes

class YouTubeVideoManager:
    """Gestiona la selección, descarga y procesamiento de videos"""

    def __init__(self):
        try:
            self.youtube_api = YouTubeAPI()
            self.selected_video = None
        except Exception as e:
            raise ValueError(f"Error al inicializar YouTubeVideoManager: {e}")

    def select_video(self, channel_id: str) -> Optional[Dict]:
        """Muestra los videos del canal público y permite seleccionar uno"""
        try:
            videos = self.youtube_api.get_uploaded_videos(channel_id)
            if not videos:
                print("No se encontraron videos en el canal.")
                return None

            print("\nVideos disponibles:")
            for i, v in enumerate(videos, 1):
                print(f"{i}. {v['title']} (ID: {v['video_id']})")
                print(f"   Publicado: {v['published_at']}")
                print(f"   {v['description'][:100]}..." if v['description'] else "   Sin descripción")
                print()

            while True:
                try:
                    choice = input("Selecciona un video (número) o 'q' para salir: ")
                    if choice.lower() == 'q':
                        return None
                    
                    choice_idx = int(choice) - 1
                    if 0 <= choice_idx < len(videos):
                        self.selected_video = videos[choice_idx]
                        return self.selected_video
                    else:
                        print("Número inválido. Intenta de nuevo.")
                except ValueError:
                    print("Por favor, ingresa un número válido.")

        except Exception as e:
            print(f"Error al seleccionar video: {e}")
            return None

    def process_selected_video(self):
        """Descarga y procesa el video seleccionado"""
        if not self.selected_video:
            print("No hay ningún video seleccionado.")
            return

        try:
            print(f"\nProcesando video: {self.selected_video['title']}")
            
            # Descargar video
            print("Descargando video...")
            downloader = VideoDownloader(self.selected_video["video_id"])
            video_path = downloader.download_video()

            # Procesar frames
            print("Extrayendo frames...")
            frames = VideoProcessor.extract_frames(video_path)
            
            print("Detectando cambios de escena...")
            scene_changes = VideoProcessor.detect_scene_changes(frames)

            # Mostrar resultados
            print("\n📊 Análisis del Video:")
            print(f"🎥 Título: {self.selected_video['title']}")
            print(f"🎬 Frames extraídos: {len(frames)}")
            print(f"🔄 Cambios de escena detectados: {len(scene_changes)}")
            
            if scene_changes:
                print("\nMomentos de cambio de escena (índices de frames):")
                print(", ".join(map(str, scene_changes)))

        except Exception as e:
            print(f"Error durante el procesamiento del video: {e}")
        finally:
            # Limpieza
            if 'video_path' in locals() and os.path.exists(video_path):
                try:
                    os.remove(video_path)
                    print("\n🧹 Archivo temporal eliminado correctamente")
                except Exception as e:
                    print(f"\n⚠️ Error al eliminar archivo temporal: {e}")

def main():
    try:
        print("🎥 Iniciando YouTube Video Analyzer...")
        manager = YouTubeVideoManager()

        while True:
            channel_id = input("\nIngresa el ID del canal de YouTube (o 'q' para salir): ")
            if channel_id.lower() == 'q':
                break

            if manager.select_video(channel_id):
                manager.process_selected_video()

        print("\n👋 ¡Gracias por usar YouTube Video Analyzer!")

    except Exception as e:
        print(f"\n❌ Error fatal: {e}")
        print("Por favor, verifica tu archivo .env y tu conexión a internet")

if __name__ == "__main__":
    main()