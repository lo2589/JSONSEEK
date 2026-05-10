import os
from pathlib import Path
from typing import Any, Optional

from .types import FileKind
from .errors import FileKindError


def detect_file_kind(path: str, kind_hint: Optional[str] = None) -> FileKind:
    """Detect whether a file is JSON or JSONL.

    Priority:
    1. Explicit kind_hint (if provided and valid)
    2. File extension .jsonl
    3. File extension .json
    4. Content sniffing (first non-empty line)
    """
    if kind_hint is not None:
        kind = kind_hint.lower().strip()
        if kind in ("json", "jsonl"):
            return kind  # type: ignore[return-value]
        raise FileKindError(f"Unsupported kind hint: {kind_hint!r}")

    ext = Path(path).suffix.lower()
    if ext == ".jsonl":
        return "jsonl"
    if ext == ".json":
        return "json"

    # Fallback: sniff first non-empty line
    if not os.path.exists(path):
        # Default to json for non-existent files when creating new
        return "json"

    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    continue
                break
            else:
                # Empty file
                return "json"
    except OSError:
        return "json"

    # Simple heuristic: count non-empty lines that look like JSON objects/arrays
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [l.strip() for l in f if l.strip()]
            if len(lines) > 1:
                # Multiple lines: likely JSONL
                return "jsonl"
            return "json"
    except OSError:
        return "json"
