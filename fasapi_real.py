from fastapi import FastAPI, HTTPException, Security, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security.api_key import APIKeyHeader
from pydantic import BaseModel, HttpUrl
from google.cloud import speech_v1
import os
import yt_dlp
import tempfile
import moviepy.editor as mp
import asyncio
from datetime import timedelta

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security configuration
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=True)

class VideoRequest(BaseModel):
    url: HttpUrl

async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == os.getenv("API_KEY"):
        return api_key_header
    raise HTTPException(status_code=403, detail="Invalid API Key")

class SubtitleEntry(BaseModel):
    start_time: str
    end_time: str
    text: str

def download_video(url):
    ydl_opts = {
        'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
        'outtmpl': '%(title)s.%(ext)s',
        'nooverwrites': True,
        'no_color': True,
        'quiet': True
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=True)
        video_path = ydl.prepare_filename(info_dict)
        return video_path

@app.post("/process-video-url/")
async def process_video_url(
    video_request: VideoRequest, 
    api_key: str = Depends(get_api_key)
):
    try:
        # Download video
        video_path = download_video(str(video_request.url))
        
        # Extract audio
        video = mp.VideoFileClip(video_path)
        audio_path = tempfile.mktemp(suffix=".wav")
        video.audio.write_audiofile(audio_path)
        
        # Prepare Google Speech-to-Text client
        speech_client = speech_v1.SpeechClient()
        
        # Read audio file
        with open(audio_path, "rb") as audio_file:
            content = audio_file.read()
        
        audio = speech_v1.RecognitionAudio(content=content)
        config = speech_v1.RecognitionConfig(
            encoding=speech_v1.RecognitionConfig.AudioEncoding.LINEAR16,
            language_code="es-ES",
            enable_word_time_offsets=True,
        )
        
        # Perform speech recognition
        operation = speech_client.long_running_recognize(config=config, audio=audio)
        response = operation.result()
        
        # Process subtitles
        subtitles = []
        for result in response.results:
            for word_info in result.alternatives[0].words:
                start_time = word_info.start_time.total_seconds()
                end_time = word_info.end_time.total_seconds()
                
                subtitle = SubtitleEntry(
                    start_time=str(timedelta(seconds=int(start_time))),
                    end_time=str(timedelta(seconds=int(end_time))),
                    text=word_info.word
                )
                subtitles.append(subtitle)
        
        # Clean up temporary files
        os.remove(video_path)
        os.remove(audio_path)
        
        return {
            "subtitles": subtitles,
            "video_title": video.filename
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health/")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)