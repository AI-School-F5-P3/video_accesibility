# Documentación del Proyecto de Audiodescripciones y Subtítulos

## 1. Introducción

### 1.1 Propósito del Proyecto
Este proyecto tiene como objetivo desarrollar un sistema integral para la creación, gestión y distribución de audiodescripciones y subtítulos para contenido audiovisual, con el fin de mejorar la accesibilidad para personas con discapacidades visuales y auditivas.

### 1.2 Alcance
El sistema abarcará desde la generación de audiodescripciones y subtítulos (manual y asistida por IA), hasta su integración en diferentes plataformas de distribución de contenido audiovisual, cumpliendo con los estándares internacionales de accesibilidad.

### 1.3 Público Objetivo
- Personas con discapacidad visual
- Personas con discapacidad auditiva
- Creadores de contenido audiovisual
- Plataformas de streaming y distribución de contenido
- Instituciones educativas y culturales

## 2. Requisitos del Sistema

### 2.1 Requisitos Funcionales

#### 2.1.1 Generación de Audiodescripciones
- Detección automática de escenas que requieren audiodescripción
- Interfaz para la creación y edición manual de audiodescripciones
- Sistema de síntesis de voz de alta calidad con múltiples idiomas
- Sincronización precisa con el contenido visual

#### 2.1.2 Generación de Subtítulos
- Transcripción automática del audio con reconocimiento de múltiples idiomas
- Interfaz para edición y corrección manual de subtítulos
- Soporte para subtítulos SDH (Subtítulos para Sordos y personas con Dificultades Auditivas)
- Sincronización precisa con el audio original

#### 2.1.3 Gestión de Contenido
- Biblioteca centralizada de audiodescripciones y subtítulos
- Sistema de versionado para diferentes idiomas y formatos
- Herramientas de control de calidad automatizadas
- Gestión de derechos y licencias

#### 2.1.4 Distribución
- Exportación en formatos estándar (SRT, VTT, TTML, etc.)
- API para integración con plataformas de streaming
- Sistema de entrega bajo demanda
- Monitorización de uso y retroalimentación

### 2.2 Requisitos No Funcionales

#### 2.2.1 Usabilidad
- Interfaz accesible según WCAG 2.1 nivel AAA
- Flujo de trabajo intuitivo para creadores de contenido
- Documentación completa y tutoriales interactivos
- Soporte multilingüe en la interfaz

#### 2.2.2 Rendimiento
- Procesamiento en tiempo real para archivos de hasta 2 horas
- Capacidad para manejar múltiples formatos de video
- Escalabilidad para procesar lotes de contenido
- Optimización para diferentes dispositivos y anchos de banda

#### 2.2.3 Seguridad
- Protección de contenido con copyright
- Gestión de usuarios y permisos
- Cumplimiento con regulaciones de privacidad (GDPR, CCPA)
- Auditoría de acceso y modificaciones

#### 2.2.4 Compatibilidad
- Soporte para principales navegadores y sistemas operativos
- Compatibilidad con reproductores de video estándar
- Integración con software de edición profesional
- Adaptabilidad a diferentes resoluciones de pantalla

## 3. Arquitectura del Sistema

### 3.1 Diagrama de Arquitectura General
[Incluir diagrama de arquitectura]

### 3.2 Componentes Principales

#### 3.2.1 Módulo de Análisis de Video (`src/core/video_analyzer.py`)
- Detección de escenas con SceneDetect
- Análisis de contenido visual
- Identificación de espacios para audiodescripciones
- Extracción de frames clave para procesamiento

#### 3.2.2 Módulo de Procesamiento de Audio (`src/core/audio_processor.py`)
- Extracción de audio de videos
- Análisis de calidad de audio con Librosa
- Preprocesamiento para reconocimiento de voz

#### 3.2.3 Módulo de Procesamiento de Voz (`src/core/speech_processor.py`)
- Transcripción automática con Whisper OpenAI
- Síntesis de voz con Coqui TTS y Google TTS
- Generación de audiodescripciones narradas

#### 3.2.4 Módulo de Procesamiento de Texto (`src/core/text_processor.py`)
- Formateo de subtítulos y audiodescripciones
- Procesamiento de texto para síntesis de voz
- Adaptación de contenido a estándares de accesibilidad

#### 3.2.5 API FastAPI (`api/`)
- RESTful API para todas las funcionalidades
- Endpoints para procesamiento de video, audiodescripciones y subtítulos
- Documentación automática con Swagger/OpenAPI

#### 3.2.6 Servicios de Integración (`src/services/`)
- Servicio de subtítulos (`subtitle_service.py`)
- Servicio de video (`video_service.py`)
- Orquestación de procesos y flujos de trabajo

