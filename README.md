# Daisy

A CLI tool for storing and querying database schema with hybrid search (BM25 + semantic). Designed primarily for AI agents to query schema information efficiently.

## Features

- **Add schema files** to a vector database with automatic parsing
- **Hybrid search** combining SPLADE sparse embeddings + dense semantic vectors with RRF fusion
- **BM25 search** for keyword-based exact matching
- **Semantic search** for meaning-based similarity
- **Auto-merge results** grouped by table to reduce token usage for AI agents

## Installation

```bash
# Clone the repository
git clone git@github.com:Yugikira/daisy.git
cd daisy

# Install dependencies with uv
uv sync

# Or install in editable mode
uv pip install -e .
```

## Usage

### Global Options

```bash
daisy --db <database_path> --model <model_name> <command>
```

| Option | Default | Description |
|--------|---------|-------------|
| `--db` | `./daisy_db` | Database storage path |
| `--model` | `all-MiniLM-L6-v2` | Embedding model (local, openai, qwen) |

### Commands

#### Add Schema File

Add a schema txt file to the database:

```bash
daisy --db ./mydb add schema.txt --table MyTable --storage ./data.xlsx --type xlsx
```

| Option | Required | Description |
|--------|----------|-------------|
| `--table` | Yes | Table name for metadata |
| `--storage` | Yes | Dataset storage path |
| `--type` | Yes | Dataset type (xlsx, csv, dta, parquet, etc.) |

#### Query (Hybrid Search)

Query with hybrid search (sparse + dense with RRF fusion):

```bash
daisy --db ./mydb query queries.json
```

#### Search (BM25/Sparse)

Keyword-based search using SPLADE sparse embeddings:

```bash
daisy --db ./mydb search queries.json
```

#### Semantic Search

Dense vector semantic search:

```bash
daisy --db ./mydb vsearch queries.json
```

#### Database Info

Show database statistics:

```bash
daisy --db ./mydb info
```

## Input Format

### Schema File Format

Default bracket format (auto-parsed):

```text
Stkcd [Stock Code] - Based on the stock code published by the exchange.
Accper [Reporting Period End Date] - Expressed in YYYY-MM-DD format.
Outcap [Capital Expenditure] - Cash paid for the acquisition and construction of fixed assets.
```

Pattern: `Abbrev [Name] - Definition`

Lines that don't match this format are stored as raw content.

### Query JSON Format

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

## Output Format

Results are grouped by table to reduce token usage for AI agents:

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

## Supported Embedding Models

| Model | Type | Dimension | Notes |
|-------|------|-----------|-------|
| `local` / `all-MiniLM-L6-v2` | sentence-transformers | 384 | Default, runs locally |
| `openai` | OpenAI API | 1536 | Requires `OPENAI_API_KEY` env var |
| `qwen` | Dashscope API | 1024 | Requires `QWEN_API_KEY` env var |

## Example Workflow

```bash
# Add schema file
daisy --db ./schema_db add example/CSR_Finidx[DES][xlsx].txt \
  --table CSR_Finidx --storage ./CSR_Finidx.xlsx --type xlsx

# Query for variables
daisy --db ./schema_db query queries.json

# Check database info
daisy --db ./schema_db info
```

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Format code
uv run ruff format .

# Lint code
uv run ruff check .
```

## License

MIT