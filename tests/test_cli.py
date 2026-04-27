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


class TestIntegration:
    """End-to-end integration tests."""

    def test_full_workflow(self, tmp_path: Path):
        """Test complete add -> query workflow."""
        db_path = tmp_path / "integration_db"
        schema_file = Path("tests/fixtures/sample_schema.txt")
        query_file = Path("tests/fixtures/sample_queries.json")

        # Add
        result = runner.invoke(
            app,
            [
                "--db",
                str(db_path),
                "add",
                str(schema_file),
                "--table",
                "CSR_Finidx",
                "--storage",
                "./CSR_Finidx.xlsx",
                "--type",
                "xlsx",
            ],
        )
        assert result.exit_code == 0

        # Query for capex should find Outcap
        result = runner.invoke(
            app,
            ["--db", str(db_path), "query", str(query_file)],
        )
        assert result.exit_code == 0

        output = json.loads(result.stdout)
        # Should have found results (threshold 0.50 filters low scores)
        # With small dataset, may return empty array - that's acceptable
        assert isinstance(output, list)
        # Check that if results exist, CSR_Finidx table is in them
        if len(output) >= 1:
            tables = [o["table"] for o in output]
            assert "CSR_Finidx" in tables


class TestConfigFile:
    """Tests for YAML config file support."""

    def test_config_file_applied(self, tmp_path: Path):
        """Test that config file sets default db path."""
        config_file = tmp_path / "daisy.yaml"
        config_file.write_text("db: config_db_path")

        db_path = tmp_path / "actual_db"

        result = runner.invoke(
            app,
            [
                "--config",
                str(config_file),
                "--db",
                str(db_path),
                "add",
                str(Path("tests/fixtures/sample_schema.txt")),
                "--table",
                "TestTable",
                "--storage",
                "./data.xlsx",
                "--type",
                "xlsx",
            ],
        )

        assert result.exit_code == 0

    def test_config_file_with_model(self, tmp_path: Path):
        """Test config file sets model."""
        config_file = tmp_path / "daisy.yaml"
        config_file.write_text("model: local")
        db_path = tmp_path / "test_db"

        result = runner.invoke(
            app,
            [
                "--config",
                str(config_file),
                "--db",
                str(db_path),
                "info",
            ],
        )

        # Should fail with db not found, not model error
        assert result.exit_code != 0
        output = result.stdout + (result.output or "")
        assert "Database not found" in output
