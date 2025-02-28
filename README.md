# Proyecto de Audiodescripciones y Subtítulos

## Descripción

Este proyecto desarrolla una plataforma integral para la creación, gestión y distribución de audiodescripciones y subtítulos para contenido audiovisual. Nuestro objetivo es mejorar la accesibilidad del contenido multimedia para personas con discapacidades visuales y auditivas, siguiendo estándares internacionales y ofreciendo herramientas avanzadas asistidas por IA.

## Características Principales

- Transcripción automática de audio usando Whisper de OpenAI
- Generación de audiodescripciones con asistencia de IA y herramientas de edición manual
- Síntesis de voz de alta calidad con Coqui TTS y Google Cloud TTS
- Detección automática de escenas con SceneDetect
- Creación de subtítulos con transcripción automática y soporte para SDH (Subtítulos para Sordos)
- Procesamiento y análisis de audio con Librosa
- API RESTful para integración con FastAPI
- Cumplimiento normativo con estándares internacionales de accesibilidad (WCAG, EBU-TT, etc.)
- Compatibilidad con múltiples idiomas a través de modelos multilingües

## Inicio Rápido

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
python3 -m venv venv
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

5. Configurar API Key de Google AI Studio:

Para habilitar las funcionalidades de IA, necesitas configurar una API key de Google AI Studio:

```
GOOGLE_AI_STUDIO_API_KEY=tu_api_key_aquí
```

## Uso del Sistema

Hay dos formas de utilizar el sistema:

### A. Interfaz Web

1. Inicia el servidor:

```bash
python3 main.py
```

2. Abre tu navegador y navega a: http://localhost:8000
3. Utiliza la interfaz web para:
   - Subir videos
   - Generar subtítulos
   - Generar audiodescripciones
   - Visualizar los resultados

### B. Línea de Comandos

También puedes utilizar el sistema desde la línea de comandos con la herramienta CLI incluida:

#### Iniciar el servidor

Primero, inicia el servidor en una terminal:

```bash
python3 main.py
```

#### Uso básico del CLI

En otra terminal, utiliza la herramienta CLI:

```bash
# Listar videos disponibles
python3 miresse-cli.py list

# Subir un nuevo video
python3 miresse-cli.py upload /ruta/al/video.mp4

# Generar subtítulos para un video (reemplaza VIDEO_ID con el ID real)
python3 miresse-cli.py subtitle VIDEO_ID

# Generar audiodescripción para un video
python3 miresse-cli.py audiodesc VIDEO_ID

# Ver subtítulos generados
python3 miresse-cli.py view-subtitle VIDEO_ID

# Ver audiodescripción generada
python3 miresse-cli.py view-audiodesc VIDEO_ID
```

#### Opciones adicionales

```bash
# Esperar a que termine el proceso de generación
python3 miresse-cli.py subtitle VIDEO_ID --wait

# Guardar subtítulos en un archivo
python3 miresse-cli.py view-subtitle VIDEO_ID --output subtitulos.srt

# Guardar audiodescripción en un archivo
python3 miresse-cli.py view-audiodesc VIDEO_ID --output audiodesc.txt
```

## Arquitectura

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

## Documentación

La documentación del proyecto incluye:

- Estándar UNE153010 - Para subtitulado
- Estándar UNE153020 - Para audiodescripción
- Documentación API automática en http://localhost:8000/docs (generada por FastAPI)
- Código de conducta

## Pruebas

Para ejecutar las pruebas:

```bash
# Asegúrate de tener el entorno virtual activado
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Ejecutar todas las pruebas
pytest

# Ejecutar pruebas específicas
pytest tests/test_video_analyzer.py
pytest tests/test_audio_processor.py
pytest tests/test_speech_processor.py
```

## Solución de Problemas

### El servidor muestra advertencias sobre la API key

Si ves advertencias como "API key de Google AI Studio no configurada", asegúrate de:
1. Haber creado correctamente el archivo `.env`
2. Haber colocado la clave correctamente (`GOOGLE_AI_STUDIO_API_KEY=tu_clave_aquí`)
3. Reiniciar el servidor después de configurar la clave

### El procesamiento tarda demasiado

El procesamiento de videos, especialmente para la generación de audiodescripciones, puede tardar varios minutos dependiendo de:
- El tamaño y duración del video
- La complejidad del contenido
- Los recursos de tu sistema

Utiliza la opción `--wait` en el CLI para esperar automáticamente a que finalice el proceso.

## Roadmap

- Fase 1 (MVP) - Funcionalidades básicas de audiodescripción y subtitulado
- Fase 2 - Integración de modelos de IA avanzados y soporte multilingüe
- Fase 3 - Herramientas avanzadas de control de calidad y API para desarrolladores
- Fase 4 - Funcionalidades colaborativas y marketplace de servicios

## Equipo

- Jaanh Yajuri B - Especialista en IA/ML - @jyajupy
- Iryna Bilokon - Especialista en IA/ML - @irynabilokon
- Lisy Velasco - Especialista en IA/ML - @lisy29
- Leire Martin-Berdinos - Especialista en IA/ML - @leimber

## Contribuir

¡Las contribuciones son bienvenidas! Por favor, lee nuestra Guía de Contribución antes de enviar un pull request. Sigue nuestro Código de Conducta en todas las interacciones.

## Licencia

Este proyecto está licenciado bajo la Licencia Apache.

## Agradecimientos

- Scalian por su propuesta y seguimiento del proyecto
- Factoría F5 por la formación que culmina este proyecto


<p align="center">
  <sub>Hecho con ❤️ para mejorar la accesibilidad audiovisual a todo el mundo</sub>
</p>
