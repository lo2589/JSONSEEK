from typing import Any
import argparse

from ..detect import detect_file_kind
from ..io.json_file import load_json_file, save_json_file
from ..path_parser import parse_path
from ..patch.locator import resolve_value_at_path
from ..value_utils import coerce_input_value
from ..formatters import format_patch_preview
from ..errors import JsonseekError, PatchError, PathError


def handle_extend(args: argparse.Namespace) -> int:
    try:
        is_dry_run = getattr(args, "dry_run", False)
        output = getattr(args, "output", "pretty")
        enc = getattr(args, "encoding", None)

        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))
        if kind == "jsonl":
            raise PatchError("extend is not supported for JSONL files. Use append instead.")

        values = coerce_input_value(args.value)
        if not isinstance(values, list):
            raise PatchError(f"extend value must be a JSON array, got {type(values).__name__}")

        data = load_json_file(args.file, encoding=enc)
        try:
            before_value = resolve_value_at_path(data, parse_path(args.path))
        except PathError:
            before_value = "<not found>"

        if is_dry_run:
            print(format_patch_preview(
                path=args.path,
                before=before_value,
                after=f"<will extend with {len(values)} item(s)>",
                output=output,
                dry_run=True,
            ))
            return 0

        patched = patch_json_extend(data, args.path, values)
        save_json_file(args.file, patched, backup=getattr(args, "backup", False), encoding=enc or "utf-8")

        try:
            after_value = resolve_value_at_path(patched, parse_path(args.path))
        except PathError:
            after_value = "<not found>"

        print(format_patch_preview(
            path=args.path,
            before=before_value,
            after=after_value,
            output=output,
            dry_run=False,
        ))
        return 0
    except (JsonseekError, PatchError) as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


def patch_json_extend(data: Any, target_path: str, values: list) -> Any:
    tokens = parse_path(target_path)
    arr = resolve_value_at_path(data, tokens)
    if not isinstance(arr, list):
        raise PatchError(f"Expected array at {target_path}, got {type(arr).__name__}")
    arr.extend(values)
    return data


def extend_value(path: str, target_path: str, values: list, encoding: str = "utf-8") -> None:
    """Extend an array in a JSON file. Python API version."""
    if not isinstance(values, list):
        raise PatchError(f"extend value must be a list, got {type(values).__name__}")
    from ..io.json_file import load_json_file, save_json_file
    data = load_json_file(path, encoding=encoding)
    patched = patch_json_extend(data, target_path, values)
    save_json_file(path, patched, backup=False, encoding=encoding)
