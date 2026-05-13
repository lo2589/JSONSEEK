import json
import os
import shutil
from typing import Any, Optional

from ..errors import JsonseekError
from .encoding import resolve_encoding


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


def _format_json_error(path: str, e: json.JSONDecodeError, encoding: str) -> str:
    """Format a JSON decode error with line content."""
    line = e.lineno or 0
    col = e.colno or 0
    line_content = _get_line_content(path, line, encoding)
    
    msg = f"Invalid JSON at line {line} in {path}\n"
    msg += f"  Line {line}: {line_content}\n"
    msg += f"  {e.msg}"
    
    return msg


def _format_encoding_error(path: str, e: Exception, detected: str) -> str:
    """Format an encoding/decoding error with context."""
    msg = f"Encoding error in {path}\n"
    msg += f"  Detected encoding: {detected}\n"
    msg += f"  Error: {e}\n"
    msg += f"  Hint: Try specifying the correct encoding with --encoding (e.g. --encoding gbk)\n"
    
    # Try to show raw byte preview around the error position
    try:
        with open(path, "rb") as f:
            raw = f.read(200)
        # Show hex dump of first 200 bytes
        hex_preview = raw[:64].hex(' ')
        msg += f"  Raw bytes (hex): {hex_preview}"
        if len(raw) > 64:
            msg += " ..."
    except Exception:
        pass
    
    return msg


def load_json_file(path: str, encoding: Optional[str] = None) -> Any:
    """Load a JSON file and return the Python tree.

    If encoding is not specified, auto-detect from BOM or common encodings.
    """
    detected = resolve_encoding(path, encoding)
    try:
        with open(path, "r", encoding=detected) as f:
            return json.load(f)
    except FileNotFoundError:
        raise JsonseekError(f"File not found: {path}")
    except (UnicodeDecodeError, UnicodeError) as e:
        raise JsonseekError(_format_encoding_error(path, e, detected))
    except json.JSONDecodeError as e:
        raise JsonseekError(_format_json_error(path, e, detected))


def dump_json_data(data: Any, pretty: bool = True) -> str:
    """Serialize data to a JSON string."""
    if pretty:
        return json.dumps(data, ensure_ascii=False, indent=2)
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _atomic_replace(src: str, dst: str) -> None:
    """Cross-platform atomic file replace."""
    try:
        os.replace(src, dst)
    except PermissionError:
        if os.name == "nt" and os.path.exists(dst):
            os.remove(dst)
            os.rename(src, dst)
        else:
            raise


def save_json_file(path: str, data: Any, backup: bool = False, encoding: str = "utf-8") -> None:
    """Save data to a JSON file atomically, optionally creating a backup."""
    if backup and os.path.exists(path):
        backup_path = path + ".bak"
        shutil.copy2(path, backup_path)

    temp_path = path + ".tmp"
    try:
        content = dump_json_data(data, pretty=True)
        with open(temp_path, "w", encoding=encoding, newline="\n") as f:
            f.write(content)
            f.write("\n")
        _atomic_replace(temp_path, path)
    except OSError as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise JsonseekError(f"Failed to write {path}: {e}")
