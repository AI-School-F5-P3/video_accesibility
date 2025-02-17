iimport os
import json
import tempfile
import logging
import cv2
import numpy as np
import yt_dlp
import io
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from dotenv import load_dotenv
from PIL import Image
from google.cloud import vision
import google.generativeai as genai
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Cargar variables de entorno
load_dotenv()
API_KEY = os.getenv('YOUTUBE_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not API_KEY:
    raise ValueError("YOUTUBE_API_KEY no encontrada en el archivo .env")

if not GEMINI_API_KEY:
    logging.warning("GEMINI_API_KEY no encontrada en el archivo .env")

genai.configure(api_key=GEMINI_API_KEY)

# YouTube API
class YouTubeAPI:
    def __init__(self):
        try:
            self.service = build("youtube", "v3", developerKey=API_KEY)
        except Exception as e:
            raise ValueError(f"Error en la autenticación de YouTube API: {e}")

    def get_uploaded_videos(self, channel_id: str) -> List[Dict]:
        try:
            playlist_request = self.service.channels().list(part="contentDetails", id=channel_id)
            playlist_response = playlist_request.execute()
            if not playlist_response.get("items"):
                raise ValueError(f"No se encontró el canal con ID: {channel_id}")

            playlist_id = playlist_response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
            video_request = self.service.playlistItems().list(part="snippet", playlistId=playlist_id, maxResults=10)
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
        except Exception as e:
            raise ValueError(f"Error al obtener videos: {e}")

# Descarga de videos
class VideoDownloader:
    def __init__(self, video_id: str):
        self.video_id = video_id
        self.video_path = os.path.join(tempfile.gettempdir(), f"{video_id}.mp4")

    def download_video(self) -> str:
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]",
            "outtmpl": self.video_path,
            "quiet": True
        }
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([f"https://www.youtube.com/watch?v={self.video_id}"])
            return self.video_path
        except Exception as e:
            raise ValueError(f"Error al descargar el video: {e}")

# Procesamiento de video
class VideoProcessor:
    @staticmethod
    def extract_frames(video_path: str, interval: int = 5) -> List[np.ndarray]:
        frames = []
        video = cv2.VideoCapture(video_path)
        if not video.isOpened():
            raise ValueError("No se pudo abrir el video")
        fps = video.get(cv2.CAP_PROP_FPS) or 30
        frame_interval = int(fps * interval)
        frame_count = 0
        while True:
            ret, frame = video.read()
            if not ret:
                break
            if frame_count % frame_interval == 0:
                frames.append(frame)
            frame_count += 1
        video.release()
        return frames

# Análisis de frames con Google Vision API
class GoogleCloudFrameAnalyzer:
    def __init__(self):
        self.client = vision.ImageAnnotatorClient()

    def analyze_frame(self, frame: np.ndarray) -> Dict:
        _, encoded_image = cv2.imencode('.jpg', frame)
        image = vision.Image(content=encoded_image.tobytes())
        response = self.client.annotate_image({
            'image': image,
            'features': [
                {'type_': vision.Feature.Type.OBJECT_LOCALIZATION},
                {'type_': vision.Feature.Type.LABEL_DETECTION},
                {'type_': vision.Feature.Type.TEXT_DETECTION},
            ]
        })
        return {
            'objects': [obj.name for obj in response.localized_object_annotations],
            'labels': [label.description for label in response.label_annotations],
            'text': response.text_annotations[0].description if response.text_annotations else ''
        }

# Análisis de frames con Gemini Vision
class GeminiFrameAnalyzer:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-pro-vision')

    def analyze_frame(self, frame: np.ndarray) -> Dict:
        _, encoded_image = cv2.imencode('.jpg', frame)
        image = Image.open(io.BytesIO(encoded_image.tobytes()))
        prompt = """Describe la escena del video detalladamente."""
        response = self.model.generate_content([prompt, image])
        return {'description': response.text}

# Gestor principal de YouTube Video Analyzer
class YouTubeVideoManager:
    def __init__(self):
        self.youtube_api = YouTubeAPI()
        self.selected_video = None

    def select_video(self, channel_id: str) -> Optional[Dict]:
        videos = self.youtube_api.get_uploaded_videos(channel_id)
        if not videos:
            return None
        self.selected_video = videos[0]  # Seleccionar el primer video por simplicidad
        return self.selected_video

    def process_selected_video(self):
        if not self.selected_video:
            print("No hay video seleccionado.")
            return
        downloader = VideoDownloader(self.selected_video["video_id"])
        video_path = downloader.download_video()
        frames = VideoProcessor.extract_frames(video_path)
        analyzer = GoogleCloudFrameAnalyzer() if API_KEY else GeminiFrameAnalyzer()
        results = [analyzer.analyze_frame(frame) for frame in frames]
        with open("video_analysis.json", "w") as f:
            json.dump(results, f, indent=2)
        os.remove(video_path)

if __name__ == "__main__":
    manager = YouTubeVideoManager()
    channel_id = input("Ingresa el ID del canal de YouTube: ")
    if manager.select_video(channel_id):
        manager.process_selected_video()
        print("Análisis completado.")