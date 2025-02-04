# video_accesibility
Autodescripciones y generación de subtitulos de videos para accesibilidad


audio-description-project/          # Directorio raíz del proyecto
├── .github/                        # Configuración de GitHub
│   └── workflows/                  # Flujos de trabajo automatizados
│       ├── ci.yml                 # Configuración de Integración Continua (tests, linting)
│       └── cd.yml                 # Configuración de Despliegue Continuo
├── src/                           # Código fuente principal
│   ├── core/                      # Componentes principales del sistema
│   │   ├── __init__.py
│   │   ├── video_processor/       # Procesamiento de vídeo
│   │   │   ├── __init__.py
│   │   │   ├── frame_extractor.py # Extracción de frames del vídeo
│   │   │   └── video_manager.py   # Gestión general de vídeos
│   │   ├── audio_processor/       # Procesamiento de audio
│   │   │   ├── __init__.py
│   │   │   ├── silence_detector.py # Detección de silencios en el audio
│   │   │   └── audio_manager.py    # Gestión general de audio
│   │   └── description_generator/  # Generación de descripciones
│   │       ├── __init__.py
│   │       ├── scene_analyzer.py   # Análisis de escenas
│   │       └── script_generator.py # Generación del guión de audiodescripción
│   ├── services/                   # Integración con servicios externos
│   │   ├── __init__.py
│   │   ├── speech_to_text/        # Servicio de transcripción de voz a texto
│   │   │   ├── __init__.py
│   │   │   └── whisper_service.py # Implementación con Whisper de OpenAI
│   │   ├── text_to_speech/        # Servicio de síntesis de voz
│   │   │   ├── __init__.py
│   │   │   └── tts_service.py     # Implementación con Coqui TTS
│   │   └── vision_service/        # Servicio de análisis de imágenes
│   │       ├── __init__.py
│   │       └── scene_vision.py    # Implementación con GPT-4 Vision/YOLO
│   ├── utils/                     # Utilidades generales
│   │   ├── __init__.py
│   │   ├── validators.py          # Validación de archivos y datos
│   │   ├── file_handlers.py       # Manejo de archivos
│   │   └── time_utils.py          # Utilidades de tiempo y sincronización
│   └── config/                    # Configuración del proyecto
│       ├── __init__.py
│       ├── settings.py            # Configuraciones generales
│       └── constants.py           # Constantes del proyecto
├── tests/                         # Tests del proyecto
│   ├── __init__.py
│   ├── conftest.py               # Configuración de pytest
│   ├── test_video_processor/     # Tests para el procesador de vídeo
│   ├── test_audio_processor/     # Tests para el procesador de audio
│   ├── test_description_generator/ # Tests para el generador de descripciones
│   └── test_services/            # Tests para los servicios externos
├── docs/                         # Documentación
│   ├── README.md                 # Documentación general
│   ├── CONTRIBUTING.md           # Guía de contribución
│   ├── API.md                    # Documentación de la API
│   └── architecture/             # Documentación de arquitectura
│       ├── diagrams/             # Diagramas del sistema
│       └── decisions/            # Registro de decisiones de arquitectura
├── data/                         # Datos del proyecto
│   ├── sample_videos/           # Vídeos de ejemplo para pruebas
│   ├── output/                  # Resultados generados
│   │   ├── transcriptions/      # Transcripciones generadas
│   │   ├── descriptions/        # Descripciones generadas
│   │   └── final/              # Vídeos finales con audiodescripción
│   └── models/                  # Modelos pre-entrenados
│       └── weights/             # Pesos de los modelos
├── notebooks/                    # Jupyter notebooks
│   ├── experiments/             # Experimentos y pruebas
│   └── prototypes/              # Prototipos de funcionalidades
├── docker/                      # Configuración de Docker
│   ├── Dockerfile              # Imagen principal del proyecto
│   ├── docker-compose.yml      # Composición de servicios para producción
│   └── docker-compose.dev.yml  # Composición de servicios para desarrollo
├── scripts/                    # Scripts útiles
│   ├── setup.sh               # Script de configuración inicial
│   ├── test.sh               # Script para ejecutar tests
│   └── deploy.sh             # Script de despliegue
├── .gitignore                # Archivos ignorados por git
├── .env.example             # Ejemplo de variables de entorno
├── pyproject.toml           # Configuración de Poetry y dependencias
├── poetry.lock             # Versiones bloqueadas de dependencias
├── README.md               # Documentación principal del proyecto
└── requirements.txt        # Dependencias (para compatibilidad)
