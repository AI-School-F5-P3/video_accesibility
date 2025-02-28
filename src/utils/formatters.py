def format_timecode(seconds: float) -> str:
    minutes = int(seconds / 60)
    remaining_seconds = int(seconds % 60)
    return f"{minutes:02d}:{remaining_seconds:02d}"