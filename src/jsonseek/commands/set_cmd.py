from typing import Tuple, Any
import argparse

from ..detect import detect_file_kind
from ..io.json_file import load_json_file, save_json_file
from ..io.rewrite import rewrite_jsonl_file
from ..path_parser import parse_path
from ..patch.locator import resolve_parent_and_key, resolve_record_and_inner_path
from ..patch.object_ops import apply_set_to_object
from ..patch.array_ops import apply_set_in_array
from ..value_utils import coerce_input_value
from ..formatters import format_patch_result
from ..errors import JsonseekError, PatchError
from ..types import KeyToken, IndexToken


def handle_set(args: argparse.Namespace) -> int:
    try:
        value = coerce_input_value(args.value)
        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))
        if kind == "jsonl":
            record_index, inner_tokens = resolve_record_and_inner_path(args.path)
            rewrite_jsonl_file(
                args.file,
                transform_record=lambda rec: patch_jsonl_record_set(
                    rec, record_index, inner_tokens, value, create_missing=getattr(args, "create_missing", False)
                ),
                backup=getattr(args, "backup", False),
            )
        else:
            data = load_json_file(args.file)
            patched = patch_json_set(data, args.path, value, create_missing=getattr(args, "create_missing", False))
            save_json_file(args.file, patched, backup=getattr(args, "backup", False))
        print(format_patch_result(f"Set {args.path}", output=getattr(args, "output", "pretty")))
        return 0
    except (JsonseekError, PatchError) as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


def patch_json_set(data: Any, target_path: str, value: Any, create_missing: bool = False) -> Any:
    tokens = parse_path(target_path)
    parent, last_token = resolve_parent_and_key(data, tokens)
    if isinstance(last_token, KeyToken):
        if not isinstance(parent, dict):
            raise PatchError(f"Expected object parent at {target_path}, got {type(parent).__name__}")
        apply_set_to_object(parent, last_token.key, value, create_missing=create_missing)
    elif isinstance(last_token, IndexToken):
        if not isinstance(parent, list):
            raise PatchError(f"Expected array parent at {target_path}, got {type(parent).__name__}")
        apply_set_in_array(parent, last_token.index, value)
    return data


def patch_jsonl_record_set(
    record: Any, target_index: int, inner_tokens: list, value: Any, create_missing: bool = False
) -> Tuple[bool, Any]:
    from ..types import JsonlRecord
    if not isinstance(record, JsonlRecord):
        raise PatchError("Expected JsonlRecord")
    if record.record_index != target_index:
        return True, record.data
    data = record.data
    if not inner_tokens:
        raise PatchError("Cannot set root record; specify an inner path")
    parent, last_token = resolve_parent_and_key(data, inner_tokens)
    if isinstance(last_token, KeyToken):
        if not isinstance(parent, dict):
            raise PatchError(f"Expected object parent, got {type(parent).__name__}")
        apply_set_to_object(parent, last_token.key, value, create_missing=create_missing)
    elif isinstance(last_token, IndexToken):
        if not isinstance(parent, list):
            raise PatchError(f"Expected array parent, got {type(parent).__name__}")
        apply_set_in_array(parent, last_token.index, value)
    return True, data
