import argparse
from typing import Optional

from ..io.encoding import resolve_encoding
from ..errors import JsonseekError


def handle_replaceline(args: argparse.Namespace) -> int:
    try:
        line_number = args.line
        path = args.file
        enc = args.encoding or resolve_encoding(path, None)
        
        # Get content from file or command line
        if args.from_file:
            with open(args.from_file, 'r', encoding=enc) as f:
                content = f.read().strip()
        elif args.content:
            content = args.content
        else:
            print("Error: Must provide content or --from-file", file=__import__("sys").stderr)
            return 1
        
        replace_line(path, line_number, content, enc)
        print(f"Replaced line {line_number}")
        return 0
    except JsonseekError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


def replace_line(path: str, line_number: int, content: str, encoding: Optional[str] = None) -> None:
    """Replace a specific line in a file (1-indexed)."""
    enc = encoding or resolve_encoding(path, None)
    
    try:
        with open(path, "r", encoding=enc) as f:
            lines = f.readlines()
    except FileNotFoundError:
        raise JsonseekError(f"File not found: {path}")
    except OSError as e:
        raise JsonseekError(f"Failed to read {path}: {e}")
    
    # Adjust for 1-indexed line numbers
    index = line_number - 1
    
    if index < 0 or index > len(lines):
        raise JsonseekError(f"Line {line_number} out of range (file has {len(lines)} lines)")
    
    # Replace the content at the index
    lines[index] = content + '\n'
    
    try:
        with open(path, "w", encoding=enc, newline='\n') as f:
            f.writelines(lines)
    except OSError as e:
        raise JsonseekError(f"Failed to write {path}: {e}")
