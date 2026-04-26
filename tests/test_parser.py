"""Tests for parser module."""

import pytest
from pathlib import Path
from daisy.parser import parse_line, parse_schema_file


class TestParseLine:
    """Tests for parse_line function."""

    def test_parse_line_bracket_format(self):
        """Test parsing standard bracket format."""
        line = "Stkcd [Stock Code] - Based on the stock code published by the exchange."
        result = parse_line(line)

        assert result["column"] == "Stkcd"
        assert result["description"] == "Stock Code"
        assert result["definition"] == "Based on the stock code published by the exchange."
        assert result["raw_content"] == line

    def test_parse_line_bracket_with_spaces(self):
        """Test parsing with extra spaces."""
        line = "Accper  [Reporting Period]  -  Expressed in YYYY-MM-DD format."
        result = parse_line(line)

        assert result["column"] == "Accper"
        assert result["description"] == "Reporting Period"
        assert result["definition"] == "Expressed in YYYY-MM-DD format."

    def test_parse_line_fallback_to_raw(self):
        """Test fallback when format doesn't match."""
        line = "stkcd, Stock Code, Based on exchange"
        result = parse_line(line)

        assert result["column"] == ""
        assert result["description"] == ""
        assert result["definition"] == ""
        assert result["raw_content"] == line

    def test_parse_line_empty(self):
        """Test parsing empty line."""
        result = parse_line("")
        assert result["raw_content"] == ""
        assert result["column"] == ""


class TestParseSchemaFile:
    """Tests for parse_schema_file function."""

    def test_parse_schema_file(self, tmp_path: Path):
        """Test parsing entire schema file."""
        schema_file = tmp_path / "test.txt"
        schema_file.write_text(
            "Stkcd [Stock Code] - Based on the exchange.\n"
            "Accper [Period] - YYYY-MM-DD format.\n"
        )

        docs = parse_schema_file(schema_file, "TestTable", "./data.xlsx", "xlsx")

        assert len(docs) == 2
        assert docs[0]["id"] == "TestTable_001"
        assert docs[0]["fields"]["table"] == "TestTable"
        assert docs[0]["fields"]["column"] == "Stkcd"
        assert docs[0]["fields"]["line_number"] == 1
        assert docs[1]["id"] == "TestTable_002"
        assert docs[1]["fields"]["line_number"] == 2