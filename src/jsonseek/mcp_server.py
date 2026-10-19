"""Zero-dependency stdio MCP server for jsonseek.

Every tool maps onto one jsonseek command and returns that command's
``--output json`` result, so agents get the same answers as the CLI.

Usage (add to .mcp.json):
  {
    "mcpServers": {
      "jsonseek": {"command": "jsonseek-mcp"}
    }
  }
"""

from __future__ import annotations

import contextlib
import io
import json
import sys
from typing import Any, Callable, Dict, List, Optional

from . import __version__
from .cli import main as cli_main


_COMMON = {
    "file": {"type": "string", "description": "Path to the JSON or JSONL file"},
    "kind": {
        "type": "string",
        "enum": ["json", "jsonl"],
        "description": "Force file kind (auto-detected by default)",
    },
    "encoding": {"type": "string", "description": "File encoding (auto-detected by default)"},
}

_WRITE = {
    "dry_run": {
        "type": "boolean",
        "default": False,
        "description": "Preview the change without writing the file",
    },
    "backup": {
        "type": "boolean",
        "default": False,
        "description": "Write a .bak copy before changing the file",
    },
}

_PATH = {"type": "string", "description": "jsonseek path, e.g. users[0].name or [3].status for JSONL"}
_VALUE = {"type": "string", "description": "JSON text or a bare literal"}


def _schema(properties: Dict[str, Any], required: List[str]) -> Dict[str, Any]:
    return {"type": "object", "properties": properties, "required": required}


TOOLS = [
    {
        "name": "shape",
        "description": (
            "Show the skeleton of a JSON/JSONL file: keys, types, array sizes, and "
            "broken JSONL lines. Run this first instead of reading the whole file."
        ),
        "inputSchema": _schema(
            {
                **_COMMON,
                "max_depth": {"type": "integer", "minimum": 0},
                "sample_size": {"type": "integer", "minimum": 1, "default": 100},
            },
            ["file"],
        ),
    },
    {
        "name": "fields",
        "description": "List field paths and their types, optionally filtered by keyword.",
        "inputSchema": _schema(
            {
                **_COMMON,
                "keyword": {"type": "string"},
                "top": {"type": "boolean", "default": False, "description": "Top-level fields only"},
            },
            ["file"],
        ),
    },
    {
        "name": "ls",
        "description": "List the direct children at a path (root by default).",
        "inputSchema": _schema({**_COMMON, "path": _PATH}, ["file"]),
    },
    {
        "name": "get",
        "description": "Return the value at a path.",
        "inputSchema": _schema({**_COMMON, "path": _PATH}, ["file", "path"]),
    },
    {
        "name": "query",
        "description": "Search keys and/or values; returns matching paths (and JSONL line numbers).",
        "inputSchema": _schema(
            {
                **_COMMON,
                "term": {"type": "string"},
                "match_mode": {"type": "string", "enum": ["key", "value", "both"], "default": "both"},
                "exact": {"type": "boolean", "default": False},
                "case_sensitive": {"type": "boolean", "default": False},
                "max_results": {"type": "integer", "minimum": 1},
            },
            ["file", "term"],
        ),
    },
    {
        "name": "set",
        "description": "Set the value at a path. Only the touched bytes change on disk.",
        "inputSchema": _schema(
            {
                **_COMMON,
                **_WRITE,
                "path": _PATH,
                "value": _VALUE,
                "create_missing": {"type": "boolean", "default": False},
            },
            ["file", "path", "value"],
        ),
    },
    {
        "name": "add",
        "description": "Add a new key to an object. Fails if the key already exists.",
        "inputSchema": _schema(
            {
                **_COMMON,
                **_WRITE,
                "path": _PATH,
                "value": _VALUE,
                "create_missing": {"type": "boolean", "default": False},
            },
            ["file", "path", "value"],
        ),
    },
    {
        "name": "delete",
        "description": "Delete a key or array element at a path.",
        "inputSchema": _schema({**_COMMON, **_WRITE, "path": _PATH}, ["file", "path"]),
    },
    {
        "name": "append",
        "description": (
            "Append to an array (JSON: path + value) or append a record to a JSONL file "
            "(JSONL: value only)."
        ),
        "inputSchema": _schema(
            {**_COMMON, **_WRITE, "path": _PATH, "value": _VALUE},
            ["file", "value"],
        ),
    },
    {
        "name": "replace_line",
        "description": "Replace one line of a file (1-indexed). Use it to repair a broken JSONL record.",
        "inputSchema": _schema(
            {
                "file": _COMMON["file"],
                "encoding": _COMMON["encoding"],
                "line": {"type": "integer", "minimum": 1},
                "content": {"type": "string"},
            },
            ["file", "line", "content"],
        ),
    },
    {
        "name": "cut_line",
        "description": "Return one line of a file (1-indexed) without reading the rest.",
        "inputSchema": _schema(
            {
                "file": _COMMON["file"],
                "encoding": _COMMON["encoding"],
                "line": {"type": "integer", "minimum": 1},
            },
            ["file", "line"],
        ),
    },
]


def _common_args(arguments: Dict[str, Any], *, output: bool = True) -> List[str]:
    argv = [arguments["file"]]
    if output:
        argv += ["--output", "json"]
    if arguments.get("kind"):
        argv += ["--kind", arguments["kind"]]
    if arguments.get("encoding"):
        argv += ["--encoding", arguments["encoding"]]
    if arguments.get("dry_run"):
        argv.append("--dry-run")
    if arguments.get("backup"):
        argv.append("--backup")
    return argv


def _flag(arguments: Dict[str, Any], key: str, flag: str) -> List[str]:
    return [flag] if arguments.get(key) else []


def _option(arguments: Dict[str, Any], key: str, flag: str) -> List[str]:
    value = arguments.get(key)
    return [] if value is None else [flag, str(value)]


def _argv_shape(a):
    return ["shape", *_common_args(a), *_option(a, "max_depth", "--max-depth"),
            *_option(a, "sample_size", "--sample-size")]


def _argv_fields(a):
    keyword = [a["keyword"]] if a.get("keyword") else []
    return ["fields", *_common_args(a), *keyword, *_flag(a, "top", "--top")]


def _argv_ls(a):
    return ["ls", *_common_args(a), a.get("path", "")]


def _argv_get(a):
    return ["get", *_common_args(a), a["path"]]


def _argv_query(a):
    return ["query", *_common_args(a), a["term"],
            *_option(a, "match_mode", "--match-mode"),
            *_flag(a, "exact", "--exact"),
            *_flag(a, "case_sensitive", "--case-sensitive"),
            *_option(a, "max_results", "--max-results")]


def _argv_set(a):
    return ["set", *_common_args(a), a["path"], a["value"],
            *_flag(a, "create_missing", "--create-missing")]


def _argv_add(a):
    return ["add", *_common_args(a), a["path"], a["value"],
            *_flag(a, "create_missing", "--create-missing")]


def _argv_delete(a):
    return ["del", *_common_args(a), a["path"], "--yes"]


def _argv_append(a):
    if a.get("path"):
        return ["append", *_common_args(a), a["path"], a["value"]]
    return ["append", *_common_args(a), a["value"]]


def _argv_replace_line(a):
    return ["replaceline", a["file"], str(a["line"]), a["content"],
            *_option(a, "encoding", "--encoding")]


def _argv_cut_line(a):
    return ["cutline", a["file"], str(a["line"]), *_option(a, "encoding", "--encoding")]


ARGV_BUILDERS: Dict[str, Callable[[Dict[str, Any]], List[str]]] = {
    "shape": _argv_shape,
    "fields": _argv_fields,
    "ls": _argv_ls,
    "get": _argv_get,
    "query": _argv_query,
    "set": _argv_set,
    "add": _argv_add,
    "delete": _argv_delete,
    "append": _argv_append,
    "replace_line": _argv_replace_line,
    "cut_line": _argv_cut_line,
}


def run_tool(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    """Run one jsonseek command in-process and capture what it prints."""
    argv = ARGV_BUILDERS[name](arguments)
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        try:
            code = cli_main(argv)
        except SystemExit as exc:  # argparse errors
            code = exc.code if isinstance(exc.code, int) else 2
    return {"exit_code": code or 0, "stdout": stdout.getvalue(), "stderr": stderr.getvalue()}


def _tool_result(name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    run = run_tool(name, arguments)
    text = run["stdout"].strip()
    if run["stderr"].strip():
        text = (text + "\n" if text else "") + run["stderr"].strip()
    result: Dict[str, Any] = {
        "content": [{"type": "text", "text": text or "(no output)"}],
        "isError": run["exit_code"] != 0,
    }
    try:
        parsed = json.loads(run["stdout"])
    except ValueError:
        parsed = None
    if isinstance(parsed, dict):
        result["structuredContent"] = parsed
    return result


def _dispatch(message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    method = message.get("method")
    request_id = message.get("id")
    if method == "initialize":
        protocol = (message.get("params") or {}).get("protocolVersion", "2024-11-05")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": protocol,
                "capabilities": {"tools": {"listChanged": False}},
                "serverInfo": {"name": "jsonseek", "version": __version__},
            },
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") or {}
        name = params.get("name")
        if name not in ARGV_BUILDERS:
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32602, "message": f"Unknown tool: {name}"},
            }
        try:
            result = _tool_result(name, params.get("arguments") or {})
        except Exception as exc:
            result = {
                "content": [{"type": "text", "text": f"{type(exc).__name__}: {exc}"}],
                "isError": True,
            }
        return {"jsonrpc": "2.0", "id": request_id, "result": result}
    if request_id is None:
        return None
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": f"Method not found: {method}"},
    }


def main() -> int:
    for line in sys.stdin.buffer:
        if not line.strip():
            continue
        try:
            response = _dispatch(json.loads(line))
        except Exception as exc:
            response = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": f"Internal error: {exc}"},
            }
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
