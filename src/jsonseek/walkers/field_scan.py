from typing import Any, Dict, List

from ..types import FieldStat, JsonlRecord
from ..value_utils import stable_type_name
from .tree_walk import walk_tree


def scan_fields_in_tree(data: Any) -> Dict[str, FieldStat]:
    """Scan a JSON tree and return field stats keyed by field name."""
    stats: Dict[str, FieldStat] = {}
    for path, value in walk_tree(data):
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}" if path else key
                _update_stat(stats, key, child_path, child)
    return stats


def _update_stat(stats: Dict[str, FieldStat], field: str, path: str, value: Any) -> None:
    if field not in stats:
        stats[field] = FieldStat(field=field, paths=[], types=[], count=0)
    stat = stats[field]
    if path not in stat.paths:
        stat.paths.append(path)
    t = stable_type_name(value)
    if t not in stat.types:
        stat.types.append(t)
    stat.count = (stat.count or 0) + 1


def scan_fields_in_record(record: JsonlRecord) -> Dict[str, FieldStat]:
    """Scan a single JSONL record and return field stats."""
    return scan_fields_in_tree(record.data)


def merge_field_stats(acc: Dict[str, FieldStat], inc: Dict[str, FieldStat]) -> Dict[str, FieldStat]:
    """Merge incremental record stats into accumulated stats."""
    for field, stat in inc.items():
        if field not in acc:
            acc[field] = FieldStat(field=field, paths=[], types=[], record_count=0)
        target = acc[field]
        for p in stat.paths:
            if p not in target.paths:
                target.paths.append(p)
        for t in stat.types:
            if t not in target.types:
                target.types.append(t)
        target.record_count = (target.record_count or 0) + 1
    return acc


def finalize_jsonl_field_stats(stats: Dict[str, FieldStat], total_records: int) -> List[FieldStat]:
    """Finalize JSONL field stats by computing coverage."""
    result: List[FieldStat] = []
    for stat in stats.values():
        rc = stat.record_count or 0
        stat.coverage = rc / total_records if total_records > 0 else 0.0
        result.append(stat)
    return result
