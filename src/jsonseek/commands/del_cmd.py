from typing import Optional, Tuple, Any
import argparse

from ..detect import detect_file_kind
from ..io.json_file import load_json_file, save_json_file
from ..io.rewrite import rewrite_jsonl_file
from ..io.jsonl_file import get_jsonl_record_by_index, get_line_context
from ..path_parser import parse_path, normalize_path
from ..patch.locator import resolve_parent_and_key, resolve_record_and_inner_path, resolve_value_at_path
from ..patch.object_ops import apply_del_from_object
from ..patch.array_ops import apply_del_from_array
from ..formatters import format_patch_preview
from ..errors import JsonseekError, PatchError, PathError
from ..types import KeyToken, IndexToken


def handle_del(args: argparse.Namespace) -> int:
    try:
        is_dry_run = getattr(args, "dry_run", False)
        output = getattr(args, "output", "pretty")
        enc = getattr(args, "encoding", None)
        context = getattr(args, "context", 2)

        # Confirm before delete if not -y and not dry-run
        if not is_dry_run and not getattr(args, "yes", False):
            response = input(f"Delete '{args.path}' in {args.file}? [y/N]: ")
            if response.lower() != 'y':
                print("Cancelled")
                return 1

        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))

        if kind == "jsonl":
            record_index, inner_tokens = resolve_record_and_inner_path(args.path)
            has_inner = bool(inner_tokens)
            record = get_jsonl_record_by_index(args.file, record_index, encoding=enc)
            target_line = record.line_number
            before_context = get_line_context(args.file, target_line, context=context, encoding=enc)

            if not has_inner:
                # Delete whole record
                if is_dry_run:
                    print(format_patch_preview(
                        path=args.path,
                        output=output,
                        dry_run=True,
                        jsonl_before=before_context,
                        jsonl_target_line=target_line,
                        operation="deleted",
                    ))
                    return 0

                rewrite_jsonl_file(
                    args.file,
                    transform_record=lambda rec: (rec.record_index != record_index, rec.data),
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
                    operation="deleted",
                ))
            else:
                # Delete inner field
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
                    transform_record=lambda rec: patch_jsonl_record_del(
                        rec, record_index, inner_tokens
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

            # Compute parent path for after display
            tokens = parse_path(args.path)
            parent_tokens = tokens[:-1]
            parent_path = normalize_path(parent_tokens) if parent_tokens else "<root>"

            if is_dry_run:
                print(format_patch_preview(
                    path=args.path,
                    before=before_value,
                    after=f"<deleted> (parent: {parent_path})",
                    output=output,
                    dry_run=True,
                ))
                return 0

            patched = patch_json_del(data, args.path)
            save_json_file(args.file, patched, backup=getattr(args, "backup", False), encoding=enc or "utf-8")

            print(format_patch_preview(
                path=args.path,
                before=before_value,
                after=f"<deleted> (parent: {parent_path})",
                output=output,
                dry_run=False,
            ))
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


def del_value(path: str, target_path: str, encoding: str = "utf-8") -> None:
    """Delete a value at a path in a JSON file. Python API version."""
    from ..io.json_file import load_json_file, save_json_file
    data = load_json_file(path, encoding=encoding)
    patched = patch_json_del(data, target_path)
    save_json_file(path, patched, backup=False, encoding=encoding)
