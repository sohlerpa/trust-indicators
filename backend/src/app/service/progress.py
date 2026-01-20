import time
from typing import Callable

ProgressFn = Callable[[str, float], None]

progress_state: dict[str, dict] = {}
results: dict[str, any] = {}

def set_progress(id: str, step: str, pct: float):
    progress_state[id] = {
        "step": step,
        "progress": pct,
        "updated": time.time()
    }