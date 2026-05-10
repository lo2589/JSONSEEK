import argparse
import glob
import os
from typing import Any, Dict, List

from ..detect import detect_file_kind
from ..io.json_file import load_json_file
from ..path_parser import parse_path
from ..patch.locator import resolve_value_at_path
from ..formatters import format_extract_result
from ..errors import JsonseekError


def handle_extract(args: argparse.Namespace) -> int:
    try:
        pattern = args.pattern
        target_path = args.path
        output = getattr(args, "output", "pretty")
        include_missing = getattr(args, "include_missing", False)

        # Expand glob pattern
        files = sorted(glob.glob(pattern))
        if not files:
            # If no glob match, treat pattern as literal single file
            if os.path.isfile(pattern):
                files = [pattern]
            else:
                print(f"No files matched pattern: {pattern}", file=__import__("sys").stderr)
                return 1

        tokens = parse_path(target_path)
        results: List[Dict[str, Any]] = []

        enc = getattr(args, "encoding", None)
        for path in files:
            kind = detect_file_kind(path, kind_hint=getattr(args, "kind", None))
            if kind == "jsonl":
                # Skip JSONL files for batch extract; they're single-file multi-record
                continue
            try:
                data = load_json_file(path, encoding=enc)
                value = resolve_value_at_path(data, tokens)
                results.append({"file": path, "value": value, "ok": True})
            except JsonseekError as e:
                if include_missing:
                    results.append({"file": path, "value": None, "ok": False, "error": str(e)})
                # else skip files where path doesn't exist

        print(format_extract_result(results, output=output))
        return 0
    except JsonseekError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1
