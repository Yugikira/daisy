# Daisy CLI Design Spec

A RAG system CLI tool for storing and querying database schema with hybrid search (BM25 + semantic).

## Overview

Daisy is a CLI tool designed primarily for AI agents to query database schema information. It supports:
- Adding schema files to a vector database
- BM25/exact search on raw content
- Semantic vector search
- Hybrid search with RRF fusion
- Auto-merging results grouped by table

## CLI Structure

### Base Command

```
daisy --db <path> --model <model_name> <command> [options]
```

### Global Options

| Option | Default | Description |
|--------|---------|-------------|
| `--db` | Required | Database storage path |
| `--model` | all-MiniLM-L6-v2 | Embedding model (local, openai, qwen, or specific model name) |

### Commands

| Command | Description | Example |
|---------|-------------|---------|
| `add` | Add schema file to database | `daisy --db ./mydb add file.txt --table CSR_Finidx --storage ./data.xlsx --type xlsx` |
| `search` | BM25/exact search | `daisy --db ./mydb search queries.json` |
| `vsearch` | Semantic vector search | `daisy --db ./mydb vsearch queries.json` |
| `query` | Hybrid search (BM25 + semantic) | `daisy --db ./mydb query queries.json` |
| `info` | Show database stats | `daisy --db ./mydb info` |

### Add Command Options

| Option | Required | Description |
|--------|----------|-------------|
| `<file>` | Yes | Schema file path (txt format) |
| `--table` | Yes | Table name for metadata |
| `--storage` | Yes | Dataset storage path |
| `--type` | Yes | Dataset type (xlsx, csv, dta, parquet, etc.) |

### Query Commands Options

| Option | Default | Description |
|--------|---------|-------------|
| `--topk` | 10 | Number of results per query variable |
| `--output` | stdout | Output file path (optional) |

## Input/Output Formats

### Query Input JSON

```json
[
  {"variable": "capex", "description": "capital expenditure"},
  {"variable": "stkcd"}
]
```

Each query object:
- `variable`: Variable abbrev/code to search (required)
- `description`: Variable name/description (optional, enriches semantic search)
- `definition`: Variable definition (optional, enriches semantic search)

### Query Output JSON (Merged by Table)

```json
[
  {
    "table": "CSR_Finidx",
    "query_variables": ["capex", "stkcd"],
    "columns": ["Outcap", "Stkcd"],
    "definitions": ["Cash paid for acquisition...", "Based on stock code..."],
    "doc_ids": ["CSR_Finidx_004", "CSR_Finidx_001"],
    "scores": [0.85, 0.92],
    "storage": "./data.xlsx",
    "type": "xlsx"
  }
]
```

Output grouped by table to reduce token usage for AI agents.

## Database Schema

### Zvec Collection Fields

| Field | Type | Index | Description |
|-------|------|-------|-------------|
| `id` | STRING | Invert | Auto-generated: `<table>_XXX` |
| `table` | STRING | Invert | Table name |
| `column` | STRING | Invert | Variable abbrev (parsed) |
| `description` | STRING | Invert | Variable name (parsed) |
| `definition` | STRING | None | Variable definition text |
| `storage` | STRING | None | Dataset storage path |
| `type` | STRING | Invert | Dataset type |
| `raw_content` | STRING | Invert | Full line content (used for BM25) |
| `line_number` | INT64 | None | Source file line number |

### Vectors

| Vector | Type | Content | Embedding Source |
|--------|------|---------|------------------|
| `dense_embedding` | VECTOR_FP32 | raw_content | Configurable model (default: all-MiniLM-L6-v2, dim=384) |
| `sparse_embedding` | SPARSE_VECTOR_FP32 | raw_content | BM25EmbeddingFunction |

HNSW index params: `ef_construction=200, m=16`

## Schema Parsing

### Default Format (Bracket)

Pattern: `Abbrev [Name] - Definition`

Example: `Stkcd [Stock Code] - Based on the stock code published by the exchange.`

Parsing extracts:
- `column`: `Stkcd`
- `description`: `Stock Code`
- `definition`: `Based on the stock code published by the exchange.`
- `raw_content`: Full original line

