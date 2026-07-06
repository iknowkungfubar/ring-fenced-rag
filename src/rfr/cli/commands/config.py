"""Config CLI commands.

Extracted from cli/__init__.py for modularity.
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

console = Console()


@click.group(name="config")
def config_group() -> None:
    """Manage configuration."""


@config_group.command(name="show")
def config_show() -> None:
    """Print the current resolved configuration."""
    from rfr.config import load_config

    cfg = load_config()
    table = Table(title="Ring-Fenced RAG Configuration")
    table.add_column("Section", style="cyan")
    table.add_column("Key", style="green")
    table.add_column("Value", style="white")
    data = cfg.model_dump(mode="python")
    for section, values in data.items():
        if isinstance(values, dict):
            for k, v in values.items():
                table.add_row(section, k, str(v))
        else:
            table.add_row("root", section, str(values))
    console.print(table)


@config_group.command(name="set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value (e.g., 'llm.model llama3.2:3b')."""
    from rfr.config import AppConfig

    cfg = AppConfig()
    parts = key.split(".")
    obj = cfg
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)
    console.print(f"Set config [bold]{key}[/] = [green]{value}[/]")
