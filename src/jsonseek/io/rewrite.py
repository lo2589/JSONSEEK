import os
import shutil
from typing import Any, Callable, Optional, Tuple

from ..types import JsonlRecord
from ..errors import JsonseekError
from .jsonl_file import iter_jsonl_records


def _atomic_replace(src: str, dst: str) -> None:
    """Cross-platform atomic file replace.

    On Windows, os.replace() fails if dst is open by another process.
    Fallback: remove dst then rename.
    """
    try:
        os.replace(src, dst)
    except PermissionError:
        if os.name == "nt" and os.path.exists(dst):
            os.remove(dst)
            os.rename(src, dst)
        else:
            raise


def rewrite_jsonl_file(
    path: str,
    transform_record: Optional[Callable[[JsonlRecord], Tuple[bool, Any]]],
    backup: bool = False,
) -> None:
    """Rewrite a JSONL file by transforming each record.

    transform_record(record) -> (keep, new_value)
      - keep=True  -> write new_value
      - keep=False -> drop the record
    """
    if backup and os.path.exists(path):
        backup_path = path + ".bak"
        shutil.copy2(path, backup_path)

    temp_path = path + ".tmp"
    try:
        with open(temp_path, "w", encoding="utf-8", newline="\n") as out_f:
            for record in iter_jsonl_records(path):
                keep, new_value = transform_record(record)
                if not keep:
                    continue
                import json
                out_f.write(json.dumps(new_value, ensure_ascii=False))
                out_f.write("\n")
        _atomic_replace(temp_path, path)
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise JsonseekError(f"Failed to rewrite {path}: {e}")
