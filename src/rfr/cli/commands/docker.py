"""Docker CLI commands.

Extracted from cli/__init__.py for modularity.
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console

from rfr import __version__

console = Console()


@click.command()
@click.option("--force", is_flag=True, help="Overwrite existing files")
def init(force: bool) -> None:
    """Generate default config and docker-compose file."""
    from rfr.config import AppConfig

    cfg = AppConfig()
    cfg_path = Path("rfr.yml")
    compose_path = Path("docker-compose.yml")

    if cfg_path.exists() and not force:
        console.print("[yellow]rfr.yml already exists. Use --force to overwrite.[/]")
        return
    cfg.save(cfg_path)
    console.print(f"[green]Created {cfg_path}[/]")

    if compose_path.exists() and not force:
        console.print("[yellow]docker-compose.yml already exists. Use --force to overwrite.[/]")
        return
    _write_default_compose(compose_path)
    console.print(f"[green]Created {compose_path}[/]")
    console.print("\nRun [bold]rfr up[/] to start the stack.")


def _write_default_compose(path: Path) -> None:
    """Write a default docker-compose.yml."""
    compose = """version: "3.8"
services:
  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
    volumes:
      - qdrant_data:/qdrant/storage

  postgres:
    image: postgres:16
    environment:
      POSTGRES_USER: rfr
      POSTGRES_PASSWORD: rfr
      POSTGRES_DB: rfr
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  qdrant_data:
  postgres_data:
"""
    path.write_text(compose)


@click.command()
@click.option("-d", "--detach", is_flag=True, help="Run in background")
@click.option("--gpu", type=click.Choice(["rocm", "cuda", "none"]), default="none")
def up(detach: bool, gpu: str) -> None:
    """Start the RAG stack (Docker Compose)."""
    cmd = ["docker", "compose", "up"]
    if detach:
        cmd.append("-d")
    if gpu in ("rocm", "cuda"):
        cmd.append("--gpu")
        cmd.append(gpu)
    subprocess.run(cmd)


@click.command()
def down() -> None:
    """Stop the RAG stack."""
    subprocess.run(["docker", "compose", "down"])


@click.command()
@click.option("--watch", is_flag=True, help="Continuously watch status")
def status(watch: bool) -> None:
    """Show the health status of all services."""
    _show_docker_status()


def _show_docker_status() -> None:
    """Display Docker container status."""
    result = subprocess.run(
        ["docker", "compose", "ps", "--format", "table"],
        capture_output=True, text=True,
    )
    console.print(result.stdout)


@click.command()
@click.argument("service", required=False, default="")
def logs(service: str) -> None:
    """Tail logs from Docker services."""
    cmd = ["docker", "compose", "logs", "--tail=50", "-f"]
    if service:
        cmd.append(service)
    subprocess.run(cmd)
