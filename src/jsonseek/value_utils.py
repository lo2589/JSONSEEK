import json
from typing import Any

from .types import NodeKind


def infer_node_kind(value: Any) -> NodeKind:
    """Infer the JSON node kind of a Python value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, (int, float)):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return "string"


def short_preview(value: Any, max_len: int = 120) -> str:
    """Return a short string preview of a value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        if len(value) <= max_len:
            return value
        return value[: max_len - 3] + "..."
    # For containers, use JSON with truncation
    try:
        s = json.dumps(value, ensure_ascii=False)
    except (TypeError, ValueError):
        s = str(value)
    if len(s) <= max_len:
        return s
    return s[: max_len - 3] + "..."


def stable_type_name(value: Any) -> str:
    """Return a stable type name string for a value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "float"
    if isinstance(value, str):
        return "string"
    if isinstance(value, list):
        return "array"
    if isinstance(value, dict):
        return "object"
    return type(value).__name__


def coerce_input_value(raw: str) -> Any:
    """Coerce a command-line input string into a Python value.

    Tries JSON parsing first, then falls back to string.
    """
    raw = raw.strip()
    if raw == "null":
        return None
    if raw == "true":
        return True
    if raw == "false":
        return False
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass
    # Try integer
    try:
        return int(raw)
    except ValueError:
        pass
    # Try float
    try:
        return float(raw)
    except ValueError:
        pass
    # Fall back to plain string
    return raw
