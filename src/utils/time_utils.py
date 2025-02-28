from formatters import format_timecode

def ms_to_timecode(ms: int) -> str:
    seconds = ms / 1000
    return format_timecode(seconds)