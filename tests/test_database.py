"""Tests for database module."""

import pytest
from pathlib import Path
from daisy.database import create_collection, open_collection, get_collection_schema


class TestDatabase:
    """Tests for database operations."""

    def test_create_collection(self, tmp_path: Path):
        """Test creating a new collection."""
        db_path = tmp_path / "test_db"
        collection = create_collection(db_path)

        assert collection is not None
        assert (db_path).exists()

    def test_open_collection_existing(self, tmp_path: Path):
        """Test opening existing collection."""
        db_path = tmp_path / "test_db"
        create_collection(db_path)

        collection = open_collection(db_path)
        assert collection is not None

    def test_open_collection_missing_raises(self, tmp_path: Path):
        """Test opening missing collection raises error."""
        db_path = tmp_path / "missing_db"

        with pytest.raises(FileNotFoundError):
            open_collection(db_path)

    def test_get_collection_schema(self):
        """Test schema has correct fields."""
        schema = get_collection_schema()

        field_names = [f.name for f in schema.fields]
        assert "table" in field_names
        assert "column" in field_names
        assert "raw_content" in field_names

        vector_names = [v.name for v in schema.vectors]
        assert "dense_embedding" in vector_names
        assert "sparse_embedding" in vector_names
