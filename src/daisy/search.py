"""Search operations and result merging."""

from typing import Any
from collections import defaultdict

from zvec import VectorQuery, RrfReRanker, DefaultLocalSparseEmbedding

# Global sparse embedding function using SPLADE
_sparse_ef = DefaultLocalSparseEmbedding(encoding_type="query")

# Minimum score threshold for semantic dense vector search (cosine similarity range)
MIN_SCORE_THRESHOLD = 0.50

# Minimum score threshold for hybrid RRF-fused results (1/(k+1) + 1/(k+1) range)
MIN_HYBRID_THRESHOLD = 0.01


def _filter_by_score(results: list[dict], min_score: float) -> list[dict]:
    """Filter results below minimum score threshold."""
    return [r for r in results if r["score"] >= min_score]


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
    """Sparse keyword search using SPLADE embeddings.

    Args:
        collection: Zvec collection
        query_text: Text to search
        topk: Number of results

    Returns:
        List of results with doc_id, score, fields
    """
    # Generate sparse vector using SPLADE and query
    sparse_vec = _sparse_ef.embed(query_text)
    sparse_query = VectorQuery(field_name="sparse_embedding", vector=sparse_vec)

    results = collection.query(
        vectors=sparse_query,
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
    collection: Any,
    query_vector: list[float],
    topk: int = 10,
    min_score: float = MIN_SCORE_THRESHOLD,
) -> list[dict]:
    """Semantic dense vector search.

    Args:
        collection: Zvec collection
        query_vector: Dense embedding vector
        topk: Number of results
        min_score: Minimum score threshold (default 0.50)

    Returns:
        List of results with doc_id, score, fields
    """
    vector_query = VectorQuery(field_name="dense_embedding", vector=query_vector)
    results = collection.query(
        vectors=vector_query,
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

    return _filter_by_score(formatted, min_score)


def hybrid_search(
    collection: Any,
    query_text: str,
    query_vector: list[float],
    topk: int = 10,
    rrf_k: int = 60,
    min_score: float = MIN_HYBRID_THRESHOLD,
) -> list[dict]:
    """Hybrid search combining BM25 and semantic with RRF fusion.

    Args:
        collection: Zvec collection
        query_text: Text for BM25
        query_vector: Dense vector for semantic
        topk: Number of results
        rrf_k: RRF fusion parameter
        min_score: Minimum RRF score threshold (default 0.01)

    Returns:
        List of results with doc_id, score, fields
    """
    # Create vector queries for both dense and sparse
    dense_query = VectorQuery(field_name="dense_embedding", vector=query_vector)
    # Generate sparse vector using SPLADE
    sparse_vec = _sparse_ef.embed(query_text)
    sparse_query = VectorQuery(field_name="sparse_embedding", vector=sparse_vec)

    reranker = RrfReRanker(topn=topk, rank_constant=rrf_k)

    results = collection.query(
        vectors=[dense_query, sparse_query],
        topk=topk,
        reranker=reranker,
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

    return _filter_by_score(formatted, min_score)
