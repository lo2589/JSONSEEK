import json
from typing import Any, List, Optional, Tuple

from .types import ShapeNode, FieldStat, QueryHit
from .value_utils import short_preview, stable_type_name


def format_shape_result(shape: ShapeNode, output: str = "pretty") -> str:
    if output == "json":
        return json.dumps(_shape_to_dict(shape), ensure_ascii=False, indent=2)
    return _format_shape_pretty(shape, indent=0)


def _shape_to_dict(node: ShapeNode) -> dict:
    return {
        "path": node.path,
        "node_kind": node.node_kind,
        "children": [_shape_to_dict(c) for c in node.children],
        "sample_types": node.sample_types,
        "count": node.count,
    }


def _format_shape_pretty(node: ShapeNode, indent: int) -> str:
    prefix = "  " * indent
    type_hint = ""
    if node.sample_types:
        type_hint = f"  ({', '.join(node.sample_types)})"
    count_hint = ""
    if node.count is not None:
        count_hint = f" [{node.count}]"
    lines = [f"{prefix}{node.path or '(root)'}{type_hint}{count_hint}"]
    for child in node.children:
        lines.append(_format_shape_pretty(child, indent + 1))
    return "\n".join(lines)


def format_fields_result(fields: List[FieldStat], output: str = "pretty") -> str:
    if output == "json":
        data = [
            {
                "field": f.field,
                "paths": f.paths,
                "types": f.types,
                "count": f.count,
                "record_count": f.record_count,
                "coverage": f.coverage,
            }
            for f in fields
        ]
        return json.dumps(data, ensure_ascii=False, indent=2)
    lines: List[str] = []
    for f in fields:
        extra = ""
        if f.coverage is not None:
            extra = f"  coverage={f.coverage:.1%}"
        elif f.count is not None:
            extra = f"  count={f.count}"
        lines.append(f"{f.field}  types={','.join(f.types)}  paths={len(f.paths)}{extra}")
    return "\n".join(lines)


def format_ls_result(value: Any, output: str = "pretty") -> str:
    if output == "json":
        return json.dumps(value, ensure_ascii=False, indent=2)
    if value is None:
        return "null"
    if isinstance(value, dict):
        lines: List[str] = []
        for k, v in value.items():
            t = stable_type_name(v)
            preview = short_preview(v, max_len=60)
            lines.append(f"{k:<20} {t:<10} {preview}")
        return "\n".join(lines)
    if isinstance(value, list):
        lines = []
        for i, v in enumerate(value):
            t = stable_type_name(v)
            preview = short_preview(v, max_len=60)
            lines.append(f"[{i}]  {t:<10} {preview}")
        return "\n".join(lines)
    return short_preview(value)


def format_get_result(value: Any, output: str = "pretty") -> str:
    if output == "json":
        return json.dumps(value, ensure_ascii=False, indent=2)
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False, indent=2)
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def format_query_result(hits: List[QueryHit], output: str = "pretty") -> str:
    if output == "json":
        data = [
            {
                "path": h.path,
                "match_type": h.match_type,
                "matched_on": h.matched_on,
                "value": h.value,
                "record_index": h.record_index,
                "line_number": h.line_number,
                "record_id": h.record_id,
                "preview": h.preview,
            }
            for h in hits
        ]
        return json.dumps(data, ensure_ascii=False, indent=2)
    lines: List[str] = []
    for h in hits:
        meta = ""
        if h.record_index is not None:
            meta += f" record={h.record_index}"
        if h.line_number is not None:
            meta += f" line={h.line_number}"
        if h.record_id is not None:
            meta += f" id={h.record_id}"
        lines.append(f"{h.path}  [{h.match_type}] {h.matched_on!r}{meta}")
    return "\n".join(lines)


