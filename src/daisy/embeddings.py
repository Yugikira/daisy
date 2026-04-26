"""Embedding model management."""

import os
import warnings
from typing import Any

from sentence_transformers import SentenceTransformer

from daisy.config import DEFAULT_DENSE_DIMENSION, DEFAULT_MODEL, MODEL_REGISTRY

_model_cache: dict[str, Any] = {}


def get_embedding_model(model_name: str) -> Any:
    """Load or retrieve cached embedding model.

    Args:
        model_name: Model name from registry

    Returns:
        Embedding model instance

    Raises:
        ValueError: If model not in registry
    """
    if model_name in _model_cache:
        return _model_cache[model_name]

    config = MODEL_REGISTRY.get(model_name)
    if not config:
        raise ValueError(
            f"Unknown model: {model_name}. Available: {list(MODEL_REGISTRY.keys())}"
        )

    if config["type"] == "local":
        model_id = config.get("model", model_name)
        model = SentenceTransformer(model_id)
        _model_cache[model_name] = model
        return model

    if config["type"] == "api":
        api_key = os.environ.get(f"{config['class'].upper()}_API_KEY")
        if not api_key:
            warnings.warn(
                f"API key not found for {config['class']}. Falling back to {DEFAULT_MODEL}"
            )
            return get_embedding_model(DEFAULT_MODEL)
        # API models would be implemented here - for now fallback to local
        return get_embedding_model(DEFAULT_MODEL)

    raise ValueError(f"Unknown model type: {config['type']}")


def get_dense_embedding(text: str, model: Any) -> list[float]:
    """Generate dense embedding vector.

    Args:
        text: Text to embed
        model: Embedding model instance

    Returns:
        List of float values (embedding vector)
    """
    if not text.strip():
        # Return zero vector for empty text
        dim = DEFAULT_DENSE_DIMENSION
        return [0.0] * dim

    embedding = model.encode(text)
    return embedding.tolist()
