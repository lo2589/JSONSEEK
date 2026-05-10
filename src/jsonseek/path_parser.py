import re
from typing import List

from .types import KeyToken, IndexToken, PathToken
from .errors import PathError


# Regex to split path like "a.b[0].c" into segments
# Segments are either dot-separated keys or bracket indices
_PATH_RE = re.compile(r"\.|\[(\d+)\]")


def parse_path(path: str) -> List[PathToken]:
    """Parse a path string into a list of PathTokens.

    Supported syntax:
    - a.b.c        -> KeyToken("a"), KeyToken("b"), KeyToken("c")
    - items[0]     -> KeyToken("items"), IndexToken(0)
    - [0]          -> IndexToken(0)
    - payload.meta.tags[2] -> KeyToken("payload"), KeyToken("meta"), KeyToken("tags"), IndexToken(2)
    - a[key1][key2] -> KeyToken("a"), KeyToken("key1"), KeyToken("key2")
    - a.key1.key2  -> KeyToken("a"), KeyToken("key1"), KeyToken("key2")

    Empty string returns empty list (refers to root).
    """
    if not path:
        return []

    tokens: List[PathToken] = []
    current_key = ""
    i = 0
    n = len(path)

    while i < n:
        ch = path[i]
        if ch == ".":
            if current_key:
                tokens.append(KeyToken(current_key))
                current_key = ""
            else:
                # Double dot or leading dot
                if i == 0 or path[i - 1] == ".":
                    raise PathError(f"Invalid path: empty key segment at position {i} in {path!r}")
            i += 1
        elif ch == "[":
            if current_key:
                tokens.append(KeyToken(current_key))
                current_key = ""
            # Parse bracket content
            j = i + 1
            while j < n and path[j] != "]":
                j += 1
            if j >= n or path[j] != "]":
                raise PathError(f"Invalid path: unclosed bracket at position {i} in {path!r}")
            content = path[i + 1 : j]
            if not content:
                raise PathError(f"Invalid path: empty bracket at position {i} in {path!r}")
            # If content is all digits -> IndexToken, else -> KeyToken
            if content.isdigit():
                tokens.append(IndexToken(int(content)))
            else:
                tokens.append(KeyToken(content))
            i = j + 1
            # After a bracket, a dot is optional; skip it if present
            if i < n and path[i] == ".":
                i += 1
        else:
            current_key += ch
            i += 1

    if current_key:
        tokens.append(KeyToken(current_key))
    elif tokens and isinstance(tokens[-1], KeyToken) and tokens[-1].key == "":
        # Trailing dot case already caught, but be safe
        raise PathError(f"Invalid path: trailing dot in {path!r}")

    return tokens


def normalize_path(tokens: List[PathToken]) -> str:
    """Convert a list of PathTokens back to a dot/bracket path string."""
    if not tokens:
        return ""
    parts: List[str] = []
    for tok in tokens:
        if isinstance(tok, KeyToken):
            # Escape dots in keys? For now, keep it simple
            parts.append(tok.key)
        elif isinstance(tok, IndexToken):
            parts.append(f"[{tok.index}]")
    # Join KeyTokens with dots, but IndexTokens attach directly
    result = ""
    for i, part in enumerate(parts):
        if part.startswith("["):
            result += part
        else:
            if i > 0 and not result.endswith("["):
                result += "."
            result += part
    return result


def join_path(base: str, token: PathToken) -> str:
    """Append a single PathToken to a base path string."""
    if not base:
        if isinstance(token, KeyToken):
            return token.key
        return f"[{token.index}]"
    if isinstance(token, KeyToken):
        return f"{base}.{token.key}"
    return f"{base}[{token.index}]"


def is_parent_path(parent: str, child: str) -> bool:
    """Return True if `parent` path is a prefix of `child` path.

    Uses token-level comparison to handle edge cases correctly.
    """
    if parent == child:
        return True
    if not parent:
        return True
    if not child:
        return False

    parent_tokens = parse_path(parent)
    child_tokens = parse_path(child)

    if len(parent_tokens) > len(child_tokens):
        return False

    for pt, ct in zip(parent_tokens, child_tokens):
        if pt != ct:
            return False

    return True
