from typing import Optional, Tuple, Any
import argparse

from ..detect import detect_file_kind
from ..io.json_file import load_json_file, save_json_file
from ..io.rewrite import rewrite_jsonl_file
from ..path_parser import parse_path
from ..patch.locator import resolve_parent_and_key, resolve_record_and_inner_path
from ..patch.object_ops import apply_del_from_object
from ..patch.array_ops import apply_del_from_array
from ..formatters import format_patch_result
from ..errors import JsonseekError, PatchError
from ..types import KeyToken, IndexToken


def handle_del(args: argparse.Namespace) -> int:
    try:
        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))
        enc = getattr(args, "encoding", None)
        if kind == "jsonl":
            # Determine if deleting whole record or inner field
            try:
                record_index, inner_tokens = resolve_record_and_inner_path(args.path)
                has_inner = bool(inner_tokens)
            except JsonseekError:
                # Maybe it's just [N] without inner path? resolve_record_and_inner_path handles that
                raise
            if not has_inner:
                # Delete whole record
                rewrite_jsonl_file(
                    args.file,
                    transform_record=lambda rec: (rec.record_index != record_index, rec.data),
                    backup=getattr(args, "backup", False),
                    encoding=enc,
                )
            else:
                rewrite_jsonl_file(
                    args.file,
                    transform_record=lambda rec: patch_jsonl_record_del(
                        rec, record_index, inner_tokens
                    ),
                    backup=getattr(args, "backup", False),
                    encoding=enc,
                )
        else:
            data = load_json_file(args.file, encoding=enc)
            patched = patch_json_del(data, args.path)
            save_json_file(args.file, patched, backup=getattr(args, "backup", False), encoding=enc or "utf-8")
        print(format_patch_result(f"Deleted {args.path}", output=getattr(args, "output", "pretty")))
        return 0
    except (JsonseekError, PatchError) as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


def patch_json_del(data: Any, target_path: str) -> Any:
    tokens = parse_path(target_path)
    parent, last_token = resolve_parent_and_key(data, tokens)
    if isinstance(last_token, KeyToken):
        if not isinstance(parent, dict):
            raise PatchError(f"Expected object parent at {target_path}, got {type(parent).__name__}")
        apply_del_from_object(parent, last_token.key)
    elif isinstance(last_token, IndexToken):
        if not isinstance(parent, list):
            raise PatchError(f"Expected array parent at {target_path}, got {type(parent).__name__}")
        apply_del_from_array(parent, last_token.index)
    return data


def patch_jsonl_record_del(
    record: Any, target_index: int, inner_tokens: list
) -> Optional[Tuple[bool, Any]]:
    from ..types import JsonlRecord
    if not isinstance(record, JsonlRecord):
        raise PatchError("Expected JsonlRecord")
    if record.record_index != target_index:
        return True, record.data
    data = record.data
    if not inner_tokens:
        return False, None
    parent, last_token = resolve_parent_and_key(data, inner_tokens)
    if isinstance(last_token, KeyToken):
        if not isinstance(parent, dict):
            raise PatchError(f"Expected object parent, got {type(parent).__name__}")
        apply_del_from_object(parent, last_token.key)
    elif isinstance(last_token, IndexToken):
        if not isinstance(parent, list):
            raise PatchError(f"Expected array parent, got {type(parent).__name__}")
        apply_del_from_array(parent, last_token.index)
    return True, data
