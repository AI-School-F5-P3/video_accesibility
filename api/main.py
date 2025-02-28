from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.config.setup import Settings 
from api.endpoints import video, subtitle, audiodesc

settings = Settings()

app = FastAPI(
    title="Audiodescription Generator",
    description="API for generating audio descriptions and subtitles for videos",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="front"), name="static")

# Include routers
app.include_router(video.router, prefix="/api/v1/videos", tags=["videos"])
app.include_router(subtitle.router, prefix="/api/v1/subtitles", tags=["subtitles"])
app.include_router(audiodesc.router, prefix="/api/v1/audiodesc", tags=["audiodescriptions"])

@app.get("/")
async def root():
    return {"message": "Welcome to Miresse API"}