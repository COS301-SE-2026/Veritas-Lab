from __future__ import annotations

from pathlib import Path

def validate_model_path(path_str: str) -> Path:
    path = Path(path_str)
    if ".." in path.parts:
        raise ValueError(f"model path must not contain '..': {path_str}")
    return path