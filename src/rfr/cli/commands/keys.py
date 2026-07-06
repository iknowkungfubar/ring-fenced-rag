"""Keys CLI commands.

Extracted from cli/__init__.py for modularity.
"""
from __future__ import annotations

import click
from rich.console import Console
from rich.table import Table

from rfr.cli.client import RfrClient

console = Console()


def _get_client() -> RfrClient:
    """Create an API client connected to the configured server."""
    return RfrClient()


@click.group(name="keys")
def keys() -> None:
    """Manage API keys."""


@keys.command(name="create")
@click.argument("name")
@click.option("--role", default="admin", help="Role for the key (viewer, editor, admin)")
def keys_create(name: str, role: str) -> None:
    """Create a new API key."""
    client = _get_client()
    result = client.create_key(name, role)
    console.print(f"Created key [bold green]{result['key']}[/]")


@keys.command(name="list")
def keys_list() -> None:
    """List all active API keys."""
    client = _get_client()
    keys_data = client.list_keys()
    table = Table(title="API Keys")
    table.add_column("Prefix")
    table.add_column("Name")
    table.add_column("Role")
    table.add_column("Created")
    for k in keys_data:
        table.add_row(k["prefix"], k["name"], k["role"], k["created_at"])
    console.print(table)


@keys.command(name="revoke")
@click.argument("prefix")
def keys_revoke(prefix: str) -> None:
    """Revoke an API key by its prefix."""
    client = _get_client()
    client.revoke_key(prefix)
    console.print(f"Revoked key with prefix [bold red]{prefix}[/]")
