import argparse
import sys
from typing import Any, Dict, List, Optional

from ..detect import detect_file_kind
from ..io.json_file import load_json_file
from ..io.jsonl_file import iter_jsonl_records
from ..value_utils import infer_node_kind
from ..formatters import format_diff_result
from ..errors import JsonseekError

# diff 条目 kind：
#   added         -> 只在 B（右）出现
#   removed       -> 只在 A（左）出现
#   value_changed -> 两边同类型，标量值不同
#   type_changed  -> 两边都有，但 JSON 类型不同
_MODE_KINDS = {
    "structure": {"added", "removed", "type_changed"},
    "content": {"value_changed", "type_changed"},
    "both": {"added", "removed", "value_changed", "type_changed"},
}


def _join(path: str, key: str) -> str:
    return f"{path}.{key}" if path else key


def _index(path: str, i: int) -> str:
    return f"{path}[{i}]"


def diff_values(a: Any, b: Any, path: str = "") -> List[Dict[str, Any]]:
    """Recursively diff two JSON values. Returns a flat list of entries
    {kind, path, before, after}. Paths use jsonseek path syntax (a.b, a[0])."""
    ka, kb = infer_node_kind(a), infer_node_kind(b)

    if ka != kb:
        return [{"kind": "type_changed", "path": path, "before": a, "after": b}]

    if ka == "object":
        entries: List[Dict[str, Any]] = []
        for key in a:                                  # removed / recurse (A 顺序优先)
            child = _join(path, key)
            if key not in b:
                entries.append({"kind": "removed", "path": child, "before": a[key], "after": None})
            else:
                entries.extend(diff_values(a[key], b[key], child))
        for key in b:                                  # added
            if key not in a:
                entries.append({"kind": "added", "path": _join(path, key), "before": None, "after": b[key]})
        return entries

    if ka == "array":
        entries = []
        n = min(len(a), len(b))
        for i in range(n):
            entries.extend(diff_values(a[i], b[i], _index(path, i)))
        for i in range(n, len(a)):
            entries.append({"kind": "removed", "path": _index(path, i), "before": a[i], "after": None})
        for i in range(n, len(b)):
            entries.append({"kind": "added", "path": _index(path, i), "before": None, "after": b[i]})
        return entries

    # 标量（同类型）
    if a != b:
        return [{"kind": "value_changed", "path": path, "before": a, "after": b}]
    return []


def filter_by_mode(diffs: List[Dict[str, Any]], mode: str) -> List[Dict[str, Any]]:
    kinds = _MODE_KINDS.get(mode, _MODE_KINDS["both"])
    return [d for d in diffs if d["kind"] in kinds]


def load_side(file: str, kind_hint: Optional[str], encoding: Optional[str]) -> Any:
    kind = detect_file_kind(file, kind_hint=kind_hint)
    if kind == "jsonl":
        return [r.data for r in iter_jsonl_records(file, encoding=encoding)]
    return load_json_file(file, encoding=encoding)


def handle_diff(args: argparse.Namespace) -> int:
    try:
        enc = getattr(args, "encoding", None)
        kind_hint = getattr(args, "kind", None)
        a = load_side(args.file_a, kind_hint, enc)
        b = load_side(args.file_b, kind_hint, enc)
        diffs = filter_by_mode(diff_values(a, b), getattr(args, "mode", "both"))
        max_results = getattr(args, "max_results", None)
        truncated = False
        if max_results is not None and len(diffs) > max_results:
            diffs = diffs[:max_results]
            truncated = True
        print(format_diff_result(
            diffs, args.file_a, args.file_b,
            mode=getattr(args, "mode", "both"),
            output=getattr(args, "output", "pretty"),
            truncated=truncated,
        ))
        return 0
    except JsonseekError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
