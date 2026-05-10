# Path Syntax Reference

## Supported Formats

jsonseek supports multiple path notations. All of these resolve to the same target:

- `a.b.c`
- `a[b][c]`
- `a[b].c`
- `a.b[c]`

### Dot Notation

```
users[0].name
meta.settings.timeout
```

### Bracket Notation (String Keys)

```
a[key1][key2]
users[0][name]
```

Bracket content rules:
- All digits = array index (e.g. `[0]`, `[12]`)
- Anything else = object key (e.g. `[name]`, `[key-1]`)

### Array Indices

```
items[0]        # first element
items[0][1]     # nested array access
matrix[0][0]    # 2D array
```

### Mixed

```
a[key1].b[0].c
users[0][tags][0]
```

## JSONL Record Selectors

For JSONL files, paths start with a record selector:

```
[0].name              # record 0, field name
[12].payload.diff     # record 12, nested field
records[0].name       # alternative form
records[12].payload.diff
```

Record selector rules:
- `[N]` or `records[N]` picks the Nth record (0-based)
- Everything after the selector is the path inside that record
- Use empty inner path to refer to the whole record: `[0]` or `records[0]`

## Edge Cases

- Empty string refers to root
- `[*]` is only used in output (shape), not input
- Double dots `a..b` are invalid
- Empty brackets `a[]` are invalid
- Unclosed brackets `a[0` are invalid
