from __future__ import annotations

import os
import sys
from pathlib import Path

import uvicorn


def main() -> None:
    backend_dir = Path(__file__).resolve().parent
    backend_src = backend_dir / "src"

    # make backend/src importable (so "import app" works)
    sys.path.insert(0, str(backend_src))

    os.environ["PYTHONPATH"] = str(backend_src)

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        reload_dirs=[str(backend_dir)],
    )


if __name__ == "__main__":
    main()
