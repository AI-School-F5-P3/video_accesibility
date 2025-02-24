from setuptools import setup, find_packages

setup(
    name="video_accessibility",
    version="0.1.0",
    packages=find_packages(),
    package_dir={"": "."},
    install_requires=[
        "opencv-python",
        "numpy",
        "pydantic",
        "pytest",
        "pytest-asyncio"
    ],
    python_requires=">=3.11",
)