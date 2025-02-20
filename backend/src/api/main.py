from fastapi import FastAPI, BackgroundTasks
from ..queue.processor_queue import ProcessorQueue

app = FastAPI()
processor_queue = ProcessorQueue()

@app.post("/process-video")
async def process_video(url: str, background_tasks: BackgroundTasks):
    video_path = await processor_queue.add_task(url)
    background_tasks.add_task(processor_queue.process_queue)
    return {"status": "processing", "video_path": video_path}