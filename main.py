import os
import sys
import logging

# Reducir el nivel de logging
logging.basicConfig(level=logging.WARNING)

# Asegurarnos que la carpeta raíz está en el path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Ajustar el import al archivo correcto
from src.config.setup import Settings
from api.endpoints import video, subtitle, audiodesc

settings = Settings()

# Aplicación con opciones mínimas
app = FastAPI(
    title="MIRESSE",
    docs_url=None,  # Desactivar Swagger que consume recursos
    redoc_url="/docs"  # Usar ReDoc que es más ligero
)

# Configuración CORS mínima
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    # Devolver el archivo HTML del frontend
    return FileResponse("front/index.html")

# Punto de entrada para ejecución directa
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="localhost", 
        port=8000, 
        reload=False,  # Desactivar reload para reducir consumo
        workers=1,     # Usar solo un worker
        log_level="warning"  # Reducir logging
    )