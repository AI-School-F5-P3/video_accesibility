# video_accesibility
Autodescripciones y generación de subtitulos de videos para accesibilidad




## Estructura del Proyecto


audio-description-project/ ├── .github/
│ └── workflows/
│ ├── ci.yml
│ └── cd.yml
├── src/
│ ├── core/
│ │ ├── init.py │ │ ├── video_processor/
│ │ │ ├── init.py │ │ │ ├── frame_extractor.py │ │ │ └── video_manager.py
│ │ ├── audio_processor/
│ │ │ ├── init.py │ │ │ ├── silence_detector.py │ │ │ └── audio_manager.py
│ │ └── description_generator/
│ │ ├── init.py │ │ ├── scene_analyzer.py
│ │ └── script_generator.py │ ├── services/
│ │ ├── init.py │ │ ├── speech_to_text/
│ │ │ ├── init.py │ │ │ └── whisper_service.py │ │ ├── text_to_speech/
│ │ │ ├── init.py │ │ │ └── tts_service.py
│ │ └── vision_service/
│ │ ├── init.py │ │ └── scene_vision.py
│ ├── utils/
│ │ ├── init.py │ │ ├── validators.py
│ │ ├── file_handlers.py
│ │ └── time_utils.py
│ └── config/
│ ├── init.py │ ├── settings.py
│ └── constants.py
├── tests/
│ ├── init.py │ ├── conftest.py
│ ├── test_video_processor/
│ ├── test_audio_processor/
│ ├── test_description_generator/ │ └── test_services/
├── docs/
│ ├── README.md
│ ├── CONTRIBUTING.md
│ ├── API.md
│ └── architecture/
│ ├── diagrams/
│ └── decisions/
├── data/
│ ├── sample_videos/
│ ├── output/
│ │ ├── transcriptions/
│ │ ├── descriptions/
│ │ └── final/
│ └── models/
│ └── weights/
├── notebooks/
│ ├── experiments/
│ └── prototypes/
├── docker/
│ ├── Dockerfile
│ ├── docker-compose.yml
│ └── docker-compose.dev.yml
├── scripts/
│ ├── setup.sh
│ ├── test.sh
│ └── deploy.sh
├── .gitignore
├── .env.example
├── pyproject.toml
├── poetry.lock
├── README.md
└── requirements.txt
