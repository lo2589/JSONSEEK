from typing import Optional
import argparse

from ..detect import detect_file_kind
from ..io.json_file import load_json_file
from ..io.jsonl_file import iter_jsonl_records
from ..walkers.field_scan import (
    scan_fields_in_tree,
    scan_fields_in_record,
    merge_field_stats,
    finalize_jsonl_field_stats,
)
from ..formatters import format_fields_result
from ..errors import JsonseekError


def handle_fields(args: argparse.Namespace) -> int:
    try:
        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))
        keyword = getattr(args, "keyword", None)
        if kind == "jsonl":
            stats = {}
            total = 0
            for record in iter_jsonl_records(args.file):
                total += 1
                rec_stats = scan_fields_in_record(record)
                merge_field_stats(stats, rec_stats)
            field_list = finalize_jsonl_field_stats(stats, total)
        else:
            data = load_json_file(args.file)
            stats = scan_fields_in_tree(data)
            field_list = list(stats.values())

        field_list = maybe_filter_fields(field_list, keyword)
        field_list = maybe_only_top_fields(field_list, top=getattr(args, "top", False))
        print(format_fields_result(field_list, output=getattr(args, "output", "pretty")))
        return 0
    except JsonseekError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


def maybe_filter_fields(stats: list, keyword: Optional[str]) -> list:
    if not keyword:
        return stats
    kw = keyword.lower()
    return [s for s in stats if kw in s.field.lower()]


def maybe_only_top_fields(stats: list, top: bool = False) -> list:
    if not top:
        return stats
    return [s for s in stats if _is_top_field(s)]


def _is_top_field(stat) -> bool:
    """Return True if this field appears at least once at the top level (path without '.')."""
    return any("." not in p for p in stat.paths)
