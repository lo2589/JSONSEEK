---
name: jsonseek
description: Query, inspect, and patch JSON/JSONL files from the command line. Use this skill whenever Kimi needs to read, search, modify, or analyze structured JSON/JSONL data on disk. Triggers include: (1) exploring unknown JSON file structure, (2) finding specific keys or values in JSON/JSONL, (3) editing JSON files (add/remove/update fields), (4) analyzing JSON schema or field coverage, (5) processing JSONL record streams.
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

## Core Workflows

### 1. Explore an unknown JSON file

```bash
jsonseek shape file.json          # structure tree
jsonseek fields file.json         # field list with types
jsonseek ls file.json             # list root children
jsonseek ls file.json path        # list children at path
```

### 2. Search for data

```bash
jsonseek query file.json keyword         # key + value match
jsonseek query file.json keyword --exact # exact match only
jsonseek query file.json keyword --match-mode key
jsonseek query file.jsonl keyword --record-id-field id
```

### 3. Read values

```bash
jsonseek get file.json name
jsonseek get file.json items[0].title
jsonseek get file.json a[b][c]         # bracket key syntax
jsonseek get file.jsonl '[0].name'     # JSONL record selector
```

### 4. Edit JSON files

```bash
jsonseek set file.json path value              # update existing
jsonseek set file.json path value --create-missing
jsonseek add file.json path value              # add new key (object only)
jsonseek del file.json path                    # delete key or array index
jsonseek append file.json array_path value     # append to array
```

### 5. Edit JSONL files

```bash
jsonseek set file.jsonl '[0].name' "Alice"     # modify record field
jsonseek del file.jsonl '[0].name'             # delete record field
jsonseek del file.jsonl '[2]'                  # delete whole record
jsonseek append file.jsonl '{"name":"new"}'    # append record
```

## Path Syntax Summary

| Style | Example | Meaning |
|---|---|---|
| Dot notation | `a.b.c` | `a -> b -> c` |
| Bracket keys | `a[key1][key2]` | `a -> key1 -> key2` |
| Mixed | `a[key1].b[0]` | `a -> key1 -> b -> index 0` |
| Array index | `items[0][1]` | `items -> 0 -> 1` |

### Batch extract

Use `extract PATTERN PATH` to pull the same path from many files:

```bash
jsonseek extract "experiments/*/metrics.json" training.loss
jsonseek extract "configs/*.json" api.endpoint --output json
```

JSONL paths start with a record selector: `[N].field` or `records[N].field`.

## Important Notes

- Use `--output json` when piping output to another tool.
- Use `--backup` before write operations to create `.bak`.
- `append` for JSON requires `path value` (array path + value).
- `append` for JSONL only needs `value` (root-level record append).
- On Windows PowerShell, JSON string values may need extra quote escaping.

## References

- **Full command reference**: See [references/commands.md](references/commands.md)
- **Path syntax details**: See [references/path-syntax.md](references/path-syntax.md)
