"""Tests for CLI module."""

import json
from pathlib import Path
from typer.testing import CliRunner

from daisy.cli import app

runner = CliRunner()


class TestCLI:
    """Tests for CLI commands."""

    def test_add_command_creates_db(self, tmp_path: Path):
        """Test add command creates database and inserts docs."""
        db_path = tmp_path / "test_db"
        schema_file = Path("tests/fixtures/sample_schema.txt")

        result = runner.invoke(
            app,
            [
                "--db",
                str(db_path),
                "add",
                str(schema_file),
                "--table",
                "TestTable",
                "--storage",
                "./data.xlsx",
                "--type",
                "xlsx",
            ],
        )

        assert result.exit_code == 0
        assert db_path.exists()

    def test_info_command(self, tmp_path: Path):
        """Test info command shows stats."""
        db_path = tmp_path / "test_db"
        schema_file = Path("tests/fixtures/sample_schema.txt")

        # First add some data
        runner.invoke(
            app,
            [
                "--db",
                str(db_path),
                "add",
                str(schema_file),
                "--table",
                "TestTable",
                "--storage",
                "./data.xlsx",
                "--type",
                "xlsx",
            ],
        )

        # Then check info
        result = runner.invoke(app, ["--db", str(db_path), "info"])

        assert result.exit_code == 0
        assert "doc_count" in result.stdout

    def test_query_command_returns_json(self, tmp_path: Path):
        """Test query command returns valid JSON."""
        db_path = tmp_path / "test_db"
        schema_file = Path("tests/fixtures/sample_schema.txt")
        query_file = Path("tests/fixtures/sample_queries.json")

        # Add data first
        runner.invoke(
            app,
            [
                "--db",
                str(db_path),
                "add",
                str(schema_file),
                "--table",
                "TestTable",
                "--storage",
                "./data.xlsx",
                "--type",
                "xlsx",
            ],
        )

        # Query
        result = runner.invoke(
            app,
            ["--db", str(db_path), "query", str(query_file)],
        )

        assert result.exit_code == 0
        # Parse output as JSON
        output = json.loads(result.stdout)
        assert isinstance(output, list)
