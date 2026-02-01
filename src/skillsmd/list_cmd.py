"""List command implementation for the skillsmd CLI."""

import io
import sys
from pathlib import Path

from rich.console import Console
from rich.table import Table

from .agents import get_agents
from .installer import list_installed_skills


def _setup_utf8_encoding() -> None:
    """Ensure UTF-8 encoding for stdout/stderr on Windows."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "buffer") and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer") and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


_setup_utf8_encoding()

console = Console()


def _shorten_path(full_path: str, cwd: str) -> str:
    """Shortens a path for display: replaces homedir with ~ and cwd with ."""
    home = str(Path.home())
    if full_path.startswith(home):
        return "~" + full_path[len(home) :]
    if full_path.startswith(cwd):
        return "." + full_path[len(cwd) :]
    return full_path


def _format_list(items: list[str], max_show: int = 5) -> str:
    """Formats a list of items, truncating if too many."""
    if len(items) <= max_show:
        return ", ".join(items)
    shown = items[:max_show]
    remaining = len(items) - max_show
    return f"{', '.join(shown)} +{remaining} more"


async def run_list(
    is_global: bool = False,
    agent_filter: list[str] | None = None,
) -> None:
    """Run the list command."""
    agents = get_agents()
    cwd = str(Path.cwd())

    # Validate agent filter
    if agent_filter:
        valid_agents = list(agents.keys())
        invalid = [a for a in agent_filter if a not in valid_agents]
        if invalid:
            console.print(f"[yellow]Invalid agents: {', '.join(invalid)}[/yellow]")
            console.print(f"[dim]Valid agents: {', '.join(valid_agents)}[/dim]")
            return

    installed_skills = await list_installed_skills(
        is_global=is_global,
        cwd=cwd,
        agent_filter=agent_filter,
    )

    scope_label = "Global" if is_global else "Project"

    if not installed_skills:
        console.print(f"[dim]No {scope_label.lower()} skills found.[/dim]")
        if is_global:
            console.print("[dim]Try listing project skills without -g[/dim]")
        else:
            console.print("[dim]Try listing global skills with -g[/dim]")
        return

    console.print(f"[bold]{scope_label} Skills[/bold]\n")

    for skill in installed_skills:
        short_path = _shorten_path(skill.canonical_path, cwd)
        agent_names = [agents[a].display_name for a in skill.agents]
        agent_info = _format_list(agent_names) if skill.agents else "[yellow]not linked[/yellow]"

        console.print(f"[cyan]{skill.name}[/cyan] [dim]{short_path}[/dim]")
        console.print(f"  [dim]Agents:[/dim] {agent_info}")

    console.print()
