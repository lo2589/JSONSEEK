from typing import Any
import argparse

from ..detect import detect_file_kind
from ..io.json_file import load_json_file, save_json_file
from ..io.jsonl_file import append_jsonl_record, get_line_context
from ..io.encoding import resolve_encoding
from ..path_parser import parse_path
from ..patch.locator import resolve_value_at_path
from ..patch.array_ops import apply_append_to_array
from ..value_utils import coerce_input_value
from ..formatters import format_patch_preview
from ..errors import JsonseekError, PatchError, PathError


def handle_append(args: argparse.Namespace) -> int:
    try:
        is_dry_run = getattr(args, "dry_run", False)
        output = getattr(args, "output", "pretty")
        enc = getattr(args, "encoding", None)
        context = getattr(args, "context", 2)

        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))

        if kind == "jsonl":
            # JSONL append: args.path is the value when args.value is omitted
            raw_value = args.value if args.value is not None else args.path
            value = coerce_input_value(raw_value)

            # Get file end context
            detected = resolve_encoding(args.file, enc)
            with open(args.file, 'r', encoding=detected) as f:
                total_lines = sum(1 for _ in f)
            target_line = total_lines if total_lines > 0 else 1
            before_context = get_line_context(args.file, target_line, context=context, encoding=enc)

            if is_dry_run:
                print(format_patch_preview(
                    path=args.file,
                    output=output,
                    dry_run=True,
                    jsonl_before=before_context,
                    jsonl_target_line=target_line,
                    operation="appended",
                ))
                return 0

            append_jsonl_record(args.file, value, encoding=enc or "utf-8")

            after_target_line = total_lines + 1
            after_context = get_line_context(args.file, after_target_line, context=context, encoding=enc)
            print(format_patch_preview(
                path=args.file,
                output=output,
                dry_run=False,
                jsonl_before=before_context,
                jsonl_after=after_context,
                jsonl_target_line=after_target_line,
                operation="appended",
            ))
        else:
            if args.value is None:
                raise PatchError("append for JSON requires both path and value arguments")
            value = coerce_input_value(args.value)
            data = load_json_file(args.file, encoding=enc)
            try:
                before_value = resolve_value_at_path(data, parse_path(args.path))
            except PathError:
                before_value = "<not found>"

            if is_dry_run:
                print(format_patch_preview(
                    path=args.path,
                    before=before_value,
                    after=value,
                    output=output,
                    dry_run=True,
                ))
                return 0

            patched = patch_json_append(data, args.path, value)
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


def patch_json_append(data: Any, target_path: str, value: Any) -> Any:
    tokens = parse_path(target_path)
    arr = resolve_value_at_path(data, tokens)
    if not isinstance(arr, list):
        raise PatchError(f"Expected array at {target_path}, got {type(arr).__name__}")
    apply_append_to_array(arr, value)
    return data


def append_value(path: str, target_path: str, value: Any, encoding: str = "utf-8") -> None:
    """Append a value to an array in a JSON file. Python API version."""
    from ..io.json_file import load_json_file, save_json_file
    data = load_json_file(path, encoding=encoding)
    patched = patch_json_append(data, target_path, value)
    save_json_file(path, patched, backup=False, encoding=encoding)
