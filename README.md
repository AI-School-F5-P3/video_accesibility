# Sistema de Accesibilidad de Video

## Estructura del Proyecto
```
├── frontend/           # Aplicación cliente (React/TypeScript)
├── backend/           # Servidor API (Node.js/Express)
├── services/         # Servicios de procesamiento de video
├── config/           # Configuraciones y variables de entorno
└── docs/            # Documentación adicional
```

## Requisitos Previos
- Node.js >= 16.x
- Python >= 3.8
- Google Cloud SDK
- FFmpeg

## Configuración
1. Configurar credenciales de Google Cloud:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"
```

2. Instalar dependencias:
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