#### 3.2.7 Interfaz Web (`front/`)
- Interfaz simple basada en HTML/CSS/JavaScript
- Componentes para procesamiento de video
- Visualización y edición de resultados

### 3.3 Flujo de Datos
- Ingesta de video → Almacenamiento en `data/raw/[uuid]/` → Análisis de video con `video_analyzer.py` → Extracción de frames clave en `data/processed/[uuid]/` → Detección de escenas
- Extracción de audio → Procesamiento con `audio_processor.py` → Transcripción con Whisper y `speech_processor.py` → Generación de subtítulos en `data/transcripts/[uuid]_srt.srt`
- Análisis de escenas → Generación de descripciones → Síntesis de voz → Integración de audiodescripciones
- Llamadas a API → Procesamiento por servicios correspondientes → Respuesta con resultados

### 3.4 Integraciones Externas
- Google Cloud Text-to-Speech para síntesis de voz de alta calidad
- OpenAI Whisper para transcripción automática
- FFmpeg para procesamiento de audio y video
- SceneDetect para análisis de escenas
- Servicios de almacenamiento para archivos multimedia

## 4. Modelo de Datos

### 4.1 Entidades Principales
- Video (identificado por UUID)
- Escena (`src/models/scene.py`)
- Transcripción (`src/models/transcript.py`)
- Audiodescripción (almacenada en JSON)
- Frames clave (almacenados como imágenes)

### 4.2 Esquema de Almacenamiento
- `data/raw/[uuid]/[uuid].mp4` - Videos originales
- `data/processed/[uuid]/` - Frames y metadata procesada
- `data/processed/[uuid]/descriptions.json` - Descripciones de escenas
- `data/processed/[uuid]/frame_[n].jpg` - Frames clave extraídos
- `data/transcripts/[uuid]_srt.srt` - Subtítulos generados
- `data/audio/` - Archivos de audio extraídos

### 4.3 Formatos de Archivo
- Formatos de entrada: MP4 y otros formatos de video compatibles con FFmpeg
- Formatos de salida para subtítulos: SRT (principal)
- Formatos de salida para audiodescripciones: WAV, MP3
- Metadatos: JSON para descripciones y configuración

## 5. Interfaz de Usuario

### 5.1 Componentes de la Interfaz
- Página principal (`front/index.html`)
- Estilos CSS (`front/css/styles.css`)
- Lógica JavaScript (`front/js/main.js` y `front/js/video-processor.js`)
- Componente de procesamiento de video (`front/js/components/VideoProcessingComponent.jsx`)

### 5.2 Flujos de Usuario
- Carga de video → Procesamiento automático → Visualización de resultados → Edición manual → Exportación
- Gestión de subtítulos: Visualización → Edición → Sincronización → Guardado
- Gestión de audiodescripciones: Visualización de escenas → Edición de descripciones → Síntesis de voz → Integración

### 5.3 API RESTful
- Endpoints en `api/endpoints/`:
  - `/video` - Gestión de videos y procesamiento
  - `/subtitle` - Generación y manipulación de subtítulos
  - `/audiodesc` - Creación y gestión de audiodescripciones
  - `/dashboard` - Estadísticas y monitorización

## 6. Tecnologías y Stack

### 6.1 Frontend
- HTML/CSS/JavaScript simple
- Componentes JavaScript modulares
- Sin dependencia de frameworks pesados

### 6.2 Backend
- Python 3.9+ como lenguaje principal
- FastAPI para la API RESTful
- Uvicorn como servidor ASGI

### 6.3 Procesamiento Multimedia
- FFmpeg para manipulación de audio/video
- OpenAI Whisper para transcripción automática
- SceneDetect para detección de escenas
- Librosa para análisis de audio
- Coqui TTS y Google TTS para síntesis de voz

### 6.4 IA y ML
- Whisper para reconocimiento automático de voz
- Transformers de Hugging Face para procesamiento de lenguaje
- PyTorch como framework de deep learning
- Google Cloud AI para servicios adicionales

## 7. Estructura de Directorios del Proyecto

