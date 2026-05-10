from typing import Any

from ..errors import PatchError


def apply_append_to_array(arr: list, value: Any) -> None:
    """Append a value to an array."""
    arr.append(value)


def apply_set_in_array(arr: list, index: int, value: Any) -> None:
    """Set a value at a specific array index."""
    if index < 0 or index >= len(arr):
        raise PatchError(f"Array index out of range: {index} (length {len(arr)})")
    arr[index] = value


def apply_del_from_array(arr: list, index: int) -> None:
    """Delete an element at a specific array index."""
    if index < 0 or index >= len(arr):
        raise PatchError(f"Array index out of range for delete: {index} (length {len(arr)})")
    del arr[index]
