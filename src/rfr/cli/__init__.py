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

import os
import subprocess
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from rfr import __version__

console = Console()


def _get_client() -> object:
    """Create an API client connected to the configured server."""
    from rfr.cli.client import RfrClient

    return RfrClient()


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
    from rfr.config import AppConfig, load_config

    console.print("[bold]Initializing Ring-Fenced RAG...[/bold]")

    # Create ~/.rfr/ directory
    config_dir = Path.home() / ".rfr"
    config_dir.mkdir(parents=True, exist_ok=True)

    # Generate config
    config_path = config_dir / "config.toml"
    if config_path.exists() and not force:
        console.print(f"[yellow]Config already exists at {config_path}[/yellow]")
        console.print("Use --force to overwrite.")
    else:
        cfg = load_config()
        cfg.save(config_path)
        console.print(f"[green]Created {config_path}[/green]")

    # Generate docker-compose.yml in current directory
    compose_path = Path.cwd() / "docker-compose.yml"
    if compose_path.exists() and not force:
        console.print("[yellow]docker-compose.yml already exists[/yellow]")
    else:
        _write_default_compose(compose_path)
        console.print(f"[green]Created {compose_path}[/green]")

    console.print("\n[bold]Next steps:[/bold]")
    console.print("  1. Edit ~/.rfr/config.toml to customize")
    console.print("  2. Run [bold]rfr up[/bold] to start the stack")
    console.print("  3. Run [bold]rfr ingest ./docs/[/bold] to add documents")
    console.print('  4. Run [bold]rfr query "your question"[/bold]')


def _write_default_compose(path: Path) -> None:
    """Write the default docker-compose.yml."""
    content = """services:
  vector-db:
    image: pgvector/pgvector:0.8.0-pg17
    container_name: rfr-vector-db
    restart: unless-stopped
    ports:
      - "5432:5432"
    environment:
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: secure_password
      POSTGRES_DB: rag_internal
    volumes:
      - pgvector_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U admin -d rag_internal"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: rfr-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  pgvector_data:
  redis_data:
"""
    path.write_text(content)


@cli.command()
@click.option("-d", "--detach", is_flag=True, help="Run in background")
@click.option("--gpu", type=click.Choice(["rocm", "cuda", "none"]), default="none")
def up(detach: bool, _gpu: str) -> None:
    """Start all Docker services."""
    compose_file = Path.cwd() / "docker-compose.yml"
    if not compose_file.exists():
        console.print("[red]No docker-compose.yml found. Run 'rfr init' first.[/red]")
        sys.exit(1)

    cmd = (
        ["docker", "compose", "-f", str(compose_file), "up", "-d"]
        if detach
        else ["docker", "compose", "-f", str(compose_file), "up"]
    )
    console.print("[bold]Starting Ring-Fenced RAG services...[/bold]")
    try:
        subprocess.run(cmd, check=True)  # noqa: S603
        console.print("[green]Services started successfully.[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to start services: {e}[/red]")
        sys.exit(1)
    except FileNotFoundError:
        console.print("[red]Docker not found. Is Docker installed?[/red]")
        sys.exit(1)


@cli.command()
def down() -> None:
    """Stop all Docker services."""
    compose_file = Path.cwd() / "docker-compose.yml"
    if not compose_file.exists():
        console.print("[red]No docker-compose.yml found.[/red]")
        sys.exit(1)

    console.print("[bold]Stopping services...[/bold]")
    try:
        subprocess.run(
            ["docker", "compose", "-f", str(compose_file), "down"],
            check=True,
        )
        console.print("[green]Services stopped.[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to stop services: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--watch", is_flag=True, help="Continuously watch status")
def status(watch: bool) -> None:
    """Show health of all components."""
    from rfr.cli.client import RfrClient, RfrClientError

    try:
        client = RfrClient()
        health = client.health()

        table = Table(title="Ring-Fenced RAG — Component Health")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Details")

        table.add_row("API Server", f"v{health.version}", f"Uptime: {health.uptime_seconds:.0f}s")
        for component, status_text in health.components.items():
            status_style = (
                "green"
                if status_text == "connected"
                else "yellow"
                if status_text == "configured"
                else "red"
            )
            table.add_row(
                component.capitalize(), f"[{status_style}]{status_text}[/{status_style}]", ""
            )

        console.print(table)
    except RfrClientError as e:
        console.print(f"[red]{e}[/red]")
        # Also check Docker status
        _show_docker_status()


def _show_docker_status() -> None:
    """Show Docker container status as fallback."""
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "table {{.Names}}\t{{.Status}}\t{{.Ports}}"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            console.print("\n[bold]Docker containers:[/bold]")
            console.print(result.stdout)
    except FileNotFoundError:
        pass


