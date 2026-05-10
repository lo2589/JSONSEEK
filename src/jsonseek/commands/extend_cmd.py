from typing import Any
import argparse

from ..detect import detect_file_kind
from ..io.json_file import load_json_file, save_json_file
from ..path_parser import parse_path
from ..patch.locator import resolve_value_at_path
from ..value_utils import coerce_input_value
from ..formatters import format_patch_result
from ..errors import JsonseekError, PatchError


def handle_extend(args: argparse.Namespace) -> int:
    try:
        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))
        if kind == "jsonl":
            raise PatchError("extend is not supported for JSONL files. Use append instead.")

        values = coerce_input_value(args.value)
        if not isinstance(values, list):
            raise PatchError(f"extend value must be a JSON array, got {type(values).__name__}")

        enc = getattr(args, "encoding", None)
        data = load_json_file(args.file, encoding=enc)
        patched = patch_json_extend(data, args.path, values)
        save_json_file(args.file, patched, backup=getattr(args, "backup", False), encoding=enc or "utf-8")
        print(format_patch_result(f"Extended {args.path} with {len(values)} item(s)", output=getattr(args, "output", "pretty")))
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
