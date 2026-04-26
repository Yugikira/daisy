"""Tests for embeddings module."""

import pytest
from daisy.embeddings import get_dense_embedding, get_embedding_model


class TestEmbeddings:
    """Tests for embedding functions."""

    def test_get_embedding_model_local(self):
        """Test loading local model."""
        model = get_embedding_model("local")
        assert model is not None

    def test_get_embedding_model_unknown_raises(self):
        """Test unknown model raises error."""
        with pytest.raises(ValueError, match="Unknown model"):
            get_embedding_model("unknown_model")

    def test_get_dense_embedding_returns_vector(self):
        """Test dense embedding returns correct dimension."""
        model = get_embedding_model("local")
        vector = get_dense_embedding("test text", model)

        assert isinstance(vector, list)
        assert len(vector) == 384  # all-MiniLM-L6-v2 dimension
        assert all(isinstance(v, float) for v in vector)