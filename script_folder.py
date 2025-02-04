import os

def create_project_structure(base_path="VIDEO_ACCESIBILITY"):
    structure = [
        ".env",
        ".gitignore",
        "README.md",
        "requirements.txt",
        "setup.py",
        "docs/UNE153020.md",
        "docs/UNE153010.md",
        "docs/api/",
        "src/__init__.py",
        "src/config/__init__.py",
        "src/config/settings.py",
        "src/core/__init__.py",
        "src/core/video_analyzer.py",
        "src/core/speech_processor.py",
        "src/core/text_processor.py",
        "src/core/audio_processor.py",
        "src/models/__init__.py",
        "src/models/scene.py",
        "src/models/transcript.py",
        "src/utils/__init__.py",
        "src/utils/validators.py",
        "src/utils/formatters.py",
        "src/utils/time_utils.py",
        "src/services/__init__.py",
        "src/services/video_service.py",
        "src/services/speech_service.py",
        "src/services/subtitle_service.py",
        "tests/__init__.py",
        "tests/test_video_analyzer.py",
        "tests/test_speech_processor.py",
        "tests/test_text_processor.py",
        "tests/test_audio_processor.py",
        "data/raw/",
        "data/processed/",
        "data/transcripts/",
        "data/audio/",
        "examples/sample_scripts/",
        "examples/sample_videos/"
    ]

    for path in structure:
        full_path = os.path.join(base_path, path)
        if path.endswith("/"):
            os.makedirs(full_path, exist_ok=True)
        else:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "w") as f:
                f.write("")
    
    print(f"Project structure created at: {base_path}")

if __name__ == "__main__":
    create_project_structure()