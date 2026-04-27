"""Zvec collection management."""

from pathlib import Path
from typing import Any

import zvec
from zvec import (
    CollectionSchema,
    FieldSchema,
    VectorSchema,
    DataType,
    HnswIndexParam,
    InvertIndexParam,
    CollectionOption,
    Doc,
)

from daisy.config import (
    DEFAULT_DENSE_DIMENSION,
    DEFAULT_HNSW_EF_CONSTRUCTION,
    DEFAULT_HNSW_M,
)


def get_collection_schema() -> CollectionSchema:
    """Create the standard collection schema for schema documents.

    Returns:
        CollectionSchema with all fields and vectors defined
    """
    return CollectionSchema(
        name="schema_docs",
        fields=[
            FieldSchema(
                "table", DataType.STRING, nullable=False, index_param=InvertIndexParam()
            ),
            FieldSchema(
                "column", DataType.STRING, nullable=True, index_param=InvertIndexParam()
            ),
            FieldSchema(
                "description",
                DataType.STRING,
                nullable=True,
                index_param=InvertIndexParam(),
            ),
            FieldSchema("definition", DataType.STRING, nullable=True),
            FieldSchema("storage", DataType.STRING, nullable=True),
            FieldSchema(
                "type", DataType.STRING, nullable=True, index_param=InvertIndexParam()
            ),
            FieldSchema(
                "raw_content",
                DataType.STRING,
                nullable=False,
                index_param=InvertIndexParam(),
            ),
            FieldSchema("line_number", DataType.INT64, nullable=True),
        ],
        vectors=[
            VectorSchema(
                "dense_embedding",
                DataType.VECTOR_FP32,
                dimension=DEFAULT_DENSE_DIMENSION,
                index_param=HnswIndexParam(
                    ef_construction=DEFAULT_HNSW_EF_CONSTRUCTION,
                    m=DEFAULT_HNSW_M,
                ),
            ),
            VectorSchema(
                "sparse_embedding",
                DataType.SPARSE_VECTOR_FP32,
                index_param=HnswIndexParam(),
            ),
        ],
    )


def create_collection(path: Path) -> Any:
    """Create and open a new collection.

    Args:
        path: Path for database storage

    Returns:
        Collection instance
    """
    path = Path(path)
    schema = get_collection_schema()
    option = CollectionOption(read_only=False, enable_mmap=True)

    return zvec.create_and_open(path=str(path), schema=schema, option=option)


def open_collection(path: Path) -> Any:
    """Open an existing collection.

    Args:
        path: Path to existing database

    Returns:
        Collection instance

    Raises:
        FileNotFoundError: If database doesn't exist
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Database not found at {path}")

    option = CollectionOption(read_only=False, enable_mmap=True)

    return zvec.open(path=str(path), option=option)


def insert_docs(collection: Any, docs: list[dict], dense_model: Any) -> int:
    """Insert documents with embeddings into collection.

    Args:
        collection: Zvec collection instance
        docs: List of doc dicts from parser
        dense_model: Embedding model for dense vectors

    Returns:
        Number of documents inserted
    """
    from daisy.embeddings import get_dense_embedding
    from daisy.search import _sparse_ef

    zvec_docs = []
    for doc in docs:
        raw_content = doc["fields"]["raw_content"]
        dense_vec = get_dense_embedding(raw_content, dense_model)
        sparse_vec = _sparse_ef.embed(raw_content)

        zvec_doc = Doc(
            id=doc["id"],
            fields=doc["fields"],
            vectors={
                "dense_embedding": dense_vec,
                "sparse_embedding": sparse_vec,
            },
        )
        zvec_docs.append(zvec_doc)

    collection.insert(zvec_docs)
    return len(zvec_docs)


def get_stats(collection: Any) -> dict:
    """Get collection statistics.

    Args:
        collection: Zvec collection instance

    Returns:
        Dict with stats: doc_count, path, schema_name
    """
    stats = collection.stats
    return {
        "doc_count": stats.doc_count,
        "path": collection.path,
        "schema_name": collection.schema.name,
    }