### Fallback (Raw Storage)

If bracket format regex fails, store entire line as:
- `column`: empty
- `description`: empty
- `definition`: empty
- `raw_content`: full line

Document ID always generated: `<table>_XXX` (sequential numbering)

## Module Architecture

```
daisy/
├── __init__.py
├── cli.py           # Typer CLI entry point, command routing
├── database.py      # Zvec collection management
├── parser.py        # Schema file parsing
├── search.py        # Search operations and result merging
├── embeddings.py    # Embedding model management
└── config.py        # Configuration handling
```

### Module Responsibilities

**cli.py**
- Command routing via Typer
- Argument parsing and validation
- Output formatting (JSON serialization)
- Entry point for `daisy` command

**database.py**
- `create_collection(path, schema)`: Initialize Zvec collection
- `open_collection(path)`: Open existing collection
- `insert_docs(collection, docs)`: Batch insert with embeddings
- `get_stats(collection)`: Return collection statistics

**parser.py**
- `parse_schema_file(path)`: Read and parse entire file
- `parse_line(line)`: Single line parsing with bracket regex
- `BRACKET_PATTERN`: Regex `r"^(\w+)\s*\[(.+?)\]\s*-\s*(.+)$"`

**search.py**
- `bm25_search(collection, queries, topk)`: Sparse vector search
- `semantic_search(collection, queries, topk)`: Dense vector search
- `hybrid_search(collection, queries, topk)`: RRF fusion of both
- `merge_results(results)`: Group results by table, merge fields into lists

**embeddings.py**
- `get_embedding_model(name)`: Load model by name (see model registry below)
- `get_dense_embedding(text, model)`: Generate dense vector
- `get_sparse_embedding(text)`: Generate BM25 sparse vector
- Model registry:
  - `local` or `all-MiniLM-L6-v2`: sentence-transformers, dim=384
  - `openai`: OpenAI text-embedding-3-small (requires API key via OPENAI_API_KEY env)
  - `qwen`: Qwen embedding (requires API key via QWEN_API_KEY env)

**config.py**
- `DEFAULT_MODEL`: "all-MiniLM-L6-v2"
- `load_config(path)`: Load optional config file
- `get_model_config()`: Return current model settings

## Data Flow

### Add Operation

```
file.txt → parser.parse_schema_file()
         → list[{fields, raw_content}]
         → embeddings.embed_all()
         → list[Doc{fields, vectors}]
         → database.insert_docs()
```

### Query Operation

```
queries.json → load_queries()
             → embeddings.embed_queries()
             → search.hybrid_search()
             → raw_results
             → search.merge_results()
             → grouped JSON output
```

## Error Handling

| Scenario | Behavior |
|----------|----------|
| DB path missing on add | Auto-create collection |
| DB path missing on search/query | Error: "Database not found at <path>" |
| Schema file unreadable | Error: "Cannot read file <path>" |
| Line parse fails | Fallback to raw storage, continue |
| Query JSON invalid | Error: "Invalid query format. Expected: [...]" |
| Embedding model unavailable | Warn, fall back to default model |
| No search results | Return empty array `[]` |
| Multiple tables in results | Each table → separate merged group |

## Dependencies

| Package | Purpose |
|---------|---------|
| `zvec` | Vector database with hybrid search |
| `typer` | CLI framework |
| `sentence-transformers` | Local embedding models |
| `pydantic` | Data validation and serialization |

## Testing Strategy

- Unit tests for parser (bracket regex, fallback)
- Unit tests for search merge logic
- Integration tests for add → query flow
- Test fixtures: sample schema files, query JSON files

## Success Criteria

1. `daisy --db ./test add example.txt --table Test --storage ./data --type csv` succeeds
2. `daisy --db ./test query queries.json` returns valid merged JSON
3. Query for "capex" returns "Outcap" column from CSR_Finidx table
4. Hybrid search combines BM25 + semantic with RRF fusion
5. Results grouped by table reduce output tokens by ~50% vs per-query format