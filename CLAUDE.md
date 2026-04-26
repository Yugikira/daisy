## Project Setup
- **Python Version:** 3.11+
- **Package Manager:** `uv`
- **Virtual Environment:** Use `.venv`

## Coding Standards
- Use type hints for all function signatures.
- Format code using `ruff`.
- Use `snake_case` for functions and variables.
- Follow PEP 8 guidelines.

## Testing
- Use `pytest`.
- All new features must have corresponding tests in the `tests/` directory.

## Common Commands
- Run Tests: `uv run pytest`
- Format Code: `uv run ruff format .`
- Lint Code: `uv run ruff check .`

## Guidelines
- When adding dependencies, add them to `pyproject.toml` using `uv add`.
- Always prefer `pathlib` over `os.path`.
