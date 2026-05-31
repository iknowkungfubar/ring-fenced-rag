"""Terminal User Interface for Ring-Fenced RAG.

A Textual-based TUI providing query interface, health monitoring,
and document management — all without leaving the terminal.

Usage:
    rfr tui

    # Or directly:
    python -m rfr.cli.tui_app

Requires: pip install 'ring-fenced-rag[tui]'
"""

from __future__ import annotations

import logging
from typing import Any

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Header,
    Input,
    Label,
    RichLog,
)

logger = logging.getLogger(__name__)


def _get_client() -> Any:
    """Get an API client (handles connection errors gracefully)."""
    from rfr.cli.client import RfrClient

    return RfrClient()


# ── Query Screen (main) ──


class QueryScreen(Screen):
    """Main query interface — ask questions, see answers with sources."""

    BINDINGS = [
        Binding("/", "focus_input", "Query"),
        Binding("s", "show_status", "Status"),
        Binding("q", "quit", "Quit"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("Ring-Fenced RAG — Ask a question", id="title")
        yield Input(placeholder="How do I restart Nginx?", id="query-input")
        yield RichLog(id="result-display", highlight=True, markup=True)
        yield Footer()

    def on_mount(self) -> None:
        """Focus the input on startup."""
        self.query_one("#query-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle query submission."""
        if event.value.strip():
            self.run_query(event.value.strip())

    @work(thread=False, exclusive=True)
    async def run_query(self, question: str) -> None:
        """Execute a query and display results."""
        display = self.query_one("#result-display", RichLog)
        display.clear()
        display.write(f"[bold cyan]Query:[/bold cyan] {question}\n")
        display.write("[dim]Searching...[/dim]\n")

        try:
            client = _get_client()
            result = client.query(question)
            display.clear()
            display.write(f"[bold cyan]Query:[/bold cyan] {question}\n")
            display.write("")

            # Answer
            display.write(f"[bold]Answer:[/bold]\n{result.answer}\n")

            # Sources
            if result.sources:
                display.write("[bold]Sources:[/bold]")
                for s in result.sources:
                    src = s.metadata.get("source", "unknown") if s.metadata else "unknown"
                    score = s.relevance_score
                    display.write(f"  [dim]📄 {src} ({(score * 100):.0f}%)[/dim]")

            # Meta
            display.write(
                f"\n[dim]Latency: {result.latency_ms:.0f}ms | Tokens: {result.token_usage.total_tokens}[/dim]"
            )

        except Exception as e:  # noqa: BLE001
            display.write(f"\n[bold red]Error:[/bold red] {e}")

    def action_focus_input(self) -> None:
        """Focus the query input."""
        self.query_one("#query-input", Input).focus()

    def action_show_status(self) -> None:
        """Switch to status screen."""
        self.app.push_screen(StatusScreen())


# ── Status Screen ──


class StatusScreen(Screen):
    """Display component health and system info."""

    BINDINGS = [
        Binding("q", "pop_screen", "Back"),
        Binding("escape", "pop_screen", "Back"),
        Binding("r", "refresh", "Refresh"),
    ]

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Label("System Status", id="title")
        yield RichLog(id="status-display", highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        """Load status on mount."""
        self.load_status()

    @work(thread=False, exclusive=True)
    async def load_status(self) -> None:
        """Fetch and display health information."""
        display = self.query_one("#status-display", RichLog)
        display.clear()
        display.write("[bold cyan]Loading status...[/bold cyan]")

        try:
            client = _get_client()
            health = client.health()

            display.clear()
            display.write("[bold]System Health[/bold]\n")

            # Version info
            from rfr.__about__ import version_info

            info = version_info()
            display.write(f"  Version:    {info['version']}")
            display.write(f"  Git commit: {info['git_commit']}")
            display.write(f"  Python:     {info['python']}")
            display.write(f"  Platform:   {info['platform']}")
            display.write("")

            # Components
            display.write("[bold]Components[/bold]")
            status_icons: dict[str, str] = {
                "connected": "✅",
                "configured": "⚙️",
                "disconnected": "❌",
                "not_configured": "⬜",
            }
            for component, status_val in health.components.items():
                icon = status_icons.get(status_val, "❓")
                display.write(f"  {icon} {component.capitalize()}: {status_val}")

            display.write(f"\n[dim]Uptime: {health.uptime_seconds:.0f}s[/dim]")

            # Keys
            try:
                keys = client.list_keys()
                display.write(f"\n[bold]API Keys:[/bold] {len(keys.keys)} active")
            except Exception:  # noqa: BLE001
                display.write("\n[dim]API keys: unable to fetch[/dim]")

        except Exception as e:  # noqa: BLE001
            display.clear()
            display.write(f"[bold red]Error fetching status:[/bold red] {e}")
            display.write(
                "\nIs the server running? Try [bold]rfr up[/bold] or [bold]rfr standalone[/bold]"
            )

    def action_refresh(self) -> None:
        """Refresh the status display."""
        self.load_status()


# ── Main Application ──


class RFRTuiApp(App):
    """Ring-Fenced RAG Terminal User Interface."""

    TITLE = "Ring-Fenced RAG"
    SUB_TITLE = "Secure Document Q&A"
    CSS = """
    Screen {
        background: #0f1117;
    }

    #title {
        padding: 1;
        text-style: bold;
        color: #4f8cff;
    }

    Input {
        margin: 0 1;
        background: #1a1d27;
        color: #e4e6ed;
        border: solid #2e3144;
    }

    Input:focus {
        border: solid #4f8cff;
    }

    RichLog {
        margin: 1;
        padding: 1;
        background: #1a1d27;
        color: #e4e6ed;
        border: solid #2e3144;
        height: 1fr;
    }

    Footer {
        background: #1a1d27;
        color: #8b8fa3;
    }

    Header {
        background: #252836;
        color: #e4e6ed;
    }
    """

    def on_mount(self) -> None:
        """Push the main query screen."""
        self.push_screen(QueryScreen())


def main() -> None:
    """Entry point for the TUI."""
    app = RFRTuiApp()
    app.run()


if __name__ == "__main__":
    main()
