"""Ingest CLI command."""

from __future__ import annotations

import click
from rich.console import Console

from rfr.cli.client import RfrClient

console = Console()


@click.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--role", default=None, help="Default role assignment for documents")
@click.option("--pattern", default="**/*", help="File glob pattern")
def ingest(path: str, role: str | None, pattern: str) -> None:
    """Ingest documents from a file or directory."""
    client = RfrClient()
    result = client.ingest_directory(
        path,
        default_role=role if role else "user",
        glob_pattern=pattern,
    )
    console.print(f"Started ingestion from [green]{path}[/] (task: {result.task_id})")
