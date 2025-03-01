# Miressë: Revolucionando la Automatización de la Audiodescripción y el Subtitulado 

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
- Base de datos con PostgreSQL para almacenamiento eficiente de información multimedia

## Inicio Rápido

### Requisitos Previos

- Python 3.9 o superior
- Docker y Docker Compose
- Componentes multimedia (FFmpeg)
- PostgreSQL 12 o superior
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

### Configuración de la Base de Datos PostgreSQL

1. **Instalar PostgreSQL** (si aún no está instalado):
   ```bash
   sudo apt update
   sudo apt install postgresql postgresql-contrib
   ```

2. **Iniciar el servicio**:
   ```bash
   sudo systemctl start postgresql
   sudo systemctl enable postgresql
   ```

3. **Configurar la base de datos Miresse**:
   ```bash
   # Acceder a PostgreSQL como superusuario
   sudo -u postgres psql

   # Dentro de PostgreSQL, ejecutar:
   CREATE DATABASE miresse;
   ALTER USER postgres WITH PASSWORD 'tu_contraseña';
   \q
   ```

4. **Actualizar el archivo `.env` con las credenciales de PostgreSQL**:
   ```
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=miresse
   DB_USER=postgres
   DB_PASSWORD=tu_contraseña
   ```

5. **Crear tablas y estructuras**:
   ```bash
   python setup_database.py
   ```

6. **Verificar la instalación**:
   ```bash
   python test_database.py
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

#### Comandos Avanzados

```bash
# Subir y procesar video con subtítulos y audiodescripción integrados
python miresse-cli.py process <video_id>
--subtitles \
--audiodesc \
--integrate \
--lang es \
--format srt

# Comprobar el estado de un video
python miresse-cli.py status <video_id>

# Obtener resultados y enlaces a subtítulos, audiodescripción o video final
python miresse-cli.py result <video_id>

# Descargar solo los subtítulos
python miresse-cli.py subtitles <video_id> --format srt --download --output "subtitulos_video.srt"

# Descargar solo la audiodescripción
python miresse-cli.py audiodesc <video_id> --format mp3 --download --output "audiodescripcion_video.mp3"

# Descargar el video final con subtítulos y audiodescripción integrados
python miresse-cli.py integrated <video_id> --download --output "video_final_integrado.mp4"

# Eliminar un video del sistema
python miresse-cli.py delete <video_id>

# Limpiar archivos temporales
python miresse-cli.py cleanup
```

## Base de Datos PostgreSQL

El proyecto utiliza PostgreSQL para almacenar referencias a videos, frames, subtítulos y audiodescripciones de manera eficiente y estructurada.

### Estructura de la Base de Datos

- **videos**: Almacena información de los videos (ID, ruta, estado de procesamiento)
- **frames**: Guarda referencias a frames extraídos del video
- **subtitles**: Almacena subtítulos con tiempos de inicio y fin
- **audio_descriptions**: Guarda audiodescripciones con tiempos y rutas a archivos de audio

### Consultar datos mediante PostgreSQL

```bash
# Conectarse a la base de datos
psql -h localhost -U postgres -d miresse

# Listar todas las tablas
\dt

# Ver videos
SELECT * FROM videos;

# Ver frames de un video específico
SELECT * FROM frames WHERE video_id = 'id-del-video';

# Ver subtítulos
SELECT * FROM subtitles WHERE video_id = 'id-del-video';

# Ver audiodescripciones
SELECT * FROM audio_descriptions WHERE video_id = 'id-del-video';

# Ver todos los elementos de un video ordenados cronológicamente
SELECT * FROM get_video_elements('id-del-video');
```

### Utilidades para la Base de Datos

```bash
# Ver el contenido de todas las tablas
python view_database.py

# Realizar pruebas en la base de datos
python test_database.py
```

## Arquitectura

El proyecto sigue una arquitectura modular:

```
├── api
│   ├── endpoints
│   │   ├── audiodesc.py
│   │   ├── subtitle.py
│   │   └── video.py
│   └── __init__.py
├── data
│   ├── audio          # Archivos de audio para audiodescripciones
│   ├── processed      # Contenido procesado (frames, videos con audiodescripción)
│   │   └── {video_id}
│   │       ├── frame_X.jpg
│   │       └── descriptions.json
│   ├── raw            # Videos originales sin procesar
│   │   └── {video_id}
│   │       └── {video_id}.mp4
│   └── transcripts    # Subtítulos y transcripciones
├── docs
│   ├── UNE153010.md
│   ├── UNE_153010.pdf
│   ├── UNE153020.md
│   └── UNE_153020.pdf
├── examples
│   └── file_draw.py
├── front
│   ├── css
│   │   └── styles.css
│   ├── index.html
│   └── js
│       └── main.js
├── src
│   ├── config
│   │   ├── credentials
│   │   │   └── google_credentials.json
│   │   ├── database.py    # Configuración de la base de datos
│   │   ├── settings.py
│   │   └── setup.py
│   ├── core
│   │   ├── audio_processor.py
│   │   ├── speech_processor.py
│   │   ├── text_processor.py
│   │   └── video_analyzer.py
│   ├── models
│   │   ├── database_models.py    # Modelos para la base de datos
│   │   ├── scene.py
│   │   ├── schemas.py
│   │   └── transcript.py
│   ├── services
│   │   ├── speech_service.py
│   │   ├── subtitle_service.py
│   │   └── video_service.py
│   └── utils
│       ├── directory_utils.py    # Utilidades para gestión de directorios
│       ├── formatters.py
│       ├── logger.py
│       ├── time_utils.py
│       └── validators.py
├── tests
│   ├── test_api.py
│   ├── test_audio_processor.py
│   ├── test_credentials.py
│   ├── test_database.py          # Pruebas para la base de datos
│   ├── test_directory_utils.py
│   ├── test_runner.py
│   ├── test_speech_processor.py
│   ├── test_speech_services.py
│   ├── test_subtitle_generation.py
│   ├── test_subtitles.py
│   ├── test_text_processor.py
│   ├── test_video_analyzer.py
│   └── whisper_test.py
├── .env                          # Variables de entorno con credenciales
├── .gitignore
├── CODE_OF_CONDUCT.md
├── DOCUMENTATION.md
├── LICENSE
├── README.md
├── main.py
├── miresse-cli.py
├── requirements.txt
├── setup_database.py             # Script para crear la base de datos
├── test_database.py              # Pruebas de la base de datos
└── view_database.py              # Visualización de datos
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
pytest tests/test_database.py  # Pruebas de la base de datos
```

## Solución de Problemas

### El servidor muestra advertencias sobre la API key

Si ves advertencias como "API key de Google AI Studio no configurada", asegúrate de:
1. Haber creado correctamente el archivo `.env`
2. Haber colocado la clave correctamente (`GOOGLE_AI_STUDIO_API_KEY=tu_clave_aquí`)
3. Reiniciar el servidor después de configurar la clave

### Problemas con la base de datos PostgreSQL

Si experimentas problemas con la base de datos:

1. **Verifica las credenciales**: Asegúrate de que las credenciales en `.env` son correctas
2. **Comprueba que PostgreSQL está funcionando**: `sudo systemctl status postgresql`
3. **Verifica la conexión manualmente**: `psql -h localhost -U postgres -d miresse`
4. **Ejecuta las pruebas de base de datos**: `python test_database.py`
5. **Verifica los logs**: Busca errores en los logs del servidor PostgreSQL

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
