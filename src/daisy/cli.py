"""CLI entry point using Typer."""

import json
from pathlib import Path
from typing import Annotated

import typer

from daisy.config import (
    DEFAULT_MODEL,
    DEFAULT_TOPK,
    load_config,
    merge_config,
)
from daisy.parser import parse_schema_file
from daisy.database import create_collection, open_collection, insert_docs, get_stats
from daisy.embeddings import get_embedding_model


# Global state for options
state: dict = {
    "db": Path("./daisy_db"),
    "model": DEFAULT_MODEL,
}


app = typer.Typer(
    name="daisy",
    help="Database schema RAG CLI with hybrid search",
)


@app.callback()
def main(
    db: Annotated[Path | None, typer.Option("--db", "-d", help="Database path")] = None,
    model: Annotated[
        str | None, typer.Option("--model", "-m", help="Embedding model")
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", "-c", help="YAML config file path"),
    ] = None,
):
    """Database schema RAG CLI with hybrid search."""
    defaults = {"db": Path("./daisy_db"), "model": DEFAULT_MODEL}

    if config:
        config_values = load_config(config)
        defaults = merge_config(defaults, config_values)

    state["db"] = db if db is not None else defaults["db"]
    state["model"] = model if model is not None else defaults["model"]


@app.command()
def add(
    file: Annotated[Path, typer.Argument(help="Schema file path")],
    table: Annotated[
        str | None, typer.Option("--table", "-t", help="Table name")
    ] = None,
    storage: Annotated[
        str | None, typer.Option("--storage", "-s", help="Dataset storage path")
    ] = None,
    type: Annotated[
        str | None, typer.Option("--type", help="Dataset type (xlsx, csv, etc.)")
    ] = None,
    schema: Annotated[
        str | None,
        typer.Option(
            "--schema",
            help="JSON dict with table, storage, and type (e.g. '{\"table\": \"T\", \"storage\": \"./data.xlsx\", \"type\": \"xlsx\"}')",
        ),
    ] = None,
    model: Annotated[
        str | None, typer.Option("--model", "-m", help="Embedding model")
    ] = None,
):
    """Add schema file to database.

    Provide metadata via individual flags (--table, --storage, --type)
    or a single --schema JSON dict containing all three.
    """
    db_path = state["db"]
    model_name = model or state["model"]

    if not file.exists():
        typer.echo(f"Error: Cannot read file {file}", err=True)
        raise typer.Exit(1)

    # Resolve metadata from --schema JSON or individual flags
    if schema:
        try:
            meta = json.loads(schema)
        except json.JSONDecodeError as e:
            typer.echo(f"Error: Invalid --schema JSON: {e}", err=True)
            raise typer.Exit(1)
        tbl = meta.get("table")
        stor = meta.get("storage")
        typ = meta.get("type")
    else:
        tbl, stor, typ = table, storage, type

    if not tbl or not stor or not typ:
        typer.echo(
            "Error: --schema JSON or all of --table, --storage, --type are required",
            err=True,
        )
        raise typer.Exit(1)

    # Parse schema file
    docs = parse_schema_file(file, tbl, stor, typ)

    # Create/open collection and insert
    collection = create_collection(db_path)
    embed_model = get_embedding_model(model_name)
    count = insert_docs(collection, docs, embed_model)

    typer.echo(f"Added {count} documents from {file} to {db_path}")


@app.command()
def info():
    """Show database stats."""
    db = state["db"]
    if not db.exists():
        typer.echo(f"Error: Database not found at {db}", err=True)
        raise typer.Exit(1)

    collection = open_collection(db)
    stats = get_stats(collection)

    typer.echo(json.dumps(stats, indent=2))