```
├── api/                # API FastAPI para todos los endpoints
│   ├── endpoints/      # Endpoints específicos (audiodesc, subtitle, video)
│   │   ├── audiodesc.py
│   │   ├── dashboard.py
│   │   ├── subtitle.py
│   │   └── video.py
│   ├── __init__.py
│   └── main.py         # Configuración principal de la API
├── data/               # Datos y archivos procesados
│   ├── audio/          # Archivos de audio extraídos
│   ├── processed/      # Videos procesados con frames y metadatos
│   │   └── [uuid]/     # Carpeta específica para cada video procesado
│   │       ├── descriptions.json
│   │       └── frame_[n].jpg
│   ├── raw/            # Videos originales sin procesar
│   │   └── [uuid]/     # Carpeta específica para cada video original
│   │       └── [uuid].mp4
│   └── transcripts/    # Subtítulos generados (.srt)
├── docs/               # Documentación
│   ├── UNE153010.md    # Estándar para subtitulado
│   └── UNE153020.md    # Estándar para audiodescripción
├── env/                # Entorno virtual de Python
├── front/              # Interfaz web simple
│   ├── css/
│   │   └── styles.css
│   ├── index.html
│   └── js/
│       ├── components/
│       │   └── VideoProcessingComponent.jsx
│       ├── main.js
│       └── video-processor.js
├── src/                # Código fuente principal
│   ├── config/         # Configuración y credenciales
│   │   ├── credentials/
│   │   │   └── google_credentials.json
│   │   ├── __init__.py
│   │   └── setup.py
│   ├── core/           # Funcionalidades principales
│   │   ├── audio_processor.py    # Procesamiento de audio
│   │   ├── speech_processor.py   # Reconocimiento y síntesis de voz
│   │   ├── text_processor.py     # Procesamiento de texto
│   │   └── video_analyzer.py     # Análisis de video y escenas
│   ├── models/         # Modelos de datos
│   │   ├── scene.py
│   │   └── transcript.py
│   ├── services/       # Servicios de alto nivel
│   │   ├── subtitle_service.py
│   │   └── video_service.py
│   └── utils/          # Utilidades
│       ├── directory_utils.py
│       ├── formatters.py
│       ├── logger.py
│       ├── time_utils.py
│       └── validators.py
├── tests/              # Tests unitarios e integración
├── main.py             # Punto de entrada principal
└── requirements.txt    # Dependencias del proyecto
```

## 8. Desarrollo y Contribución

### 8.1 Configuración del Entorno de Desarrollo
1. Clonar el repositorio
2. Crear un entorno virtual: `python -m venv env`
3. Activar el entorno: `source env/bin/activate` (Linux/Mac) o `env\Scripts\activate` (Windows)
4. Instalar dependencias: `pip install -r requirements.txt`
5. Configurar credenciales de Google Cloud en `src/config/credentials/`
6. Ejecutar la aplicación: `python main.py`

### 8.2 Estructura de Tests
- Tests unitarios en el directorio `tests/`
- Ejecutar tests: `pytest tests/`
- Pruebas específicas por módulo:
  - `test_video_analyzer.py`
  - `test_audio_processor.py`
  - `test_speech_processor.py`
  - `test_subtitles.py`
  - `test_text_processor.py`

### 8.3 Estándares de Código
- Seguir PEP 8 para estilo de código Python
- Documentar funciones y clases con docstrings
- Nombrar variables y funciones en snake_case
- Incluir tests para nuevas funcionalidades
- Validar accesibilidad en componentes de interfaz

## 9. Estándares de Accesibilidad

### 9.1 Cumplimiento con UNE153010
El proyecto sigue el estándar UNE153010 para subtitulado para personas sordas, que incluye:
- Posición y color de los subtítulos según el hablante
- Inclusión de información sonora relevante
- Formato adecuado para efectos sonoros y música
- Velocidad de lectura apropiada
- Ver documentación completa en `docs/UNE153010.md`

### 9.2 Cumplimiento con UNE153020
El proyecto sigue el estándar UNE153020 para audiodescripción, que incluye:
- Inserción en los silencios naturales
- No interferencia con diálogos ni sonidos relevantes
- Uso de vocabulario adecuado y preciso
- Neutralidad en la descripción
- Ver documentación completa en `docs/UNE153020.md`

### 9.3 Conformidad con WCAG
La interfaz web sigue las pautas WCAG 2.1 para asegurar:
- Perceptibilidad
- Operabilidad
- Comprensibilidad
- Robustez

## 10. API de Referencia

### 10.1 Endpoints de Video
```
GET    /api/videos                # Listar todos los videos
POST   /api/videos                # Subir nuevo video
GET    /api/videos/{video_id}     # Obtener información de un video
DELETE /api/videos/{video_id}     # Eliminar un video
POST   /api/videos/{video_id}/process  # Procesar un video
```

### 10.2 Endpoints de Subtítulos
```
GET    /api/subtitles/{video_id}       # Obtener subtítulos
POST   /api/subtitles/{video_id}       # Crear/actualizar subtítulos
GET    /api/subtitles/{video_id}/srt   # Descargar archivo SRT
```

