"""Search operations and result merging."""

from typing import Any
from collections import defaultdict


def merge_results(raw_results: list[dict]) -> list[dict]:
    """Merge search results grouped by table.

    Groups results from the same table, combining fields into lists
    to reduce output token count for AI agents.

    Args:
        raw_results: List of per-query results with query_variable, doc_id, fields, score

    Returns:
        List of merged results, one per table
    """
    if not raw_results:
        return []

    # Group by table
    grouped: dict[str, list[dict]] = defaultdict(list)
    for result in raw_results:
        table = result["fields"]["table"]
        grouped[table].append(result)

    merged = []
    for table, results in grouped.items():
        merged_doc = {
            "table": table,
            "query_variables": [r["query_variable"] for r in results],
            "columns": [r["fields"]["column"] for r in results],
            "definitions": [r["fields"]["definition"] for r in results],
            "doc_ids": [r["doc_id"] for r in results],
            "scores": [r["score"] for r in results],
            "storage": results[0]["fields"]["storage"],
            "type": results[0]["fields"]["type"],
        }
        merged.append(merged_doc)

    return merged


def bm25_search(collection: Any, query_text: str, topk: int = 10) -> list[dict]:
    """BM25 sparse search on raw_content field.

    Args:
        collection: Zvec collection
        query_text: Text to search
        topk: Number of results

    Returns:
        List of results with doc_id, score, fields
    """
    # Use zvec's BM25EmbeddingFunction for sparse search
    # Note: This may need adjustment based on actual zvec query API
    results = collection.search(
        query=query_text,
        topk=topk,
        output_fields=[
            "table",
            "column",
            "description",
            "definition",
            "storage",
            "type",
            "raw_content",
        ],
    )

    formatted = []
    for r in results:
        formatted.append(
            {
                "doc_id": r.id,
                "score": r.score,
                "fields": dict(r.fields),
            }
        )

    return formatted


def semantic_search(
    collection: Any, query_vector: list[float], topk: int = 10
) -> list[dict]:
    """Semantic dense vector search.

    Args:
        collection: Zvec collection
        query_vector: Dense embedding vector
        topk: Number of results

    Returns:
        List of results with doc_id, score, fields
    """
    results = collection.query(
        vectors=[{"field_name": "dense_embedding", "vector": query_vector}],
        topk=topk,
        output_fields=[
            "table",
            "column",
            "description",
            "definition",
            "storage",
            "type",
            "raw_content",
        ],
    )

    formatted = []
    for r in results:
        formatted.append(
            {
                "doc_id": r.id,
                "score": r.score,
                "fields": dict(r.fields),
            }
        )

    return formatted


def hybrid_search(
    collection: Any,
    query_text: str,
    query_vector: list[float],
    topk: int = 10,
    rrf_k: int = 60,
) -> list[dict]:
    """Hybrid search combining BM25 and semantic with RRF fusion.

    Args:
        collection: Zvec collection
        query_text: Text for BM25
        query_vector: Dense vector for semantic
        topk: Number of results
        rrf_k: RRF fusion parameter

    Returns:
        List of results with doc_id, score, fields
    """
    results = collection.query(
        vectors=[
            {"field_name": "sparse_embedding", "vector": {}},  # BM25 handled by zvec
            {"field_name": "dense_embedding", "vector": query_vector},
        ],
        topk=topk,
        reranker={"k": rrf_k},
        output_fields=[
            "table",
            "column",
            "description",
            "definition",
            "storage",
            "type",
            "raw_content",
        ],
    )

    formatted = []
    for r in results:
        formatted.append(
            {
                "doc_id": r.id,
                "score": r.score,
                "fields": dict(r.fields),
            }
        )

    return formatted
