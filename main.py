import os
import sys
import logging

# Configurar logging más detallado
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Crear directorios necesarios
os.makedirs("data/raw/test123", exist_ok=True)
os.makedirs("data/transcripts", exist_ok=True)
os.makedirs("data/audio", exist_ok=True)
os.makedirs("data/processed/test123", exist_ok=True)

# Asegurarnos que la carpeta raíz está en el path de Python
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse


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
    print("\n" + "="*50)
    print(" MIRESSE - Herramienta de Audiodescripciones y Subtítulos")
    print("="*50)
    print("\n La aplicación está iniciando...")
    print("La interfaz web estará disponible en: http://localhost:8000")
    print(" La API estará disponible en: http://localhost:8000/api/v1")
    print(" La documentación estará disponible en: http://localhost:8000/docs")
    
    # Mostrar estado de características principales
    print("\nEstado del sistema:")
    print(f"📂 Directorio de datos: {settings.DATA_DIR}")
    print(f" Idioma configurado: {settings.LANGUAGE_CODE}")
    print(f" Funciones de IA: {'Habilitadas' if hasattr(settings, 'ai_features_enabled') and settings.ai_features_enabled else 'Deshabilitadas'}")
    
    print("\n⚠️ Para detener el servidor, presiona CTRL+C")
    print("="*50 + "\n")
    
    uvicorn.run(
        "main:app", 
        host="localhost", 
        port=8000, 
        reload=False,  # Desactivar reload para reducir consumo
        workers=1,     # Usar solo un worker
        log_level="warning"  # Reducir logging
    )