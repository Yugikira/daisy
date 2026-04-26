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
daisy --db <database_path> --model <model_name> --config <config.yaml> <command>
```

| Option | Default | Description |
|--------|---------|-------------|
| `--db` | `./daisy_db` | Database storage path |
| `--model` | `all-MiniLM-L6-v2` | Embedding model (local, openai, qwen) |
| `--config` | None | YAML config file path |

### Config File

Create a YAML config file to set defaults:

```yaml
# daisy.yaml
db: ./my_database
model: local
```

Use it with the `--config` flag:

```bash
daisy --config daisy.yaml add schema.txt --table MyTable ...
```

CLI flags override config file values. Config file values override hardcoded defaults.

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

## Model Configuration

### Environment Variables for API Models

To use API-based embedding models, set the corresponding environment variables:

```bash
# For OpenAI embeddings
export OPENAI_API_KEY="sk-your-openai-api-key"

# For Qwen/Dashscope embeddings (Alibaba Cloud)
export QWEN_API_KEY="your-dashscope-api-key"
```

If the API key is not set, Daisy will automatically fall back to the local model (`all-MiniLM-L6-v2`) with a warning.

### Model Selection

Use the `--model` global option to select an embedding model:

```bash
# Use default local model (all-MiniLM-L6-v2)
daisy --db ./mydb add schema.txt --table MyTable ...

# Use OpenAI embeddings
daisy --model openai --db ./mydb add schema.txt --table MyTable ...

# Use Qwen embeddings
daisy --model qwen --db ./mydb add schema.txt --table MyTable ...

# Use alias for local model
daisy --model local --db ./mydb add schema.txt --table MyTable ...
```

**Important:** The embedding model is set when adding documents. When querying, use the same model for consistent results:

```bash
# Add with OpenAI model
daisy --model openai --db ./mydb add schema.txt --table MyTable ...

# Query with the same model
daisy --model openai --db ./mydb query queries.json
```

### Supported Models

| Model Alias | Type | Dimension | Environment Variable | Notes |
|-------------|------|-----------|---------------------|-------|
| `all-MiniLM-L6-v2` | local (sentence-transformers) | 384 | None | Default, runs locally, fastest |
| `local` | local (sentence-transformers) | 384 | None | Alias for all-MiniLM-L6-v2 |
| `openai` | API (text-embedding-3-small) | 1536 | `OPENAI_API_KEY` | High quality, requires internet |
| `qwen` | API (Dashscope) | 1024 | `QWEN_API_KEY` | Good Chinese/English support |

### Customizing Model Registry

The model registry is defined in `src/daisy/config.py`. To add a new model, edit the `MODEL_REGISTRY` dict:

```python
MODEL_REGISTRY = {
    # Add your custom model
    "custom-model": {
        "type": "local",  # or "api"
        "dimension": 768,
        "class": "sentence_transformers",  # or "openai", "qwen"
        "model": "your-model-name",  # HuggingFace model name for local
    },
}
```

For API models, you'll also need to implement the embedding logic in `src/daisy/embeddings.py`.

### Model Cache Location

Local embedding models are downloaded and cached by Hugging Face to:

```
# Windows
%USERPROFILE%\.cache\huggingface\hub

# Linux/macOS
~/.cache/huggingface/hub
```

You can customize this with the `HF_HOME` or `TRANSFORMERS_CACHE` environment variables. Models are cached permanently and only downloaded once.

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