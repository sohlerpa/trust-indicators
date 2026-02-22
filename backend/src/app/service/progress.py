import time
from typing import Callable, Any

ProgressFn = Callable[[str, float], None]

progress_state: dict[str, dict[str, Any]] = {}
results: dict[str, Any] = {}


def set_progress(id: str, step: str, pct: float) -> None:
    """
    Update the progress state for a given task identifier.

    Returns:
        None
    """
    progress_state[id] = {
        "step": step,
        "progress": pct,
        "updated": time.time(),
    }