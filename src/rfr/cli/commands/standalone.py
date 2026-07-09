"""Standalone and TUI CLI commands."""

from __future__ import annotations

import subprocess

import click
from rich.console import Console

console = Console()


@click.command()
@click.option("--port", default=8000, help="Server port")
@click.option("--reload", is_flag=True, help="Enable auto-reload for development")
def standalone(port: int, reload: bool) -> None:
    """Run the API server directly (without Docker)."""
    cmd = ["uvicorn", "rfr.api.app:app", "--host", "0.0.0.0", "--port", str(port)]
    if reload:
        cmd.append("--reload")
    subprocess.run(cmd)


@click.command()
def tui() -> None:
    """Launch the terminal user interface."""
    from rfr.cli.tui_app import app as tui_app

    tui_app.run()
