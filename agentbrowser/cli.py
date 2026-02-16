"""CLI interface for agentbrowser using Click + Rich."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .agent import BrowserAgent

console = Console()

# Shared state for CLI session (file-based for cross-command persistence)
_SESSION_FILE = Path.home() / ".agentbrowser" / ".cli_session"


def _get_session_url() -> str | None:
    """Get the current session URL (for chained commands)."""
    if _SESSION_FILE.exists():
        return _SESSION_FILE.read_text().strip() or None
    return None


def _save_session_url(url: str) -> None:
    _SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    _SESSION_FILE.write_text(url)


def _run(coro):
    """Run an async coroutine."""
    return asyncio.get_event_loop().run_until_complete(coro)


async def _agent_context(profile: str | None = None, headless: bool = True):
    """Create a BrowserAgent for CLI use."""
    return BrowserAgent(headless=headless, profile=profile)


@click.group()
@click.version_option(version="0.1.0", prog_name="agentbrowser")
def cli() -> None:
    """🤖 agentbrowser — Give your AI agents a real browser.

    Navigate, click, type, extract, and screenshot web pages
    with a simple command-line interface.
    """


@cli.command()
@click.argument("url")
@click.option("--profile", "-p", default=None, help="Browser profile to use.")
@click.option("--headed", is_flag=True, help="Run with visible browser window.")
def goto(url: str, profile: str | None, headed: bool) -> None:
    """Navigate to a URL and print page summary."""

    async def _run_goto():
        async with BrowserAgent(headless=not headed, profile=profile) as agent:
            await agent.goto(url)
            _save_session_url(url)
            summary = await agent.page_summary()
            console.print(Panel(summary, title="📄 Page Summary", border_style="blue"))

    asyncio.run(_run_goto())


@cli.command()
@click.argument("query")
@click.option("--url", default=None, help="URL to navigate to first.")
@click.option("--profile", "-p", default=None, help="Browser profile to use.")
def click_cmd(query: str, url: str | None, profile: str | None) -> None:
    """Click an element by text, label, or selector."""

    async def _run_click():
        async with BrowserAgent(headless=True, profile=profile) as agent:
            target = url or _get_session_url()
            if target:
                await agent.goto(target)
            await agent.click(query)
            console.print(f"✅ Clicked: [bold]{query}[/bold]")
            summary = await agent.page_summary()
            console.print(Panel(summary, title="📄 After Click", border_style="green"))

    asyncio.run(_run_click())


# Register as 'click' (avoid shadowing Python builtin in code)
click_cmd.name = "click"


@cli.command("type")
@click.argument("query")
@click.argument("text")
@click.option("--url", default=None, help="URL to navigate to first.")
@click.option("--submit", is_flag=True, help="Press Enter after typing.")
@click.option("--profile", "-p", default=None, help="Browser profile to use.")
def type_cmd(query: str, text: str, url: str | None, submit: bool, profile: str | None) -> None:
    """Type text into an element (found by label/placeholder/selector)."""

    async def _run_type():
        async with BrowserAgent(headless=True, profile=profile) as agent:
            target = url or _get_session_url()
            if target:
                await agent.goto(target)
            await agent.type(query, text, submit=submit)
            console.print(f"✅ Typed into [bold]{query}[/bold]: {text}")

    asyncio.run(_run_type())


@cli.command()
@click.argument("output", default="screenshot.png")
@click.option("--url", default=None, help="URL to navigate to first.")
@click.option("--full-page", is_flag=True, help="Capture full scrollable page.")
@click.option("--profile", "-p", default=None, help="Browser profile to use.")
def screenshot(output: str, url: str | None, full_page: bool, profile: str | None) -> None:
    """Take a screenshot and save to file."""

    async def _run_screenshot():
        async with BrowserAgent(headless=True, profile=profile) as agent:
            target = url or _get_session_url()
            if target:
                await agent.goto(target)
            await agent.screenshot(output, full_page=full_page)
            console.print(f"📸 Screenshot saved to [bold]{output}[/bold]")

    asyncio.run(_run_screenshot())


@cli.command()
@click.option("--url", default=None, help="URL to navigate to first.")
@click.option("--format", "fmt", type=click.Choice(["text", "json", "links"]), default="text")
@click.option("--profile", "-p", default=None, help="Browser profile to use.")
def extract(url: str | None, fmt: str, profile: str | None) -> None:
    """Extract content from the page."""

    async def _run_extract():
        async with BrowserAgent(headless=True, profile=profile) as agent:
            target = url or _get_session_url()
            if target:
                await agent.goto(target)

            if fmt == "text":
                text = await agent.get_text()
                console.print(text)
            elif fmt == "links":
                links = await agent.get_links()
                table = Table(title="Links")
                table.add_column("Text", style="cyan")
                table.add_column("URL", style="blue")
                for link in links[:50]:
                    table.add_row(link.text[:60], link.href[:80])
                console.print(table)
            elif fmt == "json":
                meta = await agent.get_meta()
                links = await agent.get_links()
                data = {
                    "meta": meta,
                    "links": [{"text": l.text, "href": l.href} for l in links],
                }
                click.echo(json.dumps(data, indent=2))

    asyncio.run(_run_extract())


@cli.command()
@click.option("--url", default=None, help="URL to navigate to first.")
@click.option("--profile", "-p", default=None, help="Browser profile to use.")
def summary(url: str | None, profile: str | None) -> None:
    """Get an LLM-friendly page summary."""

    async def _run_summary():
        async with BrowserAgent(headless=True, profile=profile) as agent:
            target = url or _get_session_url()
            if target:
                await agent.goto(target)
            s = await agent.page_summary()
            console.print(Panel(s, title="🤖 Page Summary", border_style="cyan"))

    asyncio.run(_run_summary())


# --- Profile management ---

@cli.group()
def profile() -> None:
    """Manage browser profiles (cookies, sessions)."""


@profile.command("list")
def profile_list() -> None:
    """List saved profiles."""
    from .storage import Storage
    from .config import _default_data_dir

    storage = Storage(_default_data_dir() / "agentbrowser.db")
    profiles = storage.list_profiles()
    if not profiles:
        console.print("[dim]No profiles saved yet.[/dim]")
        return
    table = Table(title="Saved Profiles")
    table.add_column("Name", style="cyan")
    table.add_column("Created", style="green")
    table.add_column("Updated", style="yellow")
    for p in profiles:
        table.add_row(p["name"], p["created_at"][:19], p["updated_at"][:19])
    console.print(table)
    storage.close()


@profile.command("create")
@click.argument("name")
@click.option("--url", default=None, help="Navigate to URL and save profile.")
def profile_create(name: str, url: str | None) -> None:
    """Create a new profile (optionally from a URL)."""

    async def _run():
        async with BrowserAgent(headless=True) as agent:
            if url:
                await agent.goto(url)
            await agent.save_profile(name)
            console.print(f"✅ Profile [bold]{name}[/bold] saved.")

    asyncio.run(_run())


@profile.command("delete")
@click.argument("name")
def profile_delete(name: str) -> None:
    """Delete a profile."""
    from .storage import Storage
    from .config import _default_data_dir

    storage = Storage(_default_data_dir() / "agentbrowser.db")
    if storage.delete_profile(name):
        console.print(f"🗑️  Profile [bold]{name}[/bold] deleted.")
    else:
        console.print(f"[red]Profile '{name}' not found.[/red]")
    storage.close()


# --- Recording ---

@cli.command("replay")
@click.argument("name")
@click.option("--profile", "-p", default=None, help="Browser profile to use.")
@click.option("--headed", is_flag=True, help="Run with visible browser.")
def replay(name: str, profile: str | None, headed: bool) -> None:
    """Replay a saved recording."""

    async def _run():
        async with BrowserAgent(headless=not headed, profile=profile) as agent:
            await agent.replay(name)
            console.print(f"✅ Replay of [bold]{name}[/bold] complete.")

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
