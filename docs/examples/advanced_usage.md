
```markdown
# Uso Avanzado

## Monitoreo y Control
```python
async def monitor_task(task_id: str):
    pipeline = VideoPipeline()
    while True:
        status = await pipeline.get_task_status(task_id)
        if status['status'] in ['completed', 'error']:
            break
        await asyncio.sleep(5)