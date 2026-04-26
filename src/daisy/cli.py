"""CLI entry point using Typer."""

import json
from pathlib import Path
from typing import Annotated

import typer

from daisy.config import DEFAULT_MODEL, DEFAULT_TOPK
from daisy.parser import parse_schema_file
from daisy.database import create_collection, open_collection, insert_docs, get_stats
from daisy.embeddings import get_embedding_model


# Global state for options
state = {"db": Path("./daisy_db")}


app = typer.Typer(
    name="daisy",
    help="Database schema RAG CLI with hybrid search",
)


@app.callback()
def main(
    db: Annotated[Path, typer.Option("--db", "-d", help="Database path")] = Path(
        "./daisy_db"
    ),
):
    """Database schema RAG CLI with hybrid search."""
    state["db"] = db


@app.command()
def add(
    file: Annotated[Path, typer.Argument(help="Schema file path")],
    table: Annotated[str, typer.Option("--table", "-t", help="Table name")],
    storage: Annotated[
        str, typer.Option("--storage", "-s", help="Dataset storage path")
    ],
    type: Annotated[str, typer.Option("--type", help="Dataset type (xlsx, csv, etc.)")],
    model: Annotated[
        str, typer.Option("--model", "-m", help="Embedding model")
    ] = DEFAULT_MODEL,
):
    """Add schema file to database."""
    db = state["db"]
    if not file.exists():
        typer.echo(f"Error: Cannot read file {file}", err=True)
        raise typer.Exit(1)

    # Parse schema file
    docs = parse_schema_file(file, table, storage, type)

    # Create/open collection and insert
    collection = create_collection(db)
    embed_model = get_embedding_model(model)
    count = insert_docs(collection, docs, embed_model)

    typer.echo(f"Added {count} documents from {file} to {db}")


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
        str, typer.Option("--model", "-m", help="Embedding model")
    ] = DEFAULT_MODEL,
    topk: Annotated[
        int, typer.Option("--topk", "-k", help="Number of results")
    ] = DEFAULT_TOPK,
):
    """Hybrid search (BM25 + semantic with RRF fusion)."""
    db = state["db"]
    if not db.exists():
        typer.echo(f"Error: Database not found at {db}", err=True)
        raise typer.Exit(1)

    if not queries.exists():
        typer.echo(f"Error: Cannot read file {queries}", err=True)
        raise typer.Exit(1)

    collection = open_collection(db)
    embed_model = get_embedding_model(model)
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
        matches = hybrid_search(collection, query_text, query_vec, topk)

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
