from typing import Dict, Any
import asyncio
from ..services.video.video_processor import VideoProcessor
from ..services.youtube.youtube_service import YouTubeService

class ProcessorQueue:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.youtube_service = YouTubeService()

    async def add_task(self, url: str) -> str:
        video_path = await self.youtube_service.download_video(url)
        await self.queue.put(video_path)
        return video_path

    async def process_queue(self):
        while True:
            video_path = await self.queue.get()
            try:
                processor = VideoProcessor(video_path, "./output")
                result = await processor.process_video()
                # Aquí podrías guardar el resultado en base de datos
                print(f"Procesado: {result}")
            except Exception as e:
                print(f"Error: {e}")
            finally:
                self.queue.task_done()