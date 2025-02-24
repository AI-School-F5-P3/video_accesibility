# API Endpoints

## POST /api/v1/process
Procesa un video para añadir características de accesibilidad.

### Request
```json
{
    "url": "string",
    "service_type": "AUDIODESCRIPCION | SUBTITULADO",
    "config": {
        "language": "es",
        "quality": "high"
    }
}