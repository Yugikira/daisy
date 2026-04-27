"""Daisy - Database schema RAG CLI tool."""

import logging
import os

# Suppress Hugging Face hub and transformers warnings
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["HF_HUB_VERBOSITY"] = "critical"
os.environ["HF_HUB_DISABLE_PROGRESS_BARS"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
os.environ["SAFETENSORS_DISABLE_PROGRESS_BARS"] = "1"
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

__version__ = "0.2.1"
