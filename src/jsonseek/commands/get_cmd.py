import argparse
from typing import Any

from ..detect import detect_file_kind
from ..io.json_file import load_json_file
from ..io.jsonl_file import get_jsonl_record_by_index
from ..path_parser import parse_path
from ..patch.locator import resolve_value_at_path, resolve_record_and_inner_path
from ..formatters import format_get_result
from ..errors import JsonseekError


def handle_get(args: argparse.Namespace) -> int:
    try:
        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))
        target_path = args.path
        if kind == "jsonl":
            record_index, inner_tokens = resolve_record_and_inner_path(target_path)
            value = get_jsonl_value(args.file, record_index, inner_tokens)
        else:
            data = load_json_file(args.file)
            tokens = parse_path(target_path)
            value = resolve_value_at_path(data, tokens)
        print(format_get_result(value, output=getattr(args, "output", "pretty")))
        return 0
    except JsonseekError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


def get_json_value(path: str, target_path: str) -> Any:
    data = load_json_file(path)
    tokens = parse_path(target_path)
    return resolve_value_at_path(data, tokens)


def get_jsonl_value(path: str, record_index: int, inner_path_tokens: list) -> Any:
    record = get_jsonl_record_by_index(path, record_index)
    if not inner_path_tokens:
        return record.data
    return resolve_value_at_path(record.data, inner_path_tokens)