### 10.3 Endpoints de Audiodescripción
```
GET    /api/audiodesc/{video_id}        # Obtener audiodescripciones
POST   /api/audiodesc/{video_id}        # Crear/actualizar audiodescripciones
GET    /api/audiodesc/{video_id}/audio  # Descargar audiodescripción narrada
```

### 10.4 Autenticación y Seguridad
- Autenticación basada en tokens
- Rate limiting para prevenir abuso
- Validación de formatos de archivo

## 11. Ejemplos de Uso

### 11.1 Procesamiento Básico de Video
```python
# Ejemplo de uso de la API para procesar un video
import requests
import json

# Subir un video
files = {'file': open('video.mp4', 'rb')}
response = requests.post('http://localhost:8000/api/videos', files=files)
video_id = response.json()['video_id']

# Procesar el video (generar subtítulos y detectar escenas)
response = requests.post(f'http://localhost:8000/api/videos/{video_id}/process')

# Obtener subtítulos generados
response = requests.get(f'http://localhost:8000/api/subtitles/{video_id}')
subtitles = response.json()

# Obtener frames de escenas detectadas
response = requests.get(f'http://localhost:8000/api/videos/{video_id}/scenes')
scenes = response.json()
```

### 11.2 Generación de Audiodescripciones
```python
# Generar audiodescripciones para un video procesado
import requests
import json

video_id = "21fd44b3-3116-497d-bd54-77ffcff4be70"

# Obtener escenas detectadas
response = requests.get(f'http://localhost:8000/api/videos/{video_id}/scenes')
scenes = response.json()

# Crear descripciones para cada escena
descriptions = []
for scene in scenes:
    descriptions.append({
        "scene_id": scene["id"],
        "start_time": scene["start_time"],
        "end_time": scene["end_time"],
        "description": f"Descripción para la escena {scene['id']}"
    })

# Enviar descripciones
payload = {"descriptions": descriptions}
response = requests.post(
    f'http://localhost:8000/api/audiodesc/{video_id}',
    json=payload
)

# Generar audio para las descripciones
response = requests.post(f'http://localhost:8000/api/audiodesc/{video_id}/synthesize')
```

### 11.3 Integración en la Interfaz
Ver el ejemplo `examples/file_draw.py` para una demostración de cómo utilizar la biblioteca para dibujar frames con información de procesamiento.

## 12. Glosario de Términos

- **Audiodescripción**: Narración insertada en los espacios naturales de un contenido audiovisual que describe elementos visuales clave para personas con discapacidad visual.
- **FFmpeg**: Herramienta de línea de comandos para procesar archivos multimedia.
- **Frame**: Imagen individual de un video.
- **SceneDetect**: Biblioteca de Python para detección automática de escenas en videos.
- **SDH**: Subtítulos para Sordos y personas con Dificultades Auditivas, incluyen información adicional sobre efectos sonoros y música.
- **SRT**: SubRip Text, formato de archivo para subtítulos.
- **TTS**: Text-to-Speech, tecnología para convertir texto en habla sintetizada.
- **UNE153010**: Norma española para el subtitulado para personas sordas.
- **UNE153020**: Norma española para la audiodescripción.
- **UUID**: Identificador único universal, utilizado para identificar cada video en el sistema.
- **WCAG**: Web Content Accessibility Guidelines, pautas de accesibilidad para el contenido web.
- **Whisper**: Modelo de reconocimiento automático de voz desarrollado por OpenAI.

## 13. Referencias y Recursos

### 13.1 Estándares y Normativas
- [UNE153010](./docs/UNE153010.md) - Subtitulado para personas sordas
- [UNE153020](./docs/UNE153020.md) - Audiodescripción para personas ciegas
- [WCAG 2.1](https://www.w3.org/TR/WCAG21/) - Pautas de accesibilidad web

### 13.2 Recursos Técnicos
- [Documentación de Whisper OpenAI](https://github.com/openai/whisper)
- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de PySceneDetect](https://scenedetect.com/)
- [Documentación de Coqui TTS](https://github.com/coqui-ai/TTS)
- [Google Cloud Text-to-Speech API](https://cloud.google.com/text-to-speech)
- [Librosa para análisis de audio](https://librosa.org/doc/latest/index.html)

### 13.3 Tutoriales y Ejemplos
- Ver directorio `examples/` para código de ejemplo
- Consultar `test_*.py` para ver ejemplos de uso de las diferentes clases.htm)


## 14. Anexos

### 14.1 Plantillas y Ejemplos
- Ejemplos de audiodescripciones bien ejecutadas
- Plantillas de subtítulos para diferentes contextos
- Checklist de validación

### 14.2 Documentación Complementaria
- Código de conducta
- normativa

---

**Versión del documento**: 1.0
**Fecha de última actualización**: [28 de febrero 2025]
