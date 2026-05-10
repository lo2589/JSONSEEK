import json
import os
import shutil
from typing import Any

from ..errors import JsonseekError


def load_json_file(path: str) -> Any:
    """Load a JSON file and return the Python tree."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        raise JsonseekError(f"File not found: {path}")
    except json.JSONDecodeError as e:
        raise JsonseekError(f"Invalid JSON in {path}: {e}")


def dump_json_data(data: Any, pretty: bool = True) -> str:
    """Serialize data to a JSON string."""
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _atomic_replace(src: str, dst: str) -> None:
    """Cross-platform atomic file replace."""
    try:
        os.replace(src, dst)
    except PermissionError:
        if os.name == "nt" and os.path.exists(dst):
            os.remove(dst)
            os.rename(src, dst)
        else:
            raise


def save_json_file(path: str, data: Any, backup: bool = False) -> None:
    """Save data to a JSON file atomically, optionally creating a backup."""
    if backup and os.path.exists(path):
        backup_path = path + ".bak"
        shutil.copy2(path, backup_path)

    temp_path = path + ".tmp"
    try:
        content = dump_json_data(data, pretty=True)
        with open(temp_path, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
            f.write("\n")
        _atomic_replace(temp_path, path)
    except OSError as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise JsonseekError(f"Failed to write {path}: {e}")
