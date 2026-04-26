"""Configuration constants and model registry."""

from pathlib import Path

DEFAULT_MODEL = "all-MiniLM-L6-v2"
DEFAULT_DENSE_DIMENSION = 384
DEFAULT_TOPK = 10
DEFAULT_HNSW_EF_CONSTRUCTION = 200
DEFAULT_HNSW_M = 16

MODEL_REGISTRY = {
    "all-MiniLM-L6-v2": {
        "type": "local",
        "dimension": 384,
        "class": "sentence_transformers",
        "model": "all-MiniLM-L6-v2",
    },
    "local": {
        "type": "local",
        "dimension": 384,
        "class": "sentence_transformers",
        "model": "all-MiniLM-L6-v2",
    },
    "openai": {
        "type": "api",
        "dimension": 1536,
        "class": "openai",
        "model": "text-embedding-3-small",
    },
    "qwen": {
        "type": "api",
        "dimension": 1024,
        "class": "qwen",
    },
}


def get_model_config(model_name: str) -> dict:
    """Get model configuration from registry.

    Args:
        model_name: Name of the model (key in MODEL_REGISTRY)

    Returns:
        Model configuration dict

    Raises:
        ValueError: If model name not in registry
    """
    if model_name not in MODEL_REGISTRY:
        raise ValueError(f"Unknown model: {model_name}. Available: {list(MODEL_REGISTRY.keys())}")
    return MODEL_REGISTRY[model_name]