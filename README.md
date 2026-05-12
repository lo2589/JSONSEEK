# JSONSEEK

> **A JSON/JSONL navigation and partial manipulation tool for developers and coding agents.**
>
> Core purpose: Reduce token waste from LLMs reading entire large JSON files. Use `shape`/`fields`/`query` to locate, then `get`/`set`/`add`/`del`/`append` for partial operations.
>
> Supports structural understanding, field summaries, partial querying, and partial modification for both JSON and JSONL.
>
> Supports bug detection and partial fixes for both JSON and JSONL.
---

## Why JSON Deserves a Dedicated Tool

JSON is the de facto standard for modern data exchange. From ML experiment logs, API configs, application log streams, to microservice registries and crawler data stores, JSON/JSONL is everywhere:

- **ML Experiment Tracking**: Training parameters, metric curves, and model configs all live in JSON — a single experiment directory can easily reach tens of MB
- **API/Microservice Configs**: Service discovery, routing rules, and environment variables are often managed as JSON configs
- **Logs & Event Streams**: Structured logs (JSONL) are easier to query than plain text, but file sizes grow extremely fast
- **Data Exchange**: Frontend-backend communication, inter-service RPC, and crawler output — JSON is the most common format

The problem: **The larger the JSON file, the more expensive it is for LLMs and developers to process**. `cat`-ing a 10MB JSON into context burns millions of tokens; even human developers suffer when searching for a field in thousands of lines of nested structure.

**JSONSEEK solves this** — by replacing full reads with partial operations, and manual scanning with structured queries. For coding agents and developers who frequently handle JSON/JSONL, this tool is worth a look.

---

## Why Use JSONSEEK (For Coding Agents)

When facing a 10MB JSON file, `cat`-ing the entire file into context is catastrophic token waste. JSONSEEK lets you:

1. **Understand structure first** — `shape` for the skeleton, `fields` for the field list, without reading content
2. **Locate targets next** — `query` to search keywords, `ls` to see child nodes at a layer, `get` to fetch specific values
3. **Modify partially last** — `set`/`add`/`del`/`append` only where needed

### Token Savings Estimate

| File Size | Operation | Full Read | JSONSEEK Output | Savings |
|---|---|---|---|---|
| 100KB config JSON | `shape` | ~25K tokens | ~100 tokens | **99%+** |
| 100KB config JSON | `fields` | ~25K tokens | ~300 tokens | **98%+** |
| 100KB config JSON | `get` single value | ~25K tokens | ~10 tokens | **99%+** |
| 100KB config JSON | `query` hits a few | ~25K tokens | ~100 tokens | **99%+** |
| 10MB log JSONL | `shape` sampling | ~2.5M tokens | ~200 tokens | **99.9%+** |
| 10MB log JSONL | `query` hits dozens | ~2.5M tokens | ~1K tokens | **99.9%+** |

> Rough estimate: 1 token ≈ 4 bytes of English text. Actual ratios vary by content and tokenizer, but the order of magnitude holds — **the larger the file, the more dramatic the savings**.

**Typical agent workflow:**

```bash
# Step 1: Understand structure (zero content read, metadata only)
jsonseek shape config.json          # See depth, array sizes
jsonseek fields config.json         # See all field names and types

# Step 2: Locate target (read only matching parts)
jsonseek query config.json api_key  # Find where api_key is
jsonseek get config.json services[0].endpoint

# Step 3: Partial modification (write only target path)
jsonseek set config.json services[0].endpoint "https://new.api.com"
jsonseek del config.json services[0].deprecated_field
```

---

## Installation

```bash
pip install -e .
jsonseek --version    # JSONSEEK 0.1.0
```

Requires Python >= 3.8. Cross-platform support for Windows / macOS / Linux.

---

## Command Cheatsheet (Agent Mode)

### Read-Only Commands (Safe, will not modify files)

| Command | Purpose | Agent Scenario |
|---|---|---|
| `shape FILE` | Display JSON skeleton tree | First look at an unknown JSON, quickly grasp structure |
| `fields FILE [KEYWORD]` | List all fields and types | Find field names, see type distribution, filter by keyword |
| `ls FILE [PATH]` | List child nodes at a path | Browse JSON like `ls` on directories |
| `get FILE PATH` | Get value at a path | Precisely read a single value, avoid full load |
| `query FILE TERM` | Search keys or values | Find where a config item is |
| `extract PATTERN PATH` | Batch extract values at same path | Grab the same field from multiple config files |
| `concat PATTERN` | Merge multiple JSONs into JSONL | Batch format conversion, data aggregation |

