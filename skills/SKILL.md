# Daisy

Daisy is a CLI tool for storing and querying database schema information using a vector database (Zvec) with hybrid search (BM25 + semantic). Use it when you need to find which database table or column corresponds to a concept, variable, or keyword.

## When to Use

- User asks "which table has X column?", "where is Y stored?", or any schema/data discovery question.
- User needs to look up variable definitions, column meanings, or dataset locations.
- User wants to search across schema documentation semantically or by keyword.

## Detecting Installation

Before running any command, determine how daisy is available:

```bash
which daisy 2>/dev/null || where daisy 2>nul
```

- **If it returns a path** — daisy is installed globally (via `uv tool install`). Use `daisy` directly.
- **If it returns nothing** — run from the cloned repo with `uv run daisy`. Set `DAISY_CMD="uv run daisy"` (or `daisy` if available) and prefix all commands with it.

All examples below use `$DAISY_CMD` to cover both cases. Resolve it once, then reuse.

### Global Options

```bash
$DAISY_CMD --db ./mydb --model local <command> [options]
```

| Option | Default | Description |
|--------|---------|-------------|
| `--db` | `./daisy_db` | Database storage path |
| `--model` | `local` | Embedding model: `local`, `openai`, `qwen` |
| `--config` | None | YAML config file for defaults |

### Commands

**Add a schema file:**
```bash
# Individual metadata flags:
$DAISY_CMD add schema.txt --table MyTable --storage ./data.xlsx --type xlsx

# Or a single --schema JSON dict:
$DAISY_CMD add schema.txt --schema '{"table":"MyTable","storage":"./data.xlsx","type":"xlsx"}'
```

**Search (three modes):**
```bash
# Hybrid search (BM25 + semantic, RRF fusion):
$DAISY_CMD query queries.json

# BM25/keyword search:
$DAISY_CMD search queries.json

# Semantic vector search:
$DAISY_CMD vsearch queries.json
```

**Filter search results** with Zvec filter syntax (repeatable, joined with AND):
```bash
$DAISY_CMD query queries.json --filter "table = 'CSR_Finidx'" --filter "type = 'xlsx'"
$DAISY_CMD search queries.json -f "table = 'MyTable'"
```

**Database info:**
```bash
$DAISY_CMD info
```

### Query JSON Format

```json
[
  {"variable": "capex", "description": "capital expenditure"},
  {"variable": "stkcd"}
]
```

- `variable` (required): variable abbreviation to search
- `description` (optional): enriches semantic search
- `definition` (optional): enriches semantic search

### Output Format

Results are grouped by table to reduce token usage:
```json
[
  {
    "table": "CSR_Finidx",
    "query_variables": ["capex"],
    "columns": ["Outcap"],
    "definitions": ["Cash paid for acquisition..."],
    "doc_ids": ["CSR_Finidx_004"],
    "scores": [0.85],
    "storage": "./data.xlsx",
    "type": "xlsx"
  }
]
```

## Zvec Filter Syntax

Use `--filter` / `-f` on `query`, `search`, and `vsearch` commands. Each `--filter` flag accepts one filter expression; multiple flags are joined with `and`:

```bash
# Single filter
$DAISY_CMD query queries.json --filter "table = 'CSR_Finidx'"

# Multiple filters → joined as: table = 'CSR_Finidx' and type = 'xlsx'
$DAISY_CMD query queries.json --filter "table = 'CSR_Finidx'" --filter "type = 'xlsx'"
```

### Syntax Rules

The filter language is SQL-like. Zvec evaluates these expressions server-side before returning vector results.

**Comparison operators:**

| Operator | Example | Matches |
|----------|---------|---------|
| `=` | `table = 'CSR_Finidx'` | Exact string match |
| `!=` | `type != 'csv'` | Not equal |
| `>` / `>=` | `line_number >= 10` | Greater than (INT64 fields) |
| `<` / `<=` | `line_number < 50` | Less than (INT64 fields) |

**Logical operators:**

| Operator | Example |
|----------|---------|
| `and` | `table = 'CSR' and type = 'xlsx'` |
| `or` | `type = 'xlsx' or type = 'csv'` |

**String values must use single quotes** inside the filter expression. Numeric values (INT64 fields like `line_number`) are unquoted.

### Available Filterable Fields

| Field | Type | Index | Description |
|-------|------|-------|-------------|
| `table` | STRING | Invert | Table name (e.g., `'CSR_Finidx'`) |
| `column` | STRING | Invert | Variable abbreviation (e.g., `'Stkcd'`) |
| `description` | STRING | Invert | Variable name/description |
| `type` | STRING | Invert | File type (`'xlsx'`, `'csv'`, `'dta'`, `'parquet'`, etc.) |
| `raw_content` | STRING | Invert | Full original line content (supports keyword matching) |

`definition` and `storage` are stored but NOT indexed, so they cannot be used in filters.

### Practical Examples

```bash
# Search only within a specific table
$DAISY_CMD query queries.json -f "table = 'CSR_Finidx'"

# Search by file type
$DAISY_CMD search queries.json -f "type = 'xlsx'"

# Combine table + type
$DAISY_CMD vsearch queries.json --filter "table = 'CSR_Finidx'" --filter "type = 'xlsx'"

# Search for a specific column
$DAISY_CMD query queries.json -f "column = 'Stkcd'"

# Exclude a type (not available in this dataset)
$DAISY_CMD query queries.json -f "type != 'db'"
```

## Schema File Format

Pattern: `Abbrev [Name] - Definition`

```
Stkcd [Stock Code] - Based on the stock code published by the exchange.
Accper [Reporting Period End Date] - Expressed in YYYY-MM-DD format.
```

## Quick Workflow

```bash
# Detect installation
DAISY_CMD=$(which daisy 2>/dev/null || echo "uv run daisy")

# 1. Add schema
$DAISY_CMD add example/CSR_Finidx[DES][xlsx].txt \
  --schema '{"table":"CSR_Finidx","storage":"./CSR_Finidx.xlsx","type":"xlsx"}'

# 2. Query
echo '[{"variable":"capex","description":"capital expenditure"}]' > /tmp/q.json
$DAISY_CMD query /tmp/q.json --filter "table = 'CSR_Finidx'"

# 3. Check stats
$DAISY_CMD info
```

## Key Files for Modifications

- **CLI commands/options:** `src/daisy/cli.py`
- **Search logic + filter:** `src/daisy/search.py`
- **Database schema:** `src/daisy/database.py`
- **Parser:** `src/daisy/parser.py`
- **Embedding models:** `src/daisy/embeddings.py`
