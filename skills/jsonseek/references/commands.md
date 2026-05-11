# jsonseek Command Reference

## Global Options

All commands accept:

- `file` — target JSON or JSONL file
- `--kind {json,jsonl}` — force file kind (auto-detect by default)
- `--output {pretty,json}` — output format
- `--backup` — create `.bak` before writing

---

## shape — Show Structure

Display the shape/type tree of a JSON/JSONL file.

```bash
jsonseek shape data.json
jsonseek shape data.json --max-depth 2
jsonseek shape data.json --array-mode full
jsonseek shape data.jsonl --sample-size 50
```

**Options:**
- `--max-depth N` — limit traversal depth
- `--array-mode {sample,full}` — sample first element vs. list all
- `--sample-size N` — records to sample for JSONL

---

## fields — List Fields

List all fields with their types and occurrence stats.

```bash
jsonseek fields data.json
jsonseek fields data.json keyword     # filter by keyword
jsonseek fields data.json --top       # only top-level fields
jsonseek fields data.jsonl
```

---

## ls — List Children

List children at a given path.

```bash
jsonseek ls data.json                 # root children
jsonseek ls data.json users[0]
jsonseek ls data.jsonl '[0]'
```

---

## get — Get Value

Retrieve a value at a path.

```bash
jsonseek get data.json name
jsonseek get data.json items[0].title
jsonseek get data.json a[b][c]
jsonseek get data.jsonl '[0].name'
jsonseek get data.jsonl 'records[0].age'
```

---

## query — Search

Search for keys and/or values matching a term.

```bash
jsonseek query data.json keyword
jsonseek query data.json keyword --exact
jsonseek query data.json keyword --case-sensitive
jsonseek query data.json keyword --match-mode key
jsonseek query data.jsonl keyword --max-results 10
jsonseek query data.jsonl keyword --record-id-field id
```

**Options:**
- `--exact` — exact match only
- `--case-sensitive` — case-sensitive matching
- `--match-mode {key,value,both}` — what to match
- `--max-results N` — limit results
- `--record-id-field FIELD` — attach record ID to results
- `--preview-field FIELD` — attach preview to results

---

## set — Set Value

Set a value at a path. For JSONL, rewrites the file.

```bash
jsonseek set data.json meta.count 99
jsonseek set data.json meta.new "val" --create-missing
jsonseek set data.jsonl '[0].name' "Alice"
jsonseek set data.jsonl '[0].tags[0]' "admin"
```

---

## add — Add Key

Add a new key to an object.

```bash
jsonseek add data.json meta.owner "team-a"
jsonseek add data.jsonl '[0].tags' "new-tag" --create-missing
```

**Note:** Cannot add to array by index. Use `set` or `append` instead.

---

## del — Delete

Delete a key, array element, or entire JSONL record.

```bash
jsonseek del data.json meta.old_key
jsonseek del data.json items[2]
jsonseek del data.jsonl '[0].name'
jsonseek del data.jsonl '[2]'          # delete whole record
```

---

## append — Append to Array

Append a single value to an array (JSON) or append a record (JSONL).

```bash
jsonseek append data.json items '{"id":3}'
jsonseek append data.jsonl '{"name":"new"}'
```

**Note:** JSON append requires `path value`. JSONL append only needs `value`.

---

## extend — Extend Array

Extend an array by appending all elements from a JSON array value (JSON only, not supported for JSONL).

```bash
jsonseek extend data.json items '[1, 2, 3]'
jsonseek extend data.json tags '["urgent", "review"]'
```

**Note:** `extend` is for JSON only. Use `append` for JSONL records.

---

## concat — Concatenate JSON to JSONL

Merge multiple JSON files into a single JSONL file.

```bash
jsonseek concat "*.json" -o output.jsonl
jsonseek concat "data/**/*.json" -o combined.jsonl
jsonseek concat "experiments/*/result.json" --no-sort -o results.jsonl
```

**Arguments:**
- `pattern` — glob pattern to match JSON files

**Options:**
- `-o, --output-file FILE` — write to file instead of stdout
- `--no-sort` — preserve glob order instead of sorting by filename
- `--encoding` — file encoding (auto-detect by default)

**Output:**
Each matched JSON file is serialized to one line in JSONL format, sorted by filename by default.

---

## extract — Batch Extract

Extract the same path from multiple JSON files matching a glob pattern.

```bash
jsonseek extract "*.json" user.name
jsonseek extract "data/*.json" metrics.cpu --output json
jsonseek extract "data/**/*.json" api.endpoint --include-missing
```

**Arguments:**
- `pattern` — glob pattern to match files (e.g. `*.json`, `data/**/*.json`)
- `path` — path to extract from each file

**Options:**
- `--output {pretty,json}` — output format
- `--kind {json,jsonl}` — force file kind
- `--include-missing` — include files where the path does not exist (default: show them)

**Notes:**
- `extract` is for batch operations on JSON files only; JSONL files will appear as `[skipped]` in the output.
- All matched files appear in the output, including those with missing paths or unsupported formats.

**Output (pretty):**
```
a.json   alice
b.json   bob
c.json   [missing] Path not found
d.jsonl  [skipped] Skipped: extract only supports JSON files
```

**Output (json):**
```json
[
  {"file": "a.json", "value": "alice", "ok": true},
  {"file": "b.json", "value": "bob", "ok": true},
  {"file": "c.json", "value": null, "ok": false, "error": "Path not found"},
  {"file": "d.jsonl", "value": null, "ok": false, "error": "Skipped: extract does not support JSONL files"}
]
```
