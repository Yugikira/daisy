"""Schema file parsing module."""

import re
from pathlib import Path
from typing import Any

BRACKET_PATTERN = re.compile(r"^(\w+)\s*\[(.+?)\]\s*-\s*(.+)$")


def parse_line(line: str) -> dict[str, str]:
    """Parse a single schema line.

    Attempts bracket format: "Abbrev [Name] - Definition"
    Falls back to raw storage if pattern doesn't match.

    Args:
        line: Single line from schema file

    Returns:
        Dict with keys: column, description, definition, raw_content
    """
    line = line.strip()
    match = BRACKET_PATTERN.match(line)

    if match:
        return {
            "column": match.group(1),
            "description": match.group(2),
            "definition": match.group(3),
            "raw_content": line,
        }

    return {
        "column": "",
        "description": "",
        "definition": "",
        "raw_content": line,
    }


def parse_schema_file(path: Path, table: str, storage: str, dtype: str) -> list[dict[str, Any]]:
    """Parse entire schema file into document dicts.

    Args:
        path: Path to schema txt file
        table: Table name for metadata
        storage: Dataset storage path
        dtype: Dataset type (xlsx, csv, etc.)

    Returns:
        List of dicts ready for embedding/insertion, each with:
        - id: "{table}_XXX" format
        - fields: table, column, description, definition, storage, type, raw_content, line_number
    """
    lines = Path(path).read_text(encoding="utf-8").strip().split("\n")
    docs = []

    for i, line in enumerate(lines, start=1):
        parsed = parse_line(line)
        doc_id = f"{table}_{i:03d}"

        doc = {
            "id": doc_id,
            "fields": {
                "table": table,
                "column": parsed["column"],
                "description": parsed["description"],
                "definition": parsed["definition"],
                "storage": storage,
                "type": dtype,
                "raw_content": parsed["raw_content"],
                "line_number": i,
            },
        }
        docs.append(doc)

    return docs