def format_extract_result(results: List[Any], output: str = "pretty") -> str:
    if output == "json":
        return json.dumps(results, ensure_ascii=False, indent=2, default=str)
    lines: List[str] = []
    for r in results:
        if not r.get("ok"):
            error = r.get("error", "")
            tag = "[skipped]" if error.startswith("Skipped:") else "[missing]"
            lines.append(f"{r['file']:<40} {tag} {error}")
            continue
        value = r["value"]
        if isinstance(value, (dict, list)):
            preview = json.dumps(value, ensure_ascii=False, default=str)
            if len(preview) > 60:
                preview = preview[:57] + "..."
        elif value is None:
            preview = "null"
        elif isinstance(value, bool):
            preview = "true" if value else "false"
        else:
            preview = str(value)
        lines.append(f"{r['file']:<40} {preview}")
    return "\n".join(lines)


def format_patch_result(message: str, output: str = "pretty") -> str:
    if output == "json":
        return json.dumps({"ok": True, "message": message}, ensure_ascii=False)
    return message


def _value_repr(value: Any) -> str:
    """Return a compact string representation of a value."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        preview = json.dumps(value, ensure_ascii=False)
        if len(preview) > 200:
            preview = preview[:197] + "..."
        return preview
    if isinstance(value, str):
        return repr(value)
    return str(value)


def format_patch_preview(
    path: str,
    before: Any = None,
    after: Any = None,
    output: str = "pretty",
    dry_run: bool = False,
    jsonl_before: Optional[List[Tuple[int, str]]] = None,
    jsonl_after: Optional[List[Tuple[int, str]]] = None,
    jsonl_target_line: Optional[int] = None,
    operation: str = "modified",
) -> str:
    """Format before/after preview for patch commands.
    
    Args:
        path: Target path being modified.
        before: Original value (for JSON).
        after: New value (for JSON).
        output: "pretty" or "json".
        dry_run: Whether this is a dry-run preview.
        jsonl_before: List of (line_num, content) for JSONL before view.
        jsonl_after: List of (line_num, content) for JSONL after view.
        jsonl_target_line: The line number being operated on (for JSONL).
        operation: "modified", "deleted", "added", or "appended".
    """
    if output == "json":
        result: dict = {
            "ok": True,
            "dry_run": dry_run,
            "path": path,
        }
        if jsonl_before is not None:
            result["jsonl_before"] = jsonl_before
            result["jsonl_after"] = jsonl_after
            result["target_line"] = jsonl_target_line
        else:
            result["before"] = before if before is not None else None
            result["after"] = after if after is not None else None
        return json.dumps(result, ensure_ascii=False, default=str)

    # Pretty output
    lines: List[str] = []
    prefix = "[DRY-RUN] " if dry_run else ""

    if jsonl_before is not None:
        # JSONL context mode
        if operation == "modified":
            tag_before = " [TO BE MODIFIED]"
            tag_after = " [MODIFIED]"
        elif operation == "deleted":
            tag_before = " [TO BE DELETED]"
            tag_after = ""
        elif operation == "appended":
            tag_before = ""
            tag_after = " [APPENDED]"
        else:
            tag_before = ""
            tag_after = ""

        lines.append(f"{prefix}Before:")
        for num, content in jsonl_before:
            marker = ">>>" if num == jsonl_target_line else "   "
            tag = tag_before if num == jsonl_target_line else ""
            lines.append(f"{marker}{num}: {content}{tag}")

        if jsonl_after is not None:
            lines.append("")
            lines.append(f"{prefix}After:")
            for num, content in jsonl_after:
                if operation == "deleted":
                    # Deleted: no target marker, lines just shift up
                    marker = "   "
                    tag = ""
                else:
                    marker = ">>>" if num == jsonl_target_line else "   "
                    tag = tag_after if num == jsonl_target_line else ""
                lines.append(f"{marker}{num}: {content}{tag}")
    else:
        # JSON value mode
        before_str = _value_repr(before) if before is not None else "<not found>"
        after_str = _value_repr(after) if after is not None else "<not found>"
        lines.append(f"{prefix}Before: {path} = {before_str}")
        lines.append(f"{prefix}After:  {path} = {after_str}")

    if dry_run:
        lines.append("")
        lines.append("(Dry run, no changes made)")

    return "\n".join(lines)
