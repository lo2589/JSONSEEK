from typing import Any, Iterator, Optional, Tuple

from ..types import KeyToken, IndexToken
from ..value_utils import infer_node_kind


def walk_tree(value: Any, base_path: str = "") -> Iterator[Tuple[str, Any]]:
    """Depth-first walk of a JSON tree, yielding (path, value) pairs.

    Paths use dot notation for keys and bracket notation for indices.
    """
    yield base_path, value
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{base_path}.{key}" if base_path else key
            yield from walk_tree(child, child_path)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            child_path = f"{base_path}[{idx}]" if base_path else f"[{idx}]"
            yield from walk_tree(child, child_path)


def walk_tree_with_parents(value: Any, base_path: str = "") -> Iterator[Tuple[str, Any, Optional[str]]]:
    """Depth-first walk yielding (path, value, parent_path) triples.

    parent_path is None for the root.
    """
    yield base_path, value, None
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{base_path}.{key}" if base_path else key
            yield from _walk_tree_with_parents_impl(child, child_path, base_path)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            child_path = f"{base_path}[{idx}]" if base_path else f"[{idx}]"
            yield from _walk_tree_with_parents_impl(child, child_path, base_path)


def _walk_tree_with_parents_impl(value: Any, base_path: str, parent_path: str) -> Iterator[Tuple[str, Any, Optional[str]]]:
    yield base_path, value, parent_path
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = f"{base_path}.{key}" if base_path else key
            yield from _walk_tree_with_parents_impl(child, child_path, base_path)
    elif isinstance(value, list):
        for idx, child in enumerate(value):
            child_path = f"{base_path}[{idx}]" if base_path else f"[{idx}]"
            yield from _walk_tree_with_parents_impl(child, child_path, base_path)