### Write Commands (Will modify files, `--backup` recommended)

| Command | Purpose | Agent Scenario |
|---|---|---|
| `set FILE PATH VALUE` | Set value | Modify config items, update URLs, change numbers |
| `add FILE PATH VALUE` | Add new key to object | Add new config fields |
| `del FILE PATH` | Delete key or array element | Clean up deprecated fields |
| `append FILE PATH VALUE` | Append single element to array (JSON) | Add a new item to a list |
| `extend FILE PATH VALUE` | Batch append to array (JSON) | Add multiple elements to a list at once |
| `append FILE VALUE` | Append record (JSONL) | Add a record to end of JSONL |

### Global Options

- `--output json` — Machine-readable output (for downstream tools / LLM parsing)
- `--backup` — Create `.bak` before modification
- `--kind {json,jsonl}` — Force file type

### Windows PowerShell Quoting Pitfalls and Solutions

PowerShell eats double quotes inside JSON strings, causing complex values to fail. Two solutions:

#### Solution 1: Temp File Method (Recommended)

```powershell
# Use --from-file instead of passing value on command line
echo '{"key": "value"}' > tmp.json
jsonseek set data.json path --from-file tmp.json

# cutline/replaceline combo for fixing broken lines
jsonseek cutline broken.jsonl 5 --save-temp
# After modifying the temp file
jsonseek replaceline broken.jsonl 5 --from-file C:\Users\...\tmpXXXX.jsonline
```

#### Solution 2: Python API (Completely bypass CLI)

```python
import sys
sys.path.insert(0, 'src')
from jsonseek.commands.set_cmd import set_value
from jsonseek.commands.add_cmd import add_value
from jsonseek.commands.replaceline_cmd import replace_line

# Pass Python objects directly, no escaping needed
set_value('data.json', 'path', {"key": "value"})
add_value('data.json', 'items', ["item1", "item2"])
replace_line('data.jsonl', 5, '{"id": 5, "fixed": true}')
```

No quoting issues on macOS/Linux bash or Windows CMD.

---

## Path Syntax

```bash
# Dot-separated
jsonseek get data.json meta.settings.timeout

# Bracket keys (supports string keys)
jsonseek get data.json meta[settings][timeout]
jsonseek get data.json users[0][name]

# Array indices
jsonseek get data.json items[0][1]

# JSONL record selector
jsonseek get data.jsonl '[0].name'
jsonseek get data.jsonl 'records[12].payload.diff'
jsonseek set data.jsonl '[0].age' 30
```

Rules:
- `[number]` → Array index (`[0]`, `[12]`)
- `[string]` → Object key (`[name]`, `[key-1]`)
- Consecutive brackets chain directly: `a[b][c]`

---

## JSON vs JSONL Quick Reference

| | JSON | JSONL |
|---|---|---|
| Reading | Load entire file into memory | Stream line by line |
| `shape` | Full tree | Sample first N records |
| `fields` | Count occurrences | Coverage (record coverage rate) |
| `get`/`ls` | Parse `path` directly | Path must start with `[N].` or `records[N].` |
| `set`/`add`/`del` | Direct patch in-memory tree | Full file rewrite (atomic replacement) |
| `append` | Append inside array | Append record at root level |

---

## Agent Practical Examples

### Scenario 1: Explore Unknown Config JSON

```bash
jsonseek shape config.json
# (root)
#   services
#     services[*]  (object) [5]
#       services[*].name
#       services[*].endpoint
#       services[*].timeout
#   database
#     database.host
#     database.port

jsonseek fields config.json
# services  types=array  paths=1
# name      types=string paths=5
# endpoint  types=string paths=5
# timeout   types=integer paths=5
# database  types=object paths=1
# host      types=string paths=1
# port      types=integer paths=1

jsonseek query config.json production
# services[2].name  [value] 'production'

jsonseek get config.json services[2].endpoint
# https://prod.api.example.com
```

### Scenario 2: Batch Modify JSONL

