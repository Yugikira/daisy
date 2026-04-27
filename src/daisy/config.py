"""Configuration constants and model registry."""

from pathlib import Path
from typing import Any

import yaml

DEFAULT_MODEL = "all-MiniLM-L6-v2"
DEFAULT_DENSE_DIMENSION = 384
DEFAULT_TOPK = 3
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
        raise ValueError(
            f"Unknown model: {model_name}. Available: {list(MODEL_REGISTRY.keys())}"
        )
    return MODEL_REGISTRY[model_name]


def load_config(path: Path) -> dict[str, Any]:
    """Load configuration from a YAML file.

    Args:
        path: Path to YAML config file

    Returns:
        Dict with config values

    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid YAML
    """
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    try:
        config = yaml.safe_load(path.read_text())
    except yaml.YAMLError as e:
        raise ValueError(f"Invalid YAML in config file {path}: {e}")

    return config if isinstance(config, dict) else {}


def merge_config(
    defaults: dict[str, Any], config_file: dict[str, Any]
) -> dict[str, Any]:
    """Merge config file values over defaults.

    CLI arguments take precedence over config file, which takes
    precedence over defaults. This merges config onto defaults.

    Args:
        defaults: Default config values
        config_file: Values from YAML config file

    Returns:
        Merged config dict
    """
    merged = defaults.copy()
    for key, value in config_file.items():
        if value is not None:
            merged[key] = value
    return merged
