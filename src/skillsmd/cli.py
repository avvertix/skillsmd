"""CLI implementation for the skillsmd package."""

import asyncio
import io
import sys
from typing import Annotated, Optional

import typer
from rich.console import Console

from skillsmd import __version__
from skillsmd.add import run_add
from skillsmd.init import run_init
from skillsmd.list_cmd import run_list
from skillsmd.remove import run_remove


def _setup_utf8_encoding() -> None:
    """Ensure UTF-8 encoding for stdout/stderr on Windows."""
    if (
        sys.platform == 'win32'
    ):  # TODO: Check when running Pytest on Windows as creates errors
        # Reconfigure stdout and stderr to use UTF-8
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding='utf-8', errors='replace'
            )
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding='utf-8', errors='replace'
            )


# Set up UTF-8 encoding before creating Console
_setup_utf8_encoding()

console = Console()

app = typer.Typer(
    name='skillsmd',
    help='The open agent skills ecosystem - Python CLI',
    add_completion=False,
    no_args_is_help=False,
)

# ASCII-safe logo for Windows compatibility
LOGO_ASCII = [
    ' ____  _  __ ___ _     _     ____  ',
    '/ ___|| |/ /|_ _| |   | |   / ___| ',
    "\\___ \\| ' /  | || |   | |   \\___ \\ ",
    ' ___) | . \\  | || |___| |___ ___) |',
    '|____/|_|\\_\\|___|_____|_____|____/ ',
]

# Unicode logo (for terminals that support it)
LOGO_UNICODE = [
    '███████╗██╗  ██╗██╗██╗     ██╗     ███████╗',
    '██╔════╝██║ ██╔╝██║██║     ██║     ██╔════╝',
    '███████╗█████╔╝ ██║██║     ██║     ███████╗',
    '╚════██║██╔═██╗ ██║██║     ██║     ╚════██║',
    '███████║██║  ██╗██║███████╗███████╗███████║',
    '╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚══════╝',
]

# Rich styles for the gradient
GRAY_STYLES = [
    'grey78',  # lighter gray
    'grey74',
    'grey66',  # mid gray
    'grey58',
    'grey50',
    'grey42',  # darker gray
]


def _can_use_unicode() -> bool:
    """Check if the terminal supports Unicode."""
    try:
        # Try to encode a box-drawing character
        '█'.encode(sys.stdout.encoding or 'utf-8')
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def show_logo() -> None:
    """Display the ASCII art logo."""
    logo_lines = LOGO_UNICODE if _can_use_unicode() else LOGO_ASCII
    console.print()
    for i, line in enumerate(logo_lines):
        style_idx = min(i, len(GRAY_STYLES) - 1)
        console.print(f'[{GRAY_STYLES[style_idx]}]{line}[/{GRAY_STYLES[style_idx]}]')


def show_banner() -> None:
    """Display the banner with usage information."""
    show_logo()
    console.print()
    console.print('[dim]The open agent skills ecosystem[/dim]')
    console.print()
    console.print(
        '  [dim]$[/dim] [grey78]skillsmd add [dim]<package>[/dim][/grey78]   [dim]Install a skill[/dim]'
    )
    console.print(
        '  [dim]$[/dim] [grey78]skillsmd list[/grey78]            [dim]List installed skills[/dim]'
    )
    console.print(
        '  [dim]$[/dim] [grey78]skillsmd find [dim][query][/dim][/grey78]    [dim]Search for skills[/dim]'
    )
    console.print(
        '  [dim]$[/dim] [grey78]skillsmd check[/grey78]           [dim]Check for updates[/dim]'
    )
    console.print(
        '  [dim]$[/dim] [grey78]skillsmd update[/grey78]          [dim]Update all skills[/dim]'
    )
    console.print(
        '  [dim]$[/dim] [grey78]skillsmd remove[/grey78]          [dim]Remove installed skills[/dim]'
    )
    console.print(
        '  [dim]$[/dim] [grey78]skillsmd init [dim][name][/dim][/grey78]     [dim]Create a new skill[/dim]'
    )
    console.print()
    console.print('[dim]try:[/dim] skillsmd add vercel-labs/agent-skills')
    console.print()
    console.print('Discover more skills at [cyan]https://skills.sh/[/cyan]')
    console.print()


