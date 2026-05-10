from typing import Optional
import argparse

from ..detect import detect_file_kind
from ..io.json_file import load_json_file
from ..io.jsonl_file import iter_jsonl_records
from ..walkers.query_scan import scan_query_hits_in_tree, scan_query_hits_in_record
from ..formatters import format_query_result
from ..errors import JsonseekError


def handle_query(args: argparse.Namespace) -> int:
    try:
        kind = detect_file_kind(args.file, kind_hint=getattr(args, "kind", None))
        term = args.term
        case_sensitive = getattr(args, "case_sensitive", False)
        exact = getattr(args, "exact", False)
        match_mode = getattr(args, "match_mode", "both")
        max_results = getattr(args, "max_results", None)
        record_id_field = getattr(args, "record_id_field", None)
        preview_field = getattr(args, "preview_field", None)

        if kind == "jsonl":
            hits = []
            for record in iter_jsonl_records(args.file):
                rec_hits = scan_query_hits_in_record(
                    record,
                    term,
                    case_sensitive=case_sensitive,
                    exact=exact,
                    match_mode=match_mode,
                    record_id_field=record_id_field,
                    preview_field=preview_field,
                )
                hits.extend(rec_hits)
        else:
            data = load_json_file(args.file)
            hits = scan_query_hits_in_tree(
                data,
                term,
                case_sensitive=case_sensitive,
                exact=exact,
                match_mode=match_mode,
            )

        hits = limit_hits(hits, max_results)
        print(format_query_result(hits, output=getattr(args, "output", "pretty")))
        return 0
    except JsonseekError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


def limit_hits(hits: list, max_results: Optional[int]) -> list:
    if max_results is None or max_results <= 0:
        return hits
    return hits[:max_results]
