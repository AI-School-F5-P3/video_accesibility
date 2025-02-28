# Proyecto de Audiodescripciones y Subtítulos


## Descripción

Este proyecto desarrolla una plataforma integral para la creación, gestión y distribución de audiodescripciones y subtítulos para contenido audiovisual. Nuestro objetivo es mejorar la accesibilidad del contenido multimedia para personas con discapacidades visuales y auditivas, siguiendo estándares internacionales y ofreciendo herramientas avanzadas asistidas por IA.

## Características Principales

- **Transcripción automática de audio** usando Whisper de OpenAI
- **Generación de audiodescripciones** con asistencia de IA y herramientas de edición manual
- **Síntesis de voz de alta calidad** con Coqui TTS y Google Cloud TTS
- **Detección automática de escenas** con SceneDetect
- **Creación de subtítulos** con transcripción automática y soporte para SDH (Subtítulos para Sordos)
- **Procesamiento y análisis de audio** con Librosa
- **API RESTful** para integración con FastAPI
- **Cumplimiento normativo** con estándares internacionales de accesibilidad (WCAG, EBU-TT, etc.)
- **Compatibilidad con múltiples idiomas** a través de modelos multilingües

##  Inicio Rápido

### Requisitos Previos

- Python 3.9 o superior
- Docker y Docker Compose
- Componentes multimedia (FFmpeg)
- Servicios Google Cloud (para TTS y procesamiento de IA)
- Cuenta en servicios cloud (opcional para despliegue)

### Instalación

1. Clonar el repositorio:
   ```bash
   git clone https://github.com/tu-organizacion/proyecto-audiodescripciones.git
   cd proyecto-audiodescripciones
   ```

2. Crear y activar un entorno virtual:
   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Configurar variables de entorno:
   ```bash
   cp .env.example .env
   # Editar .env con tus configuraciones
   ```

5. Iniciar los servicios con Docker:
   ```bash
   docker-compose up -d
   ```

6. Acceder a la aplicación:
   ```
   API: http://localhost:8000
   Documentación API: http://localhost:8000/docs
   Interfaz web: http://localhost:8000/ui
   ```

## 🧩 Arquitectura

El proyecto sigue una arquitectura modular:

```
├── api/                # API FastAPI para todos los endpoints
│   ├── endpoints/      # Endpoints específicos (audiodesc, subtitle, video)
│   └── main.py         # Configuración principal de la API
├── data/               # Datos y archivos procesados
│   ├── audio/          # Archivos de audio extraídos
│   ├── processed/      # Videos procesados con frames y metadatos
│   ├── raw/            # Videos originales sin procesar
│   └── transcripts/    # Subtítulos generados (.srt)
├── docs/               # Documentación (incluye estándares UNE153010/UNE153020)
├── front/              # Interfaz web simple con HTML/CSS/JS
├── src/                # Código fuente principal
│   ├── config/         # Configuración y credenciales
│   ├── core/           # Funcionalidades principales
│   │   ├── audio_processor.py    # Procesamiento de audio
│   │   ├── speech_processor.py   # Reconocimiento y síntesis de voz
│   │   ├── text_processor.py     # Procesamiento de texto
│   │   └── video_analyzer.py     # Análisis de video y escenas
│   ├── models/         # Modelos de datos
│   ├── services/       # Servicios de alto nivel
│   └── utils/          # Utilidades (logging, formateo, validación)
├── tests/              # Tests unitarios e integración
└── examples/           # Ejemplos de uso
```

##  Documentación

La documentación del proyecto incluye:

- Estándar UNE153010 - Para subtitulado
- Estándar UNE153020 - Para audiodescripción
- Documentación API automática en (generada por FastAPI):
- [Guía de Contribución](./CONTRIBUTING.md)
- [Código de conducta](./CODE_OF_CONDUCT.md)

## Pruebas

Para ejecutar las pruebas:

```bash
# Asegúrate de tener el entorno virtual activado
source env/bin/activate  # En Windows: env\Scripts\activate

# Ejecutar todas las pruebas
pytest

# Ejecutar pruebas específicas
pytest tests/test_video_analyzer.py
pytest tests/test_audio_processor.py
pytest tests/test_speech_processor.py
```

##  Roadmap

- **Fase 1 (MVP)** - Funcionalidades básicas de audiodescripción y subtitulado
- **Fase 2** - Integración de modelos de IA avanzados y soporte multilingüe
- **Fase 3** - Herramientas avanzadas de control de calidad y API para desarrolladores
- **Fase 4** - Funcionalidades colaborativas y marketplace de servicios



## Demos 

- [Demo en vivo](https://drive.google.com/file/d/1NQJxre1EunOqDbzsNwLlu5S1XoMYb13i/view?usp=drive_link)
  


## Equipo

- **Jaanh Yajuri B** - Especialista en IA/ML - [@jyajupy](https://github.com/jyajupy)
- **Iryna Bilokon** - Especialista en IA/ML - [@irynabilokon](https://github.com/irynabilokon)
- **Lisy Velasco** - Especialista en IA/ML - [@lisy29](https://github.com/Lisy29)
- **Leire Martin-Berdinos** - Especialista en IA/ML - [@leimber](https://github.com/leimber)


## Contribuir

¡Las contribuciones son bienvenidas! Por favor, lee nuestra [Guía de Contribución](./CONTRIBUTING.md) antes de enviar un pull request. Sigue nuestro [Código de Conducta](./CODE_OF_CONDUCT.md) en todas las interacciones.

## 📄 Licencia

Este proyecto está licenciado bajo la [Licencia Apache](./LICENSE).

## Agradecimientos

- Scalian por su propuesta y seguimiento del proyecto
- Factoría F5 por la formación que culmina este proyecto




<p align="center">
  <sub>Hecho con ❤️ para mejorar la accesibilidad audiovisual para todos</sub>
</p>
