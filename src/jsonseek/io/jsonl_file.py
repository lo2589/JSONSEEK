import json
from typing import Any, Iterator, List

from ..types import JsonlRecord
from ..errors import JsonseekError


def iter_jsonl_records(path: str) -> Iterator[JsonlRecord]:
    """Iterate over JSONL records, yielding JsonlRecord objects."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            line_number = 0
            record_index = 0
            for line in f:
                line_number += 1
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    data = json.loads(stripped)
                except json.JSONDecodeError as e:
                    raise JsonseekError(f"Invalid JSON at line {line_number} in {path}: {e}")
                yield JsonlRecord(record_index=record_index, line_number=line_number, data=data)
                record_index += 1
    except FileNotFoundError:
        raise JsonseekError(f"File not found: {path}")
    except OSError as e:
        raise JsonseekError(f"Failed to read {path}: {e}")


def load_jsonl_sample(path: str, limit: int = 100) -> List[JsonlRecord]:
    """Load up to `limit` records from a JSONL file."""
    results: List[JsonlRecord] = []
    for record in iter_jsonl_records(path):
        results.append(record)
        if len(results) >= limit:
            break
    return results


def get_jsonl_record_by_index(path: str, record_index: int) -> JsonlRecord:
    """Get a specific record by index from a JSONL file."""
    for record in iter_jsonl_records(path):
        if record.record_index == record_index:
            return record
    raise JsonseekError(f"Record index {record_index} not found in {path}")


def append_jsonl_record(path: str, value: Any) -> None:
    """Append a single JSON record to a JSONL file."""
    try:
        line = json.dumps(value, ensure_ascii=False)
        with open(path, "a", encoding="utf-8", newline="\n") as f:
            f.write(line)
            f.write("\n")
    except OSError as e:
        raise JsonseekError(f"Failed to append to {path}: {e}")
