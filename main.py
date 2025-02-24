
import os
import sys

# Asegurarnos que la carpeta raíz está en el path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ajustar el import al archivo correcto
from src.config.setup import Settings
from api.endpoints import video, subtitle, audiodesc

settings = Settings()

app = FastAPI(
    title="MIRESSE - Accesibilidad",
    description="API para generar audiodescripciones y subtítulos para videos",
    version="1.0.0"
)

# Configuración CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Montar archivos estáticos
app.mount("/static", StaticFiles(directory="front"), name="static")

# Incluir routers
app.include_router(video.router, prefix="/api/v1/videos", tags=["videos"])
app.include_router(subtitle.router, prefix="/api/v1/subtitles", tags=["subtitles"])
app.include_router(audiodesc.router, prefix="/api/v1/audiodesc", tags=["audiodescriptions"])

@app.get("/")
async def root():
    return {"message": "MIRESSE API funcionando correctamente. Visita /docs para ver la documentación."}

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)