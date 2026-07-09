"""Query CLI command."""

from __future__ import annotations

import click
from rich.console import Console

from rfr.cli.client import RfrClient

console = Console()


@click.command()
@click.argument("question", nargs=-1, required=True)
@click.option("--role", default=None, help="Override role for this query")
@click.option("--top-k", default=3, help="Number of documents to retrieve")
@click.option("--no-llm", is_flag=True, help="Return retrieved docs only")
def query(question: tuple[str, ...], role: str | None, top_k: int, no_llm: bool) -> None:
    """Ask a question against your indexed documents."""
    client = RfrClient()
    q = " ".join(question)
    response = client.query(q, top_k=top_k)
    console.print(f"[bold]Answer:[/] {response.answer}")
    if response.sources:
        console.print("\n[bold]Sources:[/]")
        for src in response.sources:
            console.print(f"  - {src.title} ({src.score:.2f})")
