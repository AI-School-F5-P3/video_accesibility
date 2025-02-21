from setuptools import setup, find_packages

setup(
    name="video_accessibility",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.115.8",
        "uvicorn>=0.34.0",
        "google-cloud-aiplatform>=1.71.1",
        "pytube>=15.0.0",
        "python-dotenv>=1.0.1",
        "numpy>=2.1.1",
        "pytest>=8.3.4"
    ],
    python_requires=">=3.11",
)