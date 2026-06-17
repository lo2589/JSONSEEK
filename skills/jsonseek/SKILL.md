---
name: jsonseek
description: Query, inspect, and patch JSON/JSONL files from the command line. Use this skill whenever Kimi needs to read, search, modify, or analyze structured JSON/JSONL data on disk. Triggers include: (1) exploring unknown JSON file structure, (2) finding specific keys or values in JSON/JSONL, (3) editing JSON files (add/remove/update fields), (4) analyzing JSON schema or field coverage, (5) processing JSONL record streams, (6) repairing corrupted JSONL files.
---

# jsonseek Skill

This skill provides fast, local operations on JSON/JSONL without loading entire files into context.

## Quick Start

```bash
# Inspect structure
jsonseek shape data.json

# Search for a keyword
jsonseek query data.json keyword

# Get a value
jsonseek get data.json users[0].name

# Modify JSON
jsonseek set data.json meta.count 99
jsonseek add data.json meta.owner "team-a"
jsonseek del data.json meta.owner

# JSONL operations
jsonseek shape data.jsonl
jsonseek query data.jsonl keyword
jsonseek get data.jsonl '[0].name'
jsonseek set data.jsonl '[0].age' 30
```

## Global Options

| Option | When to use |
|--------|-------------|
| `--output json` | Always use when piping output to another tool or when LLM needs to parse the result |
| `--backup` | Use before any write operation to create `.bak` |
| `--dry-run` | **Always use first** for write commands to preview before applying |
| `--kind {json,jsonl}` | Force file type when auto-detection fails |
| `--encoding ENCODING` | Force encoding when auto-detection fails (e.g. `--encoding gbk`) |
| `--context N` | JSONL preview: show N lines of context around target line (default 2) |

## Core Workflows

### 1. Explore an unknown JSON file

```bash
jsonseek shape file.json          # structure tree
jsonseek fields file.json         # field list with types
jsonseek ls file.json             # list root children
jsonseek ls file.json path        # list children at path
```

`shape` options:
- `--max-depth N` — limit traversal depth
- `--array-mode full` — traverse all array elements instead of sampling
- `--sample-size N` — JSONL: number of records to sample (default 100)

`fields` options:
- `keyword` — filter fields by name
- `--top` — show only top-level fields

### 2. Search for data

```bash
jsonseek query file.json keyword         # key + value match
jsonseek query file.json keyword --exact # exact match only
jsonseek query file.json keyword --match-mode key
jsonseek query file.jsonl keyword --record-id-field id
jsonseek query file.jsonl keyword --max-results 5
```

Query options:
- `--case-sensitive` — case-sensitive matching
- `--exact` — exact match (default is substring)
- `--match-mode {key,value,both}` — what to match (default both)
- `--max-results N` — limit results
- `--record-id-field FIELD` — JSONL: use this field as record ID in output
- `--preview-field FIELD` — JSONL: also show this field as preview

### 3. Read values

```bash
jsonseek get file.json name
jsonseek get file.json items[0].title
jsonseek get file.json a[b][c]         # bracket key syntax
jsonseek get file.jsonl '[0].name'     # JSONL record selector
```

### 4. Edit JSON files

**Always use `--dry-run` first, then commit.**

```bash
jsonseek set file.json path value              # update existing
jsonseek set file.json path value --create-missing
jsonseek add file.json path value              # add new key (object only)
jsonseek del file.json path                    # delete key or array index
jsonseek append file.json array_path value     # append one item to array
jsonseek extend file.json array_path value     # extend array with multiple items (JSON array)
```

Set/add options:
- `--create-missing` — auto-create intermediate paths
- `--from-file FILE` — read value from file (avoids shell quoting issues)

Del options:
- `-y`, `--yes` — skip confirmation

### 5. Edit JSONL files

```bash
jsonseek set file.jsonl '[0].name' "Alice"     # modify record field
jsonseek del file.jsonl '[0].name'             # delete record field
jsonseek del file.jsonl '[2]'                  # delete whole record
jsonseek append file.jsonl '{"name":"new"}'    # append record
```

### 6. Preview changes with --dry-run

Before any write, preview the before/after:

```bash
# JSON
jsonseek set file.json path value --dry-run
# [DRY-RUN] Before: path = old_value
# [DRY-RUN] After:  path = new_value
# (Dry run, no changes made)

# JSONL with line context
jsonseek set file.jsonl '[5].level' "warning" --dry-run
# [DRY-RUN] Before:
# >>>5: {"level":"ERROR"} [TO BE MODIFIED]
#    4: {"level":"INFO"}
# [DRY-RUN] After:
# >>>5: {"level":"WARNING"} [MODIFIED]
#    4: {"level":"INFO"}

# Machine-readable
jsonseek set file.json path value --dry-run --output json
# {"ok":true,"dry_run":true,"path":"...","before":"...","after":"..."}
```

### 7. Repair corrupted JSONL

```bash
# Discover errors (shows invalid lines)
jsonseek shape broken.jsonl

# Extract problematic line
jsonseek cutline broken.jsonl 5 --save-temp
# returns temp file path

# Fix the temp file, then replace back
jsonseek replaceline broken.jsonl 5 --from-file /path/to/fixed.jsonline
```

### 8. Compare two files `diff`

Compare two JSON/JSONL files along **two aspects**: structure (schema) and content (values).

```bash
jsonseek diff a.json b.json                    # both aspects (default)
jsonseek diff a.json b.json --mode structure   # only schema: keys/types added/removed/changed
jsonseek diff a.json b.json --mode content     # only value changes at shared paths
jsonseek diff a.json b.json --output json      # machine-readable
jsonseek diff a.jsonl b.jsonl                  # JSONL: compared record-by-record (by index)
```

Markers (pretty output):

| Marker | Meaning |
|---|---|
| `+ path (type) preview` | added — only in B (right) |
| `- path (type) preview` | removed — only in A (left) |
| `~ path  before -> after` | value changed (same type) |
| `! path  typeA -> typeB` | type changed |

Modes:
- `structure` — `added` / `removed` / `type_changed` (ignores pure value changes)
- `content` — `value_changed` / `type_changed` (ignores key add/remove)
- `both` (default) — all of the above

Notes:
- Paths use jsonseek syntax (`a.b`, `items[0]`), so you can feed a diff path straight into `get`.
- Objects compared by key (whole new/removed subtree collapses to one entry); arrays compared by index.
- Types are JSON kinds (`null/boolean/number/string/array/object`); `1` vs `1.0` is **not** a type change.
- `--max-results N` caps the number of entries; `--kind` forces file kind for both files.
- **`diff` is read-only** — safe to run via CLI on Windows (no shell-quoting issue).

```bash
# JSON output shape
jsonseek diff a.json b.json --output json
# {"identical":false,"mode":"both","files":{...},
#  "summary":{"added":2,"removed":1,"changed":2,"type_changed":1},
#  "truncated":false,"diffs":[{"kind":"value_changed","path":"age","before":30,"after":31}, ...]}
```

### Batch extract

Use `extract PATTERN PATH` to pull the same path from many JSON files:

```bash
jsonseek extract "experiments/*/metrics.json" training.loss
jsonseek extract "configs/*.json" api.endpoint --output json
jsonseek extract "data/**/*.json" meta.version
```

Options:
- `--include-missing` — include files where path does not exist (default skips)

### Concatenate JSON files to JSONL

Use `concat PATTERN` to merge multiple JSON files into a single JSONL file:

```bash
jsonseek concat "experiments/*/result.json" -o combined.jsonl
jsonseek concat "data/*.json" --no-sort -o output.jsonl
```

Options:
- `-o, --output-file` — output file (default stdout)
- `--no-sort` — preserve glob order instead of sorting by filename

## Path Syntax Summary

| Style | Example | Meaning |
|---|---|---|
| Dot notation | `a.b.c` | `a -> b -> c` |
| Bracket keys | `a[key1][key2]` | `a -> key1 -> key2` |
| Mixed | `a[key1].b[0]` | `a -> key1 -> b -> index 0` |
| Array index | `items[0][1]` | `items -> 0 -> 1` |

## Important Notes

- Use `--output json` when piping output to another tool.
- Use `--backup` before write operations to create `.bak`.
- **Use `--dry-run` before any write to preview changes.**
- `append` adds a single item to an array.
- `extend` adds all items from a JSON array to the target array.
- `append` for JSON requires `path value` (array path + value).
- `append` for JSONL only needs `value` (root-level record append).

## Windows Users: Query via CLI, Write via Python API

On Windows PowerShell, **read-only commands** (`shape`, `fields`, `get`, `query`, `ls`, `extract`, `concat`, `diff`) work fine via CLI. However, **write commands** (`set`, `add`, `del`, `append`, `extend`, `replaceline`) are problematic because PowerShell strips double quotes from JSON strings, causing complex values to fail.

> **Recommendation for Windows:** Use CLI for all read/query operations. Use Python API for all write/modify operations.

### Chinese / UTF-8 Output on Windows

For read-only CLI commands that print Chinese text, set Python and PowerShell output encoding to UTF-8 before running jsonseek:

```powershell
$env:PYTHONIOENCODING = "utf-8"
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8
```

This helps with display output such as:

```powershell
python -m jsonseek.cli get file.json path
python -m jsonseek.cli query file.json keyword
```

It does **not** make shell-passed JSON strings safe for writes. This is still unsafe on Windows:

```powershell
python -m jsonseek.cli set file.json path '{"content":"中文"}'
```

For Chinese or complex JSON writes, use the Python API or `--from-file`, not PowerShell command arguments.

### Python API (Recommended for Writes on Windows)

Import directly in Python scripts to bypass shell quoting issues completely:

```python
import sys
sys.path.insert(0, 'src')

from jsonseek.commands.set_cmd import set_value
from jsonseek.commands.add_cmd import add_value
from jsonseek.commands.append_cmd import append_value
from jsonseek.commands.extend_cmd import extend_value
from jsonseek.commands.del_cmd import del_value
from jsonseek.commands.replaceline_cmd import replace_line

# Set/Add/Append/Extend complex values - no shell quoting issues
set_value('file.json', 'path', {"key": "value"})
add_value('file.json', 'path', ["item1", "item2"])
append_value('file.json', 'items', {"id": 1})
extend_value('file.json', 'items', [{"id": 2}, {"id": 3}])

# Delete
del_value('file.json', 'path')

# Replace line in file
replace_line('file.jsonl', 5, '{"id": 5, "name": "fixed"}')
```

CLI write commands print a patch preview on success and `Error: ...` on failure. Python API write helpers are quiet on success and raise an exception on failure.

### Fallback: Temp File Method

If you must use CLI for writes on Windows, use `--from-file` to avoid passing JSON strings on the command line:

```bash
# For set/add with complex values
echo '{"key": "value"}' > tmp.json
jsonseek set file.json path --from-file tmp.json

# For cutline/replaceline workflow
jsonseek cutline broken.jsonl 2 --save-temp
# C:\Users\...\tmpXXXX.jsonline
# Edit the temp file, then:
jsonseek replaceline broken.jsonl 2 --from-file C:\Users\...\tmpXXXX.jsonline
```

## References

- **Full command reference**: See [references/commands.md](references/commands.md)
- **Path syntax details**: See [references/path-syntax.md](references/path-syntax.md)
