import json
from typing import Any, Iterator, List, Optional, Tuple

from ..types import JsonlRecord
from ..errors import JsonseekError
from .encoding import resolve_encoding
from .json_file import _format_encoding_error


def _get_line_content(path: str, line_number: int, encoding: str) -> str:
    """Get the content of a specific line (1-indexed)."""
    try:
        with open(path, "r", encoding=encoding) as f:
            for i, line in enumerate(f, 1):
                if i == line_number:
                    return line.rstrip('\n\r')
    except Exception:
        pass
    return ""


def iter_jsonl_records(path: str, encoding: Optional[str] = None, collect_errors: bool = False) -> Iterator[JsonlRecord]:
    """Iterate over JSONL records, yielding JsonlRecord objects.
    
    If collect_errors is True, collect all parse errors instead of raising on first.
    """
    detected = resolve_encoding(path, encoding)
    errors = []
    try:
        with open(path, "r", encoding=detected) as f:
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
                    if collect_errors:
                        errors.append((line_number, stripped, str(e)))
                        continue
                    else:
                        raise JsonseekError(_format_jsonl_error(path, line_number, stripped, e))
                yield JsonlRecord(record_index=record_index, line_number=line_number, data=data)
                record_index += 1
    except FileNotFoundError:
        raise JsonseekError(f"File not found: {path}")
    except (UnicodeDecodeError, UnicodeError) as e:
        raise JsonseekError(_format_encoding_error(path, e, detected))
    except OSError as e:
        raise JsonseekError(f"Failed to read {path}: {e}")
    
    if errors:
        raise JsonseekError(_format_multi_jsonl_error(path, errors))


def _format_jsonl_error(path: str, line_number: int, line_content: str, e: json.JSONDecodeError) -> str:
    """Format a single JSONL decode error."""
    msg = f"Invalid JSON at line {line_number} in {path}\n"
    msg += f"  Line {line_number}: {line_content}\n"
    msg += f"  {e.msg}"
    return msg


def _format_multi_jsonl_error(path: str, errors: List[tuple]) -> str:
    """Format multiple JSONL decode errors."""
    msg = f"Found {len(errors)} invalid lines in {path}:\n"
    for line_num, content, error in errors:
        msg += f"  Line {line_num}: {content}\n"
        msg += f"    Error: {error}\n"
    return msg


def get_all_jsonl_errors(path: str, encoding: Optional[str] = None) -> List[Tuple[int, str, str]]:
    """Collect all JSON parsing errors in a JSONL file."""
    detected = resolve_encoding(path, encoding)
    errors = []
    try:
        with open(path, "r", encoding=detected) as f:
            for line_number, line in enumerate(f, 1):
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    json.loads(stripped)
                except json.JSONDecodeError as e:
                    errors.append((line_number, stripped, e.msg))
    except (UnicodeDecodeError, UnicodeError) as e:
        raise JsonseekError(_format_encoding_error(path, e, detected))
    except Exception:
        pass
    return errors


def validate_jsonl_file(path: str, encoding: Optional[str] = None) -> None:
    """Validate a JSONL file and raise if any errors found."""
    errors = get_all_jsonl_errors(path, encoding)
    if errors:
        raise JsonseekError(_format_multi_jsonl_error(path, errors))


def load_jsonl_sample(path: str, limit: int = 100, encoding: Optional[str] = None) -> List[JsonlRecord]:
    """Load up to `limit` records from a JSONL file."""
    results: List[JsonlRecord] = []
    for record in iter_jsonl_records(path, encoding=encoding):
        results.append(record)
        if len(results) >= limit:
            break
    return results


def get_jsonl_record_by_index(path: str, record_index: int, encoding: Optional[str] = None) -> JsonlRecord:
    """Get a specific record by index from a JSONL file."""
    for record in iter_jsonl_records(path, encoding=encoding):
        if record.record_index == record_index:
            return record
    raise JsonseekError(f"Record index {record_index} not found in {path}")


def get_line_context(path: str, target_line: int, context: int = 2, encoding: Optional[str] = None) -> List[Tuple[int, str]]:
    """Return lines around target_line with context. 1-indexed.
    
    Returns list of (line_number, content) tuples.
    """
    detected = resolve_encoding(path, encoding)
    start = max(1, target_line - context)
    end = target_line + context
    result: List[Tuple[int, str]] = []
    try:
        with open(path, "r", encoding=detected) as f:
            for i, line in enumerate(f, 1):
                if i < start:
                    continue
                if i > end:
                    break
                result.append((i, line.rstrip('\n\r')))
    except FileNotFoundError:
        raise JsonseekError(f"File not found: {path}")
    except OSError as e:
        raise JsonseekError(f"Failed to read {path}: {e}")
    return result


def append_jsonl_record(path: str, value: Any, encoding: str = "utf-8") -> None:
    """Append a single JSON record to a JSONL file."""
    try:
        line = json.dumps(value, ensure_ascii=False)
        with open(path, "a", encoding=encoding, newline="\n") as f:
            f.write(line)
            f.write("\n")
    except OSError as e:
        raise JsonseekError(f"Failed to append to {path}: {e}")
