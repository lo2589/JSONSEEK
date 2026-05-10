import json
from typing import Any, List

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


def format_patch_result(message: str, output: str = "pretty") -> str:
    if output == "json":
        return json.dumps({"ok": True, "message": message}, ensure_ascii=False)
    return message