@cli.group()
def config() -> None:
    """Manage configuration."""


@config.command(name="show")
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


@config.command(name="set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str) -> None:
    """Set a configuration value (e.g., 'llm.model llama3.2:3b')."""
    from rfr.config import AppConfig

    cfg = AppConfig()
    # Parse dotted key path (e.g., "llm.model" -> cfg.llm.model)
    parts = key.split(".")
    obj = cfg
    for part in parts[:-1]:
        obj = getattr(obj, part)
    setattr(obj, parts[-1], value)
    cfg.save()
    console.print(f"[green]Set {key} = {value}[/green]")


@cli.command()
@click.argument("path", type=click.Path(exists=True))
@click.option("--role", default=None, help="Default role assignment for documents")
@click.option("--pattern", default="**/*", help="File glob pattern")
def ingest(path: str, role: str | None, pattern: str) -> None:
    """Ingest documents from a file or directory."""
    from rfr.cli.client import RfrClient, RfrClientError
    from rfr.config import AppConfig

    client = RfrClient()
    console.print(f"[bold]Ingesting documents from {path}...[/bold]")

    try:
        if os.path.isdir(path):
            response = client.ingest_directory(
                path=path,
                default_role=role or AppConfig().ingestion.default_role,
                glob_pattern=pattern,
            )
        else:
            response = client.ingest_file(
                path=path,
                allowed_roles=[role] if role else None,
            )

        console.print(f"[green]Ingestion queued (task: {response.task_id})[/green]")
        console.print(f"Status: {response.status}")

        # Poll for completion
        import time

        with console.status("[bold]Processing...[/bold]"):
            while True:
                status = client.get_ingestion_status(response.task_id)
                if status.status in ("completed", "failed"):
                    break
                time.sleep(2)

        if status.status == "completed" and status.result:
            r = status.result
            console.print("[green]Ingestion complete:[/green]")
            console.print(f"  Added: {r.get('num_added', 0)}")
            console.print(f"  Updated: {r.get('num_updated', 0)}")
            console.print(f"  Skipped: {r.get('num_skipped', 0)}")
        elif status.status == "failed":
            console.print(f"[red]Ingestion failed: {status.error_message}[/red]")

    except RfrClientError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("question", nargs=-1, required=True)
@click.option("--role", default=None, help="Override role for this query")
@click.option("--top-k", default=3, help="Number of documents to retrieve")
@click.option("--no-llm", is_flag=True, help="Return retrieved docs only")
def query(question: tuple[str, ...], role: str | None, top_k: int, no_llm: bool) -> None:
    """Ask a question against your indexed documents."""
    from rfr.cli.client import RfrClient, RfrClientError

    q = " ".join(question)
    client = RfrClient()

    try:
        with console.status("[bold]Querying...[/bold]"):
            result = client.query(q, top_k=top_k)

        console.print()

        if no_llm:
            console.print("[bold]Retrieved documents:[/bold]")
            for i, source in enumerate(result.sources, 1):
                console.print(f"\n[cyan][{i}][/cyan] {source.content[:200]}...")
        else:
            console.print(result.answer)
            console.print()

        if result.sources:
            console.print("[dim]Sources:[/dim]")
            for source in result.sources:
                src = source.metadata.get("source", "unknown")
                score = source.relevance_score
                console.print(f"  [dim]📄 {src} (score: {score:.2f})[/dim]")

        if result.token_usage.total_tokens > 0:
            console.print(
                f"\n[dim]Response: {result.latency_ms:.0f}ms | "
                f"Tokens: {result.token_usage.total_tokens}[/dim]"
            )

    except RfrClientError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


@cli.group()
def keys() -> None:
    """Manage API keys."""


@keys.command(name="create")
@click.argument("name")
@click.option("--role", default="user", help="Role for this key")
def keys_create(name: str, role: str) -> None:
    """Create a new API key."""
    from rfr.cli.client import RfrClient, RfrClientError

    client = RfrClient()
    try:
        result = client.create_key(name, role)
        console.print("[bold]API Key Created[/bold]")
        console.print(f"  Name:   {result.name}")
        console.print(f"  Role:   {result.role}")
        console.print(f"  Prefix: {result.key_prefix}")
        console.print("\n[bold yellow]Raw Key:[/bold yellow]")
        console.print(f"[bold]{result.key}[/bold]")
        console.print(
            "\n[dim]⚠ This is the only time the raw key is shown. Store it securely.[/dim]"
        )
    except RfrClientError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


@keys.command(name="list")
def keys_list() -> None:
    """List all API keys."""
    from rfr.cli.client import RfrClient, RfrClientError

    client = RfrClient()
    try:
        result = client.list_keys()
        if not result.keys:
            console.print("No API keys found. Create one with 'rfr keys create <name>'")
            return
        table = Table(title="API Keys")
        table.add_column("Prefix")
        table.add_column("Name")
        table.add_column("Role")
        table.add_column("Active")
        table.add_column("Created")
        table.add_column("Last Used")
        for key in result.keys:
            table.add_row(
                key.prefix,
                key.name,
                key.role,
                "[green]✓[/green]" if key.is_active else "[red]✗[/red]",
                key.created_at.strftime("%Y-%m-%d") if key.created_at else "-",
                key.last_used_at.strftime("%Y-%m-%d %H:%M") if key.last_used_at else "-",
            )
        console.print(table)
    except RfrClientError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


@keys.command(name="revoke")
@click.argument("prefix")
def keys_revoke(prefix: str) -> None:
    """Revoke an API key by its prefix."""
    from rfr.cli.client import RfrClient, RfrClientError

    client = RfrClient()
    try:
        result = client.revoke_key(prefix)
        if result.deactivated:
            console.print(f"[green]Key '{prefix}' deactivated.[/green]")
    except RfrClientError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


@cli.group()
def docs() -> None:
    """Manage indexed documents."""


@docs.command(name="list")
def docs_list() -> None:
    """List indexed documents."""
    from rfr.cli.client import RfrClient, RfrClientError

    client = RfrClient()
    try:
        result = client.list_documents()
        if not result.items:
            console.print("No documents indexed. Run 'rfr ingest <path>' to add documents.")
            return
        table = Table(title="Indexed Documents")
        table.add_column("Doc ID")
        table.add_column("Source")
        table.add_column("Chunks")
        table.add_column("Roles")
        for doc in result.items:
            roles = ", ".join(doc.allowed_roles) if doc.allowed_roles else "-"
            table.add_row(doc.doc_id, doc.source, str(doc.chunk_count), roles)
        console.print(table)
    except RfrClientError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


@docs.command(name="delete")
@click.argument("doc_id")
def docs_delete(doc_id: str) -> None:
    """Delete a document by its doc_id."""
    from rfr.cli.client import RfrClient, RfrClientError

    client = RfrClient()
    try:
        result = client.delete_document(doc_id)
        if result.deleted:
            console.print(
                f"[green]Document '{doc_id}' deleted ({result.chunks_removed} chunks).[/green]"
            )
    except RfrClientError as e:
        console.print(f"[red]{e}[/red]")
        sys.exit(1)


@cli.command()
@click.option("--port", default=8000, help="Server port")
def standalone(port: int) -> None:
    """Run the API server without Docker (standalone mode)."""
    from rfr.config import AppConfig

    cfg = AppConfig()
    cfg.server.port = port

    console.print(f"[bold]Starting standalone server on port {port}...[/bold]")
    console.print("[dim]Database: SQLite (in-memory, data not persisted)[/dim]")
    console.print("[dim]LLM: Mock mode (no external inference)[/dim]")
    console.print(f"[dim]API docs: http://localhost:{port}/docs[/dim]")

    import uvicorn

    try:
        uvicorn.run(
            "rfr.api.app:create_app",
            host=cfg.server.host,
            port=port,
            log_level=cfg.server.log_level.lower(),
        )
    except KeyboardInterrupt:
        console.print("\nServer stopped.")


@cli.command()
@click.argument("service", required=False, default=None)
@click.option("-f", "--follow", is_flag=True, help="Follow log output")
def logs(service: str | None, follow: bool) -> None:
    """Tail Docker service logs."""
    compose_file = Path.cwd() / "docker-compose.yml"
    if not compose_file.exists():
        console.print("[red]No docker-compose.yml found.[/red]")
        sys.exit(1)

    cmd = ["docker", "compose", "-f", str(compose_file), "logs"]
    if follow:
        cmd.append("-f")
    if service:
        cmd.append(service)

    try:
        subprocess.run(cmd, check=True)  # noqa: S603
    except subprocess.CalledProcessError as e:
        console.print(f"[red]Failed to get logs: {e}[/red]")
        sys.exit(1)


@cli.command()
def tui() -> None:
    """Launch the terminal user interface."""
    console.print("[bold]Launching TUI...[/bold]")
    try:
        from rfr.cli.tui_app import RFRTuiApp  # type: ignore[import-untyped]

        app = RFRTuiApp()
        app.run()
    except ImportError:
        console.print(
            "[yellow]TUI dependencies not installed. Run: "
            "pip install 'ring-fenced-rag[tui]'[/yellow]"
        )
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    cli()