@app.callback(invoke_without_command=True)
def main_callback(
    ctx: typer.Context,
    version: Annotated[
        bool,
        typer.Option('--version', '-v', help='Show version number'),
    ] = False,
) -> None:
    """The open agent skills ecosystem."""
    if version:
        console.print(__version__)
        raise typer.Exit()

    if ctx.invoked_subcommand is None:
        show_banner()


@app.command('add')
def add_command(
    source: Annotated[
        str, typer.Argument(help='Source to install (owner/repo, URL, or local path)')
    ],
    global_install: Annotated[
        bool,
        typer.Option('--global', '-g', help='Install skill globally'),
    ] = False,
    agent: Annotated[
        Optional[list[str]],
        typer.Option('--agent', '-a', help="Target specific agents (use '*' for all)"),
    ] = None,
    skill: Annotated[
        Optional[list[str]],
        typer.Option('--skill', '-s', help="Install specific skills (use '*' for all)"),
    ] = None,
    list_only: Annotated[
        bool,
        typer.Option('--list', '-l', help='List available skills without installing'),
    ] = False,
    yes: Annotated[
        bool,
        typer.Option('--yes', '-y', help='Skip confirmation prompts'),
    ] = False,
    all_mode: Annotated[
        bool,
        typer.Option('--all', help="Shorthand for --skill '*' --agent '*' -y"),
    ] = False,
    full_depth: Annotated[
        bool,
        typer.Option('--full-depth', help='Search all subdirectories'),
    ] = False,
) -> None:
    """Add a skill package."""
    show_logo()
    asyncio.run(
        run_add(
            source=source,
            is_global=global_install,
            agent_names=agent,
            skill_names=skill,
            list_only=list_only,
            yes=yes,
            all_mode=all_mode,
            full_depth=full_depth,
        )
    )


@app.command('remove')
@app.command('rm', hidden=True)
def remove_command(
    skills: Annotated[
        Optional[list[str]],
        typer.Argument(help='Skill names to remove'),
    ] = None,
    global_install: Annotated[
        bool,
        typer.Option('--global', '-g', help='Remove from global scope'),
    ] = False,
    agent: Annotated[
        Optional[list[str]],
        typer.Option('--agent', '-a', help='Remove from specific agents'),
    ] = None,
    yes: Annotated[
        bool,
        typer.Option('--yes', '-y', help='Skip confirmation prompts'),
    ] = False,
    all_mode: Annotated[
        bool,
        typer.Option('--all', help='Remove all skills'),
    ] = False,
) -> None:
    """Remove installed skills."""
    asyncio.run(
        run_remove(
            skill_names=skills,
            is_global=global_install,
            agent_names=agent,
            yes=yes,
            all_mode=all_mode,
        )
    )


@app.command('list')
@app.command('ls', hidden=True)
def list_command(
    global_install: Annotated[
        bool,
        typer.Option('--global', '-g', help='List global skills'),
    ] = False,
    agent: Annotated[
        Optional[list[str]],
        typer.Option('--agent', '-a', help='Filter by specific agents'),
    ] = None,
) -> None:
    """List installed skills."""
    asyncio.run(
        run_list(
            is_global=global_install,
            agent_filter=agent,
        )
    )


@app.command('init')
def init_command(
    name: Annotated[
        Optional[str],
        typer.Argument(help='Name for the new skill'),
    ] = None,
) -> None:
    """Initialize a new skill (creates SKILL.md)."""
    show_logo()
    console.print()
    run_init(name)


@app.command('find')
@app.command('search', hidden=True)
def find_command(
    query: Annotated[
        Optional[str],
        typer.Argument(help='Search query'),
    ] = None,
) -> None:
    """Search for skills."""
    show_logo()
    console.print()
    console.print('[yellow]Find command not yet implemented in Python port[/yellow]')
    console.print('[dim]Visit https://skills.sh/ to discover skills[/dim]')


@app.command('check')
def check_command() -> None:
    """Check for available skill updates."""
    console.print('[yellow]Check command not yet implemented in Python port[/yellow]')


@app.command('update')
@app.command('upgrade', hidden=True)
def update_command() -> None:
    """Update all skills to latest versions."""
    console.print('[yellow]Update command not yet implemented in Python port[/yellow]')


def main() -> None:
    """Entry point for the CLI."""
    app()
