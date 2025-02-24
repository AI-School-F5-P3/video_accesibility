# API Reference

## Clases Principales

### VideoPipeline
Clase principal para el procesamiento de videos.

#### Métodos
- `process_url(url: str, service_type: ServiceType) -> ProcessingResult`
- `get_task_status(task_id: str) -> Dict[str, Any]`

### VideoAnalyzer
Clase para análisis de video.

#### Métodos
- `analyze_content(video_path: Path) -> VideoMetadata`
- `detect_scenes(video_path: Path) -> List[Scene]`