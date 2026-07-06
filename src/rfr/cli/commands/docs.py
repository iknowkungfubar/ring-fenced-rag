"""Docs CLI commands (list/delete documents)."""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from rfr.cli.client import RfrClient

console = Console()


@click.group(name="docs")
def docs() -> None:
    """Manage indexed documents."""


@docs.command(name="list")
def docs_list() -> None:
    """List all indexed documents."""
    client = RfrClient()
    doc_list = client.list_documents()
    table = Table(title="Indexed Documents")
    table.add_column("ID")
    table.add_column("Title")
    table.add_column("Source")
    for doc in doc_list:
        table.add_row(doc.id, doc.title, doc.source)
    console.print(table)


@docs.command(name="delete")
@click.argument("doc_id")
def docs_delete(doc_id: str) -> None:
    """Delete a document by its ID."""
    client = RfrClient()
    result = client.delete_document(doc_id)
    console.print(f"Deleted document [red]{doc_id}[/]")
