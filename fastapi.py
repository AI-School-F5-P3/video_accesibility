from fastapi import FastAPI, UploadFile, File, HTTPException, Security, Depends
from fastapi.security.api_key import APIKeyHeader
from fastapi.middleware.cors import CORSMiddleware
from google.cloud import speech_v1
from google.cloud import storage
import os
import json
import moviepy.editor as mp
from pydantic import BaseModel
import asyncio
from typing import List
import datetime

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Update with your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == os.getenv("API_KEY"):
        return api_key_header
    raise HTTPException(status_code=403, detail="Invalid API Key")

class SubtitleEntry(BaseModel):
    start_time: str
    end_time: str
    text: str

# Initialize Google Cloud clients
speech_client = speech_v1.SpeechClient()
storage_client = storage.Client()

@app.post("/upload-video/")
async def upload_video(
    file: UploadFile = File(...),
    api_key: str = Depends(get_api_key)
):
    try:
        # Save uploaded video temporarily
        temp_video_path = f"temp_{file.filename}"
        with open(temp_video_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Extract audio from video
        video = mp.VideoFileClip(temp_video_path)
        temp_audio_path = "temp_audio.wav"
        video.audio.write_audiofile(temp_audio_path)
        
        # Prepare audio for Google Speech-to-Text
        with open(temp_audio_path, "rb") as audio_file:
            content = audio_file.read()
        
        audio = speech_v1.RecognitionAudio(content=content)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="es-ES",  # Update based on your needs
            enable_word_time_offsets=True,
        )
        
        # Perform speech recognition
        operation = speech_client.long_running_recognize(config=config, audio=audio)
        response = operation.result()
        
        # Process results into subtitles
        subtitles = []
        for result in response.results:
            for word_info in result.alternatives[0].words:
                start_time = word_info.start_time.total_seconds()
                end_time = word_info.end_time.total_seconds()
                
                subtitle = SubtitleEntry(
                    start_time=str(datetime.timedelta(seconds=int(start_time))),
                    end_time=str(datetime.timedelta(seconds=int(end_time))),
                    text=word_info.word
                )
                subtitles.append(subtitle)
        
        # Clean up temporary files
        os.remove(temp_video_path)
        os.remove(temp_audio_path)
        
        return {"subtitles": subtitles}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0000", port=8000)