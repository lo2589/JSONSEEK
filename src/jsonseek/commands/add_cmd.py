from typing import Tuple, Any
import argparse

from ..detect import detect_file_kind
from ..io.json_file import load_json_file, save_json_file
from ..io.rewrite import rewrite_jsonl_file
from ..io.jsonl_file import get_jsonl_record_by_index, get_line_context
from ..path_parser import parse_path
from ..patch.locator import resolve_parent_and_key, resolve_record_and_inner_path, resolve_value_at_path
from ..patch.object_ops import apply_add_to_object
from ..value_utils import coerce_input_value
from ..formatters import format_patch_preview
from ..errors import JsonseekError, PatchError, PathError
from ..types import KeyToken, IndexToken


def handle_add(args: argparse.Namespace) -> int:
    try:
        is_dry_run = getattr(args, "dry_run", False)
        output = getattr(args, "output", "pretty")
        enc = getattr(args, "encoding", None)
        context = getattr(args, "context", 2)

        # Get value from file or command line
        if getattr(args, "from_file", None):
            from ..io.encoding import resolve_encoding
            file_enc = args.encoding or resolve_encoding(args.file, None)
            with open(args.from_file, 'r', encoding=file_enc) as f:
                raw = f.read().strip()
            value = coerce_input_value(raw)
        else:
            value = coerce_input_value(args.value)

        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))

        if kind == "jsonl":
            record_index, inner_tokens = resolve_record_and_inner_path(args.path)
            record = get_jsonl_record_by_index(args.file, record_index, encoding=enc)
            target_line = record.line_number
            before_context = get_line_context(args.file, target_line, context=context, encoding=enc)

            if is_dry_run:
                print(format_patch_preview(
                    path=args.path,
                    output=output,
                    dry_run=True,
                    jsonl_before=before_context,
                    jsonl_target_line=target_line,
                    operation="modified",
                ))
                return 0

            rewrite_jsonl_file(
                args.file,
                transform_record=lambda rec: patch_jsonl_record_add(
                    rec, record_index, inner_tokens, value, create_missing=getattr(args, "create_missing", False)
                ),
                backup=getattr(args, "backup", False),
                encoding=enc,
            )

            after_context = get_line_context(args.file, target_line, context=context, encoding=enc)
            print(format_patch_preview(
                path=args.path,
                output=output,
                dry_run=False,
                jsonl_before=before_context,
                jsonl_after=after_context,
                jsonl_target_line=target_line,
                operation="modified",
            ))
        else:
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

            patched = patch_json_add(data, args.path, value, create_missing=getattr(args, "create_missing", False))
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


def patch_json_add(data: Any, target_path: str, value: Any, create_missing: bool = False) -> Any:
    tokens = parse_path(target_path)
    parent, last_token = resolve_parent_and_key(data, tokens)
    if isinstance(last_token, KeyToken):
        if not isinstance(parent, dict):
            raise PatchError(f"Expected object parent at {target_path}, got {type(parent).__name__}")
        apply_add_to_object(parent, last_token.key, value, create_missing=create_missing)
    else:
        raise PatchError(f"Cannot add to array by index; use set or append: {target_path}")
    return data


def patch_jsonl_record_add(
    record: Any, target_index: int, inner_tokens: list, value: Any, create_missing: bool = False
) -> Tuple[bool, Any]:
    from ..types import JsonlRecord
    if not isinstance(record, JsonlRecord):
        raise PatchError("Expected JsonlRecord")
    if record.record_index != target_index:
        return True, record.data
    data = record.data
    if not inner_tokens:
        raise PatchError("Cannot add to root record; specify an inner path")
    parent, last_token = resolve_parent_and_key(data, inner_tokens)
    if isinstance(last_token, KeyToken):
        if not isinstance(parent, dict):
            raise PatchError(f"Expected object parent, got {type(parent).__name__}")
        apply_add_to_object(parent, last_token.key, value, create_missing=create_missing)
    else:
        raise PatchError(f"Cannot add to array by index; use set or append")
    return True, data


def add_value(path: str, target_path: str, value: Any, create_missing: bool = False, encoding: str = "utf-8") -> None:
    """Add a value at a path in a JSON file. Python API version."""
    from ..io.json_file import load_json_file, save_json_file
    data = load_json_file(path, encoding=encoding)
    patched = patch_json_add(data, target_path, value, create_missing=create_missing)
    save_json_file(path, patched, backup=False, encoding=encoding)