```bash
jsonseek shape logs.jsonl
# (root)
#   timestamp  (string)
#   level      (string)
#   message    (string)

jsonseek query logs.jsonl ERROR --max-results 5
# message  [value] 'connection failed' record=12 line=15

# Change level of record 12 to warning
jsonseek set logs.jsonl '[12].level' "warning"

# Delete record 100
jsonseek del logs.jsonl '[100]'

# Append new record
jsonseek append logs.jsonl '{"timestamp":"2024-01-01","level":"info","message":"started"}'
```

### Scenario 3: Precise Partial Modification (Avoid Full Read)

```bash
# Don't do this: cat 10MB.json | feed to LLM for analysis
# Do this instead:
jsonseek get large.json data[0].metrics.cpu_usage
# 42.5

jsonseek set large.json data[0].metrics.cpu_usage 45.0
```

### Scenario 4: Batch Extract and Array Extension

```bash
# Batch extract same field from multiple experiment records
jsonseek extract "experiments/*/metrics.json" training.loss --output json
# [{"file":"exp1/metrics.json","value":0.12,"ok":true}, ...]

# Append multiple elements to array at once (extend unpacks array and appends one by one)
jsonseek extend data.json tags '["urgent", "review"]'
# Equivalent to sequentially appending "urgent" and "review"
```

### Scenario 5: Merge Multiple JSONs into JSONL

```bash
# Convert all JSON experiment records in directory to single JSONL
jsonseek concat "experiments/*/result.json" -o combined.jsonl
# combined.jsonl:
# {"experiment":"exp1","accuracy":0.95}
# {"experiment":"exp2","accuracy":0.92}

# Default sorted by filename; add --no-sort to preserve original order
jsonseek concat "logs/*.json" --no-sort -o logs.jsonl
```

### Scenario 6: Large File Debug and Error Fix

When JSON files are corrupted or have syntax errors, JSONSEEK can precisely locate problematic lines, and together with the temp file method enables safe fixes:

```bash
# Step 1: Discover errors (auto-locate to line)
jsonseek shape broken.jsonl
# Error: Found 2 invalid lines in broken.jsonl:
#   Line 5: {"id": 5, "broken
#     Error: Unterminated string starting at
#   Line 12: {"id": 12, "another}
#     Error: Unterminated string starting at

# Step 2: Extract problematic line to temp file
jsonseek cutline broken.jsonl 5 --save-temp
# C:\Users\...\tmpXXXX.jsonline

# Step 3: Fix temp file with Python (bypass PowerShell quoting issues)
python -c "open(r'C:\Users\...\tmpXXXX.jsonline','w',encoding='utf-8').write('{\"id\": 5, \"name\": \"fixed\"}')"

# Step 4: Replace back into original file
jsonseek replaceline broken.jsonl 5 --from-file C:\Users\...\tmpXXXX.jsonline

# Step 5: Verify fix
jsonseek shape broken.jsonl
# (root)
#   id  (integer)
#   name  (string)
```

**Debug Scenario Token Savings Comparison:**

| Scenario | Traditional (Full Read) | JSONSEEK Way | Savings |
|-----|---------------------|---------------|------|
| Locate syntax error in 10MB JSONL | Read full ~2.5M tokens | shape output ~200 tokens | **99.99%** |
| Fix line 5 of corrupted JSONL | Read context + modify ~500K tokens | cutline + replaceline ~1K tokens | **99.8%** |
| Batch fix N errors | N × context reads | N × (cutline + replaceline) | **~99%** |

---

## Project Structure

```
src/jsonseek/
  cli.py            # CLI entry point
  types.py          # Core data types
  errors.py         # Exceptions
  detect.py         # File type detection
  formatters.py     # Output formatting (pretty/json)
  path_parser.py    # Path parsing (supports . / [] mixed)
  value_utils.py    # Type inference and input coercion
  io/               # File I/O (json, jsonl, rewrite)
  walkers/          # Tree traversal (shape, fields, query)
  patch/            # Patch operations (locator, object/array ops)
  commands/         # Command handlers
tests/              # Unit tests (53 cases)
```

---

## Roadmap

- [x] JSON read/write and patch
- [x] JSONL streaming scan and rewrite
- [x] `--output json` machine-readable output
- [x] Windows / macOS / Linux cross-platform support
- [x] Large file error location and fix (cutline/replaceline)
- [x] Python API methods (set_value/add_value/del_value)
- [x] PowerShell temp file bypass solution
- [ ] `--dry-run` preview modifications
- [ ] Claude Code / Cursor / OpenAI-compatible coding workflows plugin integration

---

## License

MIT