@app.command()
def query(
    queries: Annotated[Path, typer.Argument(help="Query JSON file")],
    model: Annotated[
        str | None, typer.Option("--model", "-m", help="Embedding model")
    ] = None,
    topk: Annotated[
        int, typer.Option("--topk", "-k", help="Number of results")
    ] = DEFAULT_TOPK,
    filters: Annotated[
        list[str] | None,
        typer.Option(
            "--filter", "-f", help="Zvec filter expression (repeatable, joined with AND)"
        ),
    ] = None,
):
    """Hybrid search (BM25 + semantic with RRF fusion)."""
    db = state["db"]
    model_name = model or state["model"]
    if not db.exists():
        typer.echo(f"Error: Database not found at {db}", err=True)
        raise typer.Exit(1)

    if not queries.exists():
        typer.echo(f"Error: Cannot read file {queries}", err=True)
        raise typer.Exit(1)

    collection = open_collection(db)
    embed_model = get_embedding_model(model_name)
    query_list = json.loads(queries.read_text())

    from daisy.search import hybrid_search, merge_results

    results = []
    for q in query_list:
        query_text = (
            q.get("variable", "")
            + " "
            + q.get("description", "")
            + " "
            + q.get("definition", "")
        ).strip()
        query_vec = embed_model.encode(query_text).tolist()
        matches = hybrid_search(collection, query_text, query_vec, topk, filters=filters)

        for match in matches:
            results.append(
                {
                    "query_variable": q["variable"],
                    "doc_id": match["doc_id"],
                    "fields": match["fields"],
                    "score": match["score"],
                }
            )

    merged = merge_results(results)
    typer.echo(json.dumps(merged, indent=2))


@app.command()
def search(
    queries: Annotated[Path, typer.Argument(help="Query JSON file")],
    topk: Annotated[
        int, typer.Option("--topk", "-k", help="Number of results")
    ] = DEFAULT_TOPK,
    filters: Annotated[
        list[str] | None,
        typer.Option(
            "--filter", "-f", help="Zvec filter expression (repeatable, joined with AND)"
        ),
    ] = None,
):
    """BM25/sparse keyword search."""
    db = state["db"]
    if not db.exists():
        typer.echo(f"Error: Database not found at {db}", err=True)
        raise typer.Exit(1)

    if not queries.exists():
        typer.echo(f"Error: Cannot read file {queries}", err=True)
        raise typer.Exit(1)

    collection = open_collection(db)
    query_list = json.loads(queries.read_text())

    from daisy.search import bm25_search, merge_results

    results = []
    for q in query_list:
        query_text = (q.get("variable", "") + " " + q.get("description", "")).strip()
        matches = bm25_search(collection, query_text, topk, filters=filters)

        for match in matches:
            results.append(
                {
                    "query_variable": q["variable"],
                    "doc_id": match["doc_id"],
                    "fields": match["fields"],
                    "score": match["score"],
                }
            )

    merged = merge_results(results)
    typer.echo(json.dumps(merged, indent=2))


@app.command()
def vsearch(
    queries: Annotated[Path, typer.Argument(help="Query JSON file")],
    model: Annotated[
        str | None, typer.Option("--model", "-m", help="Embedding model")
    ] = None,
    topk: Annotated[
        int, typer.Option("--topk", "-k", help="Number of results")
    ] = DEFAULT_TOPK,
    filters: Annotated[
        list[str] | None,
        typer.Option(
            "--filter", "-f", help="Zvec filter expression (repeatable, joined with AND)"
        ),
    ] = None,
):
    """Semantic vector search."""
    db = state["db"]
    model_name = model or state["model"]
    if not db.exists():
        typer.echo(f"Error: Database not found at {db}", err=True)
        raise typer.Exit(1)

    if not queries.exists():
        typer.echo(f"Error: Cannot read file {queries}", err=True)
        raise typer.Exit(1)

    collection = open_collection(db)
    embed_model = get_embedding_model(model_name)
    query_list = json.loads(queries.read_text())

    from daisy.search import merge_results, semantic_search

    results = []
    for q in query_list:
        query_text = (
            q.get("variable", "")
            + " "
            + q.get("description", "")
            + " "
            + q.get("definition", "")
        ).strip()
        query_vec = embed_model.encode(query_text).tolist()
        matches = semantic_search(collection, query_vec, topk, filters=filters)

        for match in matches:
            results.append(
                {
                    "query_variable": q["variable"],
                    "doc_id": match["doc_id"],
                    "fields": match["fields"],
                    "score": match["score"],
                }
            )

    merged = merge_results(results)
    typer.echo(json.dumps(merged, indent=2))
