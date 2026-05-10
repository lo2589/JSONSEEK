import argparse
from typing import Any, Dict

from ..detect import detect_file_kind
from ..io.json_file import load_json_file
from ..io.jsonl_file import get_jsonl_record_by_index
from ..path_parser import parse_path
from ..patch.locator import resolve_value_at_path, resolve_record_and_inner_path
from ..formatters import format_ls_result
from ..errors import JsonseekError


def handle_ls(args: argparse.Namespace) -> int:
    try:
        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))
        target_path = getattr(args, "path", "") or ""
        enc = getattr(args, "encoding", None)
        if kind == "jsonl":
            record_index, inner_tokens = resolve_record_and_inner_path(target_path)
            record = get_jsonl_record_by_index(args.file, record_index, encoding=enc)
            if inner_tokens:
                value = resolve_value_at_path(record.data, inner_tokens)
            else:
                value = record.data
        else:
            data = load_json_file(args.file, encoding=enc)
            tokens = parse_path(target_path)
            if tokens:
                value = resolve_value_at_path(data, tokens)
            else:
                value = data
        children = list_children(value)
        print(format_ls_result(children, output=getattr(args, "output", "pretty")))
        return 0
    except JsonseekError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


def list_children(value: Any) -> Dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    if isinstance(value, list):
        return {str(i): v for i, v in enumerate(value)}
    return {}
