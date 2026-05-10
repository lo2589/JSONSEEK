from typing import Any
import argparse

from ..detect import detect_file_kind
from ..io.json_file import load_json_file, save_json_file
from ..io.jsonl_file import append_jsonl_record
from ..path_parser import parse_path
from ..patch.locator import resolve_value_at_path
from ..patch.array_ops import apply_append_to_array
from ..value_utils import coerce_input_value
from ..formatters import format_patch_result
from ..errors import JsonseekError, PatchError


def handle_append(args: argparse.Namespace) -> int:
    try:
        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))
        enc = getattr(args, "encoding", None)
        if kind == "jsonl":
            # JSONL append: args.path is the value when args.value is omitted
            raw_value = args.value if args.value is not None else args.path
            value = coerce_input_value(raw_value)
            append_jsonl_record(args.file, value, encoding=enc or "utf-8")
            print(format_patch_result(f"Appended record to {args.file}", output=getattr(args, "output", "pretty")))
        else:
            if args.value is None:
                raise PatchError("append for JSON requires both path and value arguments")
            value = coerce_input_value(args.value)
            data = load_json_file(args.file, encoding=enc)
            patched = patch_json_append(data, args.path, value)
            save_json_file(args.file, patched, backup=getattr(args, "backup", False), encoding=enc or "utf-8")
            print(format_patch_result(f"Appended to {args.path}", output=getattr(args, "output", "pretty")))
        return 0
    except (JsonseekError, PatchError) as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


def patch_json_append(data: Any, target_path: str, value: Any) -> Any:
    tokens = parse_path(target_path)
    arr = resolve_value_at_path(data, tokens)
    if not isinstance(arr, list):
        raise PatchError(f"Expected array at {target_path}, got {type(arr).__name__}")
    apply_append_to_array(arr, value)
    return data
