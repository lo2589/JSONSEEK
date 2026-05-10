from typing import Any, List, Tuple

from ..types import PathToken, KeyToken, IndexToken, JsonlRecord
from ..errors import PathError
from ..path_parser import parse_path


def resolve_value_at_path(data: Any, path_tokens: List[PathToken]) -> Any:
    """Resolve a value by following path tokens from data root.

    Returns the value at the path, or raises PathError if not found.
    """
    current = data
    for token in path_tokens:
        if isinstance(token, KeyToken):
            if not isinstance(current, dict):
                raise PathError(f"Expected object at path, got {type(current).__name__}")
            if token.key not in current:
                raise PathError(f"Key not found: {token.key}")
            current = current[token.key]
        elif isinstance(token, IndexToken):
            if not isinstance(current, list):
                raise PathError(f"Expected array at path, got {type(current).__name__}")
            if token.index < 0 or token.index >= len(current):
                raise PathError(f"Index out of range: {token.index} (length {len(current)})")
            current = current[token.index]
    return current


def resolve_parent_and_key(data: Any, path_tokens: List[PathToken]) -> Tuple[Any, PathToken]:
    """Resolve the parent container and the final key/index token.

    Returns (parent, last_token). Raises PathError if parent cannot be resolved.
    """
    if not path_tokens:
        raise PathError("Cannot resolve empty path for patch operation")

    parent_tokens = path_tokens[:-1]
    last_token = path_tokens[-1]

    if not parent_tokens:
        # The root itself is the parent (only valid if data is dict/list)
        return data, last_token

    current = data
    for token in parent_tokens:
        if isinstance(token, KeyToken):
            if not isinstance(current, dict):
                raise PathError(f"Expected object at path, got {type(current).__name__}")
            if token.key not in current:
                raise PathError(f"Key not found: {token.key}")
            current = current[token.key]
        elif isinstance(token, IndexToken):
            if not isinstance(current, list):
                raise PathError(f"Expected array at path, got {type(current).__name__}")
            if token.index < 0 or token.index >= len(current):
                raise PathError(f"Index out of range: {token.index} (length {len(current)})")
            current = current[token.index]

    return current, last_token


def resolve_record_and_inner_path(path: str) -> Tuple[int, List[PathToken]]:
    """Parse a JSONL path like '[12].payload.diff' or 'records[12].payload.diff'.

    Returns (record_index, inner_path_tokens).
    """
    if not path:
        raise PathError("Empty path for JSONL record selection")

    # Handle [N] or records[N] prefix
    if path.startswith("["):
        end = path.find("]")
        if end == -1:
            raise PathError(f"Unclosed bracket in JSONL path: {path!r}")
        idx_str = path[1:end]
        try:
            record_index = int(idx_str)
        except ValueError:
            raise PathError(f"Invalid record index: {idx_str!r}")
        inner = path[end + 1 :]
        if inner.startswith("."):
            inner = inner[1:]
        return record_index, parse_path(inner)

    # Try records[N] or just N as first key segment
    tokens = parse_path(path)
    if not tokens:
        raise PathError(f"Empty path for JSONL record selection: {path!r}")

    first = tokens[0]
    if isinstance(first, KeyToken) and first.key.lower() == "records" and len(tokens) >= 2:
        second = tokens[1]
        if isinstance(second, IndexToken):
            return second.index, tokens[2:]

    # If first token is a bare integer-like key... actually the spec says [N] or records[N]
    # Fallback: if path starts with a number token treated as index? No, let's require bracket syntax.
    raise PathError(
        f"JSONL path must start with [N] or records[N], got: {path!r}"
    )
