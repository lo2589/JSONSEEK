from typing import Any

from ..errors import PatchError


def apply_add_to_object(parent: dict, key: str, value: Any, create_missing: bool = False) -> None:
    """Add a key to an object. Raises PatchError if key already exists."""
    if key in parent:
        raise PatchError(f"Key already exists: {key!r}")
    parent[key] = value


def apply_set_to_object(parent: dict, key: str, value: Any, create_missing: bool = False) -> None:
    """Set a key in an object. Creates the key if it doesn't exist when create_missing=True."""
    if key not in parent and not create_missing:
        raise PatchError(f"Key not found for set: {key!r}")
    parent[key] = value


def apply_del_from_object(parent: dict, key: str) -> None:
    """Delete a key from an object. Raises PatchError if key not found."""
    if key not in parent:
        raise PatchError(f"Key not found for delete: {key!r}")
    del parent[key]
