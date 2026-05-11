import argparse
import glob
import json
import os
import shutil
from typing import Any, List

from ..errors import JsonseekError
from ..io.encoding import resolve_encoding
from ..io.json_file import load_json_file


def handle_concat(args: argparse.Namespace) -> int:
    try:
        pattern = args.pattern
        output_file = getattr(args, "output_file", None)
        no_sort = getattr(args, "no_sort", False)

        # Expand glob pattern
        files = glob.glob(pattern, recursive=True)
        if not no_sort:
            files = sorted(files)
        if not files:
            if os.path.isfile(pattern):
                files = [pattern]
            else:
                print(f"No files matched pattern: {pattern}", file=__import__("sys").stderr)
                return 1

        enc = getattr(args, "encoding", None)
        lines: List[str] = []

        for path in files:
            try:
                data = load_json_file(path, encoding=enc)
                line = json.dumps(data, ensure_ascii=False)
                lines.append(line)
            except JsonseekError as e:
                print(f"Error processing {path}: {e}", file=__import__("sys").stderr)
                return 1

        output = "\n".join(lines)
        if output_file:
            _write_file(output_file, output, enc or "utf-8")
            print(f"Wrote {len(lines)} record(s) to {output_file}")
        else:
            print(output)

        return 0
    except JsonseekError as e:
        print(f"Error: {e}", file=__import__("sys").stderr)
        return 1


def _write_file(path: str, content: str, encoding: str) -> None:
    """Write content to a file atomically."""
    temp_path = path + ".tmp"
    try:
        with open(temp_path, "w", encoding=encoding, newline="\n") as f:
            f.write(content)
            f.write("\n")
        try:
            os.replace(temp_path, path)
        except PermissionError:
            if os.name == "nt" and os.path.exists(path):
                os.remove(path)
                os.rename(temp_path, path)
            else:
                raise
    except OSError as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise JsonseekError(f"Failed to write {path}: {e}")
