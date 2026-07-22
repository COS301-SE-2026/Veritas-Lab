from __future__ import annotations

from pathlib import Path

def validate_model_path(path_str: str) -> None:
    if ".." in Path(path_str).parts:
        raise ValueError(f"model path must not contain '..': {path_str}")