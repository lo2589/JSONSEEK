from typing import Any, List, Optional

from ..types import QueryHit, JsonlRecord
from ..value_utils import short_preview
from ..path_parser import is_parent_path
from .tree_walk import walk_tree


def scan_query_hits_in_tree(
    data: Any,
    term: str,
    *,
    case_sensitive: bool = False,
    exact: bool = False,
    match_mode: str = "both",
) -> List[QueryHit]:
    """Search for term matches in a JSON tree."""
    raw_hits = _collect_raw_hits(data, term, case_sensitive=case_sensitive, exact=exact, match_mode=match_mode)
    return _dedupe_overlapping_hits(raw_hits)


def scan_query_hits_in_record(
    record: JsonlRecord,
    term: str,
    *,
    case_sensitive: bool = False,
    exact: bool = False,
    match_mode: str = "both",
    record_id_field: Optional[str] = None,
    preview_field: Optional[str] = None,
) -> List[QueryHit]:
    """Search for term matches within a single JSONL record."""
    raw_hits = _collect_raw_hits(record.data, term, case_sensitive=case_sensitive, exact=exact, match_mode=match_mode)
    deduped = _dedupe_overlapping_hits(raw_hits)
    return _attach_record_meta(deduped, record, record_id_field, preview_field)


def _collect_raw_hits(
    data: Any,
    term: str,
    case_sensitive: bool,
    exact: bool,
    match_mode: str,
) -> List[QueryHit]:
    hits: List[QueryHit] = []
    cmp_term = term if case_sensitive else term.lower()

    for path, value in walk_tree(data):
        val_str = _to_searchable_str(value)
        val_cmp = val_str if case_sensitive else val_str.lower()
        key_match = False
        val_match = False
        last_key = _last_path_segment(path)
        last_key_cmp = last_key if case_sensitive else last_key.lower()

        if match_mode in ("both", "key"):
            if exact:
                key_match = last_key_cmp == cmp_term
            else:
                key_match = cmp_term in last_key_cmp

        if match_mode in ("both", "value"):
            if isinstance(value, (dict, list)):
                val_match = False
            else:
                if exact:
                    val_match = val_cmp == cmp_term
                else:
                    val_match = cmp_term in val_cmp

        if key_match:
            hits.append(QueryHit(
                path=path,
                match_type="key",
                matched_on=last_key,
                value=value,
            ))
        if val_match:
            hits.append(QueryHit(
                path=path,
                match_type="value",
                matched_on=val_str,
                value=value,
            ))

    return hits


def _dedupe_overlapping_hits(hits: List[QueryHit]) -> List[QueryHit]:
    """Remove hits that are children of already-hit paths."""
    # Sort by path depth (shallow first), then by path string for stability
    sorted_hits = sorted(hits, key=lambda h: (len(h.path.split(".")), h.path))
    kept: List[QueryHit] = []
    for hit in sorted_hits:
        covered = any(is_parent_path(k.path, hit.path) and k.path != hit.path for k in kept)
        if not covered:
            kept.append(hit)
    return kept


def _attach_record_meta(
    hits: List[QueryHit],
    record: JsonlRecord,
    record_id_field: Optional[str],
    preview_field: Optional[str],
) -> List[QueryHit]:
    record_id = None
    if record_id_field and isinstance(record.data, dict):
        record_id = str(record.data.get(record_id_field)) if record.data.get(record_id_field) is not None else None

    preview = None
    if preview_field and isinstance(record.data, dict):
        pv = record.data.get(preview_field)
        if pv is not None:
            preview = short_preview(pv)

    for hit in hits:
        hit.record_index = record.record_index
        hit.line_number = record.line_number
        hit.record_id = record_id
        hit.preview = preview
    return hits


def _to_searchable_str(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _last_path_segment(path: str) -> str:
    if not path:
        return ""
    # Handle both "a.b[0]" -> last segment before bracket, and "a.b.c" -> "c"
    # For query key matching, we want the immediate key name
    if "." in path:
        return path.rsplit(".", 1)[-1].split("[")[0]
    return path.split("[")[0]
