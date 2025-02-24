# Video Accessibility Project

## Estructura del Proyecto
```
├── frontend/           # Aplicación cliente (React/TypeScript)
├── backend/           # Servidor API (Node.js/Express)
├── services/         # Servicios de procesamiento de video
├── config/           # Configuraciones y variables de entorno
└── docs/            # Documentación adicional
```

## Requisitos
- Node.js >= 16.x
- Python 3.11+
- Google Cloud SDK
- FFmpeg
- OpenCV
- Google Cloud Platform credentials
- YouTube API key

## Configuración
1. Configurar credenciales de Google Cloud:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

2. Crear archivo `.env`:
```bash
GOOGLE_CLOUD_PROJECT=your-project-id
VERTEX_LOCATION=us-central1
YOUTUBE_API_KEY=your-youtube-api-key
```

3. Instalar dependencias:
```bash
npm install   # Frontend y Backend
pip install -r requirements.txt  # Servicios Python
```

## APIs y Servicios Requeridos
- YouTube Data API v3
- Vision AI
- Vertex AI
- Speech-to-Text
- Google AI Studio

## Estándares Implementados
- UNE 153020 (Audiodescripción)
- UNE 153010 (Subtitulado)
