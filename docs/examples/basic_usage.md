
```markdown
# Uso Básico

## Procesamiento de Video
```python
from app.pipeline.video_pipeline import VideoPipeline
from app.models.schemas import ServiceType

async def process_video():
    pipeline = VideoPipeline()
    result = await pipeline.process_url(
        "https://www.youtube.com/watch?v=example",
        ServiceType.AUDIODESCRIPCION
    )
    print(f"Task ID: {result.task_id}")