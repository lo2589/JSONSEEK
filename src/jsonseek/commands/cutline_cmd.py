import argparse
from typing import Optional

from ..io.encoding import resolve_encoding
from ..errors import JsonseekError


def handle_cutline(args: argparse.Namespace) -> int:
    try:
        line_number = args.line
        path = args.file
        enc = args.encoding or resolve_encoding(path, None)
        
        content = cut_line(path, line_number, enc)
        
        if args.save_temp:
            import tempfile
            import os
            suffix = '.jsonline'
            fd, tmp_path = tempfile.mkstemp(suffix=suffix, text=True)
            with os.fdopen(fd, 'w', encoding=enc) as f:
                f.write(content)
            print(tmp_path)
        else:
            print(content)
        return 0
    except JsonseekError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


def cut_line(path: str, line_number: int, encoding: Optional[str] = None) -> str:
    """Extract a specific line from a file (1-indexed)."""
    enc = encoding or resolve_encoding(path, None)
    try:
        with open(path, "r", encoding=enc) as f:
            for i, line in enumerate(f, 1):
                if i == line_number:
                    return line.rstrip('\n\r')
    except FileNotFoundError:
        raise JsonseekError(f"File not found: {path}")
    except OSError as e:
        raise JsonseekError(f"Failed to read {path}: {e}")
    
    raise JsonseekError(f"Line {line_number} not found in {path}")
