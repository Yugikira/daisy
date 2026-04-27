"""Daisy - Database schema RAG CLI tool."""

import logging
import os

# Suppress Hugging Face hub and transformers warnings
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"
logging.getLogger("transformers").setLevel(logging.ERROR)
logging.getLogger("huggingface_hub").setLevel(logging.ERROR)

__version__ = "0.2.0"
