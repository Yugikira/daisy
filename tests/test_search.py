"""Tests for search module."""

from daisy.search import merge_results


class TestMergeResults:
    """Tests for result merging logic."""

    def test_merge_results_single_table(self):
        """Test merging results from single table."""
        raw_results = [
            {
                "query_variable": "capex",
                "doc_id": "CSR_Finidx_004",
                "fields": {
                    "table": "CSR_Finidx",
                    "column": "Outcap",
                    "definition": "Cash paid...",
                    "storage": "./data.xlsx",
                    "type": "xlsx",
                },
                "score": 0.85,
            },
            {
                "query_variable": "stkcd",
                "doc_id": "CSR_Finidx_001",
                "fields": {
                    "table": "CSR_Finidx",
                    "column": "Stkcd",
                    "definition": "Based on...",
                    "storage": "./data.xlsx",
                    "type": "xlsx",
                },
                "score": 0.92,
            },
        ]

        merged = merge_results(raw_results)

        assert len(merged) == 1
        assert merged[0]["table"] == "CSR_Finidx"
        assert merged[0]["query_variables"] == ["capex", "stkcd"]
        assert merged[0]["columns"] == ["Outcap", "Stkcd"]
        assert merged[0]["definitions"] == ["Cash paid...", "Based on..."]
        assert merged[0]["doc_ids"] == ["CSR_Finidx_004", "CSR_Finidx_001"]
        assert merged[0]["scores"] == [0.85, 0.92]
        assert merged[0]["storage"] == "./data.xlsx"
        assert merged[0]["type"] == "xlsx"

    def test_merge_results_multiple_tables(self):
        """Test merging results from multiple tables."""
        raw_results = [
            {
                "query_variable": "var1",
                "doc_id": "TableA_001",
                "fields": {
                    "table": "TableA",
                    "column": "ColA",
                    "definition": "DefA",
                    "storage": "./a.csv",
                    "type": "csv",
                },
                "score": 0.8,
            },
            {
                "query_variable": "var2",
                "doc_id": "TableB_001",
                "fields": {
                    "table": "TableB",
                    "column": "ColB",
                    "definition": "DefB",
                    "storage": "./b.xlsx",
                    "type": "xlsx",
                },
                "score": 0.7,
            },
        ]

        merged = merge_results(raw_results)

        assert len(merged) == 2
        tables = [m["table"] for m in merged]
        assert "TableA" in tables
        assert "TableB" in tables

    def test_merge_results_empty(self):
        """Test merging empty results."""
        merged = merge_results([])
        assert merged == []
