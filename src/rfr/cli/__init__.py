"""Ring-Fenced RAG CLI — the primary user interaction surface.

Usage:
    rfr init                  Generate config + docker-compose.yml
    rfr up                    Start all Docker services
    rfr down                  Stop all Docker services
    rfr status                Show component health
    rfr config show           Print current config
    rfr config set <k> <v>    Update a config value
    rfr ingest <path>         Ingest documents
    rfr query <question>      Ask a question
    rfr keys create <name>    Create API key
    rfr keys list             List API keys
    rfr keys revoke <prefix>  Revoke an API key
    rfr docs list             List indexed documents
    rfr docs delete <doc_id>  Delete a document
    rfr standalone            Run API server without Docker
    rfr logs [service]        Tail Docker logs
    rfr tui                   Launch terminal UI
"""

from __future__ import annotations

import sys

import click

from rfr import __version__


@click.group(
    name="rfr",
    help="Ring-Fenced RAG — self-hosted secure document Q&A",
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.version_option(version=__version__, prog_name="rfr")
def cli() -> None:
    """Ring-Fenced RAG CLI — secure document Q&A with role-based access control."""


@cli.command()
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing config and docker-compose files",
)
def init(force: bool) -> None:
    """Generate default configuration and docker-compose.yml."""
    click.echo("Initializing Ring-Fenced RAG project...")
    # TODO: Implement config generation
    click.echo("Done. Edit .rfr/config.toml to customize, then run 'rfr up'.")


@cli.command()
@click.option("-d", "--detach", is_flag=True, help="Run in background")
@click.option("--gpu", type=click.Choice(["rocm", "cuda", "none"]), default="none")
def up(detach: bool, gpu: str) -> None:
    """Start all Docker services."""
    click.echo("Starting Ring-Fenced RAG services...")
    # TODO: Implement Docker Compose orchestration
    click.echo("Services started.")


@cli.command()
def down() -> None:
    """Stop all Docker services."""
    # TODO: Implement Docker Compose stop
    click.echo("Services stopped.")


@cli.command()
@click.option("--watch", is_flag=True, help="Continuously watch status")
def status(watch: bool) -> None:
    """Show health of all components."""
    # TODO: Implement health check
    click.echo("All components healthy.")


@cli.group()
def config() -> None:
    """Manage configuration."""


@config.command(name="show")
def config_show() -> None:
    """Print the current resolved configuration."""
    from rich.console import Console
    from rich.table import Table

    from rfr.config import load_config

    cfg = load_config()
    console = Console()
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


@config.command(name="set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value (e.g., 'llm.model llama3.2:3b')."""
    click.echo(f"Setting {key} = {value}")
    # TODO: Implement config update
    click.echo("Configuration updated.")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--role", default=None, help="Default role assignment for documents")
@click.option("--pattern", default="**/*.{md,txt,pdf}", help="File glob pattern")
def ingest(path: str, role: str | None, pattern: str) -> None:
    """Ingest documents from a file or directory."""
    click.echo(f"Ingesting documents from {path}...")
    # TODO: Implement ingestion
    click.echo("Ingestion completed.")


@cli.command()
@click.argument("question", nargs=-1, required=True)
@click.option("--role", default=None, help="Override role for this query")
@click.option("--top-k", default=3, help="Number of documents to retrieve")
@click.option("--no-llm", is_flag=True, help="Return retrieved docs only")
def query(question: tuple[str, ...], role: str | None, top_k: int, no_llm: bool) -> None:
    """Ask a question against your indexed documents."""
    q = " ".join(question)
    click.echo(f"Querying: {q}")
    # TODO: Implement query via API or standalone pipeline
    click.echo("No documents indexed yet. Run 'rfr ingest' first.")


@cli.group()
def keys() -> None:
    """Manage API keys."""


@keys.command(name="create")
@click.argument("name")
@click.option("--role", default="user", help="Role for this key")
def keys_create(name: str, role: str) -> None:
    """Create a new API key."""
    click.echo(f"Creating API key '{name}' with role '{role}'...")
    # TODO: Implement key creation via API
    click.echo("API key created.")


@keys.command(name="list")
def keys_list() -> None:
    """List all API keys."""
    click.echo("API keys:")
    # TODO: Implement key listing


@keys.command(name="revoke")
@click.argument("prefix")
def keys_revoke(prefix: str) -> None:
    """Revoke an API key by its prefix."""
    click.echo(f"Revoking API key '{prefix}'...")
    # TODO: Implement key revocation


@cli.group()
def docs() -> None:
    """Manage indexed documents."""


@docs.command(name="list")
def docs_list() -> None:
    """List indexed documents."""
    from rich.console import Console
    from rich.table import Table

    console = Console()
    table = Table(title="Indexed Documents")
    table.add_column("ID")
    table.add_column("Source")
    table.add_column("Chunks")
    table.add_column("Roles")
    console.print(table)
    click.echo("No documents indexed.")


@docs.command(name="delete")
@click.argument("doc_id")
def docs_delete(doc_id: str) -> None:
    """Delete a document by its doc_id."""
    click.echo(f"Deleting document '{doc_id}'...")
    # TODO: Implement document deletion


@cli.command()
@click.option("--port", default=8000, help="Server port")
def standalone(port: int) -> None:
    """Run the API server without Docker (standalone mode)."""
    click.echo(f"Starting standalone server on port {port}...")
    # TODO: Implement standalone server startup
    click.echo("Server stopped.")


@cli.command()
@click.argument("service", required=False, default=None)
@click.option("-f", "--follow", is_flag=True, help="Follow log output")
def logs(service: str | None, follow: bool) -> None:
    """Tail Docker service logs."""
    click.echo(f"Showing logs for {service or 'all services'}...")
    # TODO: Implement log tailing


@cli.command()
def tui() -> None:
    """Launch the terminal user interface."""
    click.echo("Launching TUI...")
    try:
        from textual import __version__ as textual_version  # type: ignore[import-untyped]

        from rfr.cli.tui_app import RFRTuiApp  # type: ignore[import-untyped]

        click.echo(f"Textual v{textual_version}")
        app = RFRTuiApp()
        app.run()
    except ImportError:
        click.echo("TUI dependencies not installed. Run: pip install 'ring-fenced-rag[tui]'")
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    cli()
