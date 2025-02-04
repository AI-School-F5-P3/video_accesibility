# video_accesibility
Autodescripciones y generación de subtitulos de videos para accesibilidad




## Estructura del Proyecto


audio-description-project/
├── .github/
│   └── workflows/
│       ├── ci.yml
│       └── cd.yml
├── src/
│   ├── core/
│   │   ├── __init__.py
│   │   ├── video_processor/
│   │   │   ├── __init__.py
│   │   │   ├── frame_extractor.py
│   │   │   └── video_manager.py
│   │   ├── audio_processor/
│   │   │   ├── __init__.py
│   │   │   ├── silence_detector.py
│   │   │   └── audio_manager.py
│   │   └── description_generator/
│   │       ├── __init__.py
│   │       ├── scene_analyzer.py
│   │       └── script_generator.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── speech_to_text/
│   │   │   ├── __init__.py
│   │   │   └── whisper_service.py
│   │   ├── text_to_speech/
│   │   │   ├── __init__.py
│   │   │   └── tts_service.py
│   │   └── vision_service/
│   │       ├── __init__.py
│   │       └── scene_vision.py
│   ├── utils/
│   │   ├── __init__.py
│   │   ├── validators.py
│   │   ├── file_handlers.py
│   │   └── time_utils.py
│   └── config/
│       ├── __init__.py
│       ├── settings.py
│       └── constants.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_video_processor/
│   ├── test_audio_processor/
│   ├── test_description_generator/
│   └── test_services/
├── docs/
│   ├── README.md
│   ├── CONTRIBUTING.md
│   ├── API.md
│   └── architecture/
│       ├── diagrams/
│       └── decisions/
├── data/
│   ├── sample_videos/
│   ├── output/
│   │   ├── transcriptions/
│   │   ├── descriptions/
│   │   └── final/
│   └── models/
│       └── weights/
├── notebooks/
│   ├── experiments/
│   └── prototypes/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
├── scripts/
│   ├── setup.sh
│   ├── test.sh
│   └── deploy.sh
├── .gitignore
├── .env.example
├── pyproject.toml
├── poetry.lock
├── README.md
└── requirements.txt
