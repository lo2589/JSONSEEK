import argparse
import sys
from typing import Any, List, Optional

from . import commands
from .detect import detect_file_kind
from .errors import JsonseekError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="jsonseek", description="Query and patch JSON/JSONL files from the command line.")
    parser.add_argument("--version", action="version", version="%(prog)s 0.1.0")

    sub = parser.add_subparsers(dest="command", help="Available commands")

    # Common arguments helper
    def add_common(p: argparse.ArgumentParser) -> None:
        p.add_argument("file", help="Target JSON or JSONL file")
        p.add_argument("--kind", choices=["json", "jsonl"], default=None, help="Force file kind (auto-detect by default)")
        p.add_argument("--output", choices=["pretty", "json"], default="pretty", help="Output format")
        p.add_argument("--backup", action="store_true", default=False, help="Create .bak backup before writing")
        p.add_argument("--encoding", default=None, help="File encoding (auto-detect by default)")
        p.add_argument("--dry-run", action="store_true", default=False, help="Preview changes without applying")
        p.add_argument("--context", type=int, default=2, help="Lines of context around target line (JSONL only)")

    # shape
    shape_p = sub.add_parser("shape", help="Show structure/shape of the file")
    add_common(shape_p)
    shape_p.add_argument("--max-depth", type=int, default=None, help="Maximum depth to traverse")
    shape_p.add_argument("--array-mode", choices=["sample", "full"], default="sample", help="Array traversal mode")
    shape_p.add_argument("--sample-size", type=int, default=100, help="Number of records to sample for JSONL")

    # fields
    fields_p = sub.add_parser("fields", help="List fields and their types")
    add_common(fields_p)
    fields_p.add_argument("keyword", nargs="?", default=None, help="Filter fields by keyword")
    fields_p.add_argument("--top", action="store_true", default=False, help="Show only top-level fields")

    # ls
    ls_p = sub.add_parser("ls", help="List children at a path")
    add_common(ls_p)
    ls_p.add_argument("path", nargs="?", default="", help="Path to list (default: root)")

    # get
    get_p = sub.add_parser("get", help="Get value at a path")
    add_common(get_p)
    get_p.add_argument("path", help="Path to retrieve")

    # query
    query_p = sub.add_parser("query", help="Search for keys or values")
    add_common(query_p)
    query_p.add_argument("term", help="Search term")
    query_p.add_argument("--case-sensitive", action="store_true", default=False, help="Case-sensitive matching")
    query_p.add_argument("--exact", action="store_true", default=False, help="Exact match only")
    query_p.add_argument("--match-mode", choices=["key", "value", "both"], default="both", help="What to match against")
    query_p.add_argument("--max-results", type=int, default=None, help="Limit number of results")
    query_p.add_argument("--record-id-field", default=None, help="Field to use as record ID in JSONL output")
    query_p.add_argument("--preview-field", default=None, help="Field to preview in JSONL output")

    # add
    add_p = sub.add_parser("add", help="Add a key/value to an object")
    add_common(add_p)
    add_p.add_argument("path", help="Target path")
    add_p.add_argument("value", nargs="?", default=None, help="Value to add (JSON string or literal)")
    add_p.add_argument("--create-missing", action="store_true", default=False, help="Create missing intermediate keys")
    add_p.add_argument("--from-file", default=None, help="Read value from file")

    # del
    del_p = sub.add_parser("del", help="Delete a key or array element")
    add_common(del_p)
    del_p.add_argument("path", help="Target path to delete")
    del_p.add_argument("-y", "--yes", action="store_true", help="Skip confirmation")

    # set
    set_p = sub.add_parser("set", help="Set a value at a path")
    add_common(set_p)
    set_p.add_argument("path", help="Target path")
    set_p.add_argument("value", nargs="?", default=None, help="Value to set (JSON string or literal)")
    set_p.add_argument("--create-missing", action="store_true", default=False, help="Create missing intermediate keys")
    set_p.add_argument("--from-file", default=None, help="Read value from file")

    # append
    append_p = sub.add_parser("append", help="Append a value to an array or JSONL file")
    add_common(append_p)
    append_p.add_argument("path", help="Target array path (JSON) or value (JSONL)")
    append_p.add_argument("value", nargs="?", default=None, help="Value to append (JSON only)")

    # extract
    extract_p = sub.add_parser("extract", help="Extract a path from multiple JSON files")
    extract_p.add_argument("pattern", help="Glob pattern to match files (e.g. '*.json' or 'data/*.json')")
    extract_p.add_argument("path", help="Path to extract from each file")
    extract_p.add_argument("--output", choices=["pretty", "json"], default="pretty", help="Output format")
    extract_p.add_argument("--kind", choices=["json", "jsonl"], default=None, help="Force file kind")
    extract_p.add_argument("--include-missing", action="store_true", default=False, help="Include files where path is missing")

    # extend
    extend_p = sub.add_parser("extend", help="Extend an array with multiple values (JSON only)")
    add_common(extend_p)
    extend_p.add_argument("path", help="Target array path")
    extend_p.add_argument("value", help="JSON array string to extend with")

    # concat
    concat_p = sub.add_parser("concat", help="Concatenate multiple JSON files into JSONL")
    concat_p.add_argument("pattern", help="Glob pattern to match JSON files (e.g. '*.json' or 'data/*.json')")
    concat_p.add_argument("--output-file", "-o", default=None, help="Output JSONL file (default: stdout)")
    concat_p.add_argument("--encoding", default=None, help="File encoding (auto-detect by default)")
    concat_p.add_argument("--no-sort", action="store_true", default=False, help="Preserve glob order instead of sorting by filename")

    # cutline
    cutline_p = sub.add_parser("cutline", help="Extract a specific line from a file")
    cutline_p.add_argument("file", help="Target file")
    cutline_p.add_argument("line", type=int, help="Line number to extract (1-indexed)")
    cutline_p.add_argument("--encoding", default=None, help="File encoding")
    cutline_p.add_argument("--save-temp", action="store_true", help="Save to temp file and return path")

    # replaceline
    replaceline_p = sub.add_parser("replaceline", help="Replace a line in a file")
    replaceline_p.add_argument("file", help="Target file")
    replaceline_p.add_argument("line", type=int, help="Line number (1-indexed)")
    replaceline_p.add_argument("content", nargs='?', default=None, help="Content to insert")
    replaceline_p.add_argument("--encoding", default=None, help="File encoding")
    replaceline_p.add_argument("--from-file", default=None, help="Read content from file")

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 1
    return dispatch_command(args)


def dispatch_command(args: argparse.Namespace) -> int:
    command = args.command
    handlers = {
        "shape": commands.shape_cmd.handle_shape,
        "fields": commands.fields_cmd.handle_fields,
        "ls": commands.ls_cmd.handle_ls,
        "get": commands.get_cmd.handle_get,
        "query": commands.query_cmd.handle_query,
        "add": commands.add_cmd.handle_add,
        "del": commands.del_cmd.handle_del,
        "set": commands.set_cmd.handle_set,
        "append": commands.append_cmd.handle_append,
        "extract": commands.extract_cmd.handle_extract,
        "extend": commands.extend_cmd.handle_extend,
        "concat": commands.concat_cmd.handle_concat,
        "cutline": commands.cutline_cmd.handle_cutline,
        "replaceline": commands.replaceline_cmd.handle_replaceline,
    }
    handler = handlers.get(command)
    if handler is None:
        print(f"Unknown command: {command}", file=sys.stderr)
        return 1
    return handler(args)


if __name__ == "__main__":
    sys.exit(main())
