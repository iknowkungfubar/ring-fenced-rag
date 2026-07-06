"""Ring-Fenced RAG CLI — command registration.

Commands are defined in commands/*.py and registered here.
"""
from __future__ import annotations

import click

from rfr import __version__

from rfr.cli.commands.docker import init, up, down, status, logs
from rfr.cli.commands.config import config_group
from rfr.cli.commands.ingest import ingest
from rfr.cli.commands.query import query
from rfr.cli.commands.keys import keys
from rfr.cli.commands.docs import docs
from rfr.cli.commands.standalone import standalone, tui


@click.group(
    invoke_without_command=False,
    help="Ring-Fenced RAG — secure document query with role-based access control.",
)
@click.version_option(version=__version__, prog_name="rfr")
def cli() -> None:
    """Ring-Fenced RAG CLI."""


cli.add_command(init)
cli.add_command(up)
cli.add_command(down)
cli.add_command(status)
cli.add_command(config_group)
cli.add_command(ingest)
cli.add_command(query)
cli.add_command(keys)
cli.add_command(docs)
cli.add_command(standalone)
cli.add_command(logs)
cli.add_command(tui)
