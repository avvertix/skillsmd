"""CLI implementation for the skillsmd package."""

import asyncio
import io
import sys
from typing import Annotated, Optional

import typer
from rich.console import Console

from skillsmd import __version__
from skillsmd.add import run_add
from skillsmd.find import run_find
from skillsmd.init import run_init
from skillsmd.list_cmd import run_list
from skillsmd.remove import run_remove
from skillsmd.skill_lock import read_skill_lock


def _setup_utf8_encoding() -> None:
    """Ensure UTF-8 encoding for stdout/stderr on Windows."""
    if sys.platform == 'win32':
        # Don't reconfigure if running under pytest (breaks capture)
        if 'pytest' in sys.modules:
            return
        # Reconfigure stdout and stderr to use UTF-8
        if hasattr(sys.stdout, 'buffer'):
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding='utf-8', errors='replace'
            )
        if hasattr(sys.stderr, 'buffer'):
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding='utf-8', errors='replace'
            )


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
    asyncio.run(run_find(query))


@app.command('check')
def check_command() -> None:
    """Check for available skill updates."""
    asyncio.run(run_check())


@app.command('update')
@app.command('upgrade', hidden=True)
def update_command() -> None:
    """Update all skills to latest versions."""
    asyncio.run(run_update())


CHECK_UPDATES_API_URL = 'https://add-skill.vercel.sh/check-updates'


async def run_check() -> None:
    """Check for available skill updates."""
    import httpx

    console.print('[grey78]Checking for skill updates...[/grey78]')
    console.print()

    lock = await read_skill_lock()
    skill_names = list(lock.skills.keys())

    if not skill_names:
        console.print('[dim]No skills tracked in lock file.[/dim]')
        console.print(
            '[dim]Install skills with[/dim] [grey78]skillsmd add <package>[/grey78]'
        )
        return

    # Build check request - only include skills with folder hash
    check_skills = []
    for skill_name in skill_names:
        entry = lock.skills.get(skill_name)
        if entry and entry.skill_folder_hash:
            check_skills.append(
                {
                    'name': skill_name,
                    'source': entry.source,
                    'path': entry.skill_path,
                    'skillFolderHash': entry.skill_folder_hash,
                }
            )

    if not check_skills:
        console.print('[dim]No skills to check.[/dim]')
        return

    console.print(f'[dim]Checking {len(check_skills)} skill(s) for updates...[/dim]')

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                CHECK_UPDATES_API_URL,
                json={'skills': check_skills},
                headers={'Content-Type': 'application/json'},
                timeout=30.0,
            )

            if response.status_code != 200:
                console.print(
                    f'[red]API error: {response.status_code} {response.reason_phrase}[/red]'
                )
                raise typer.Exit(1)

            data = response.json()
            updates = data.get('updates', [])
            errors = data.get('errors', [])

            console.print()

            if not updates:
                console.print('[grey78]✓ All skills are up to date[/grey78]')
            else:
                console.print(f'[grey78]{len(updates)} update(s) available:[/grey78]')
                console.print()
                for update in updates:
                    console.print(f'  [grey78]↑[/grey78] {update["name"]}')
                    console.print(f'    [dim]source: {update["source"]}[/dim]')
                console.print()
                console.print(
                    '[dim]Run[/dim] [grey78]skillsmd update[/grey78] [dim]to update all skills[/dim]'
                )

            if errors:
                console.print()
                console.print(
                    f'[dim]Could not check {len(errors)} skill(s) (may need reinstall)[/dim]'
                )

    except httpx.RequestError as e:
        console.print(f'[red]Error checking for updates: {e}[/red]')
        raise typer.Exit(1)

    console.print()


async def run_update() -> None:
    """Update all skills to latest versions."""
    import httpx

    console.print('[grey78]Checking for skill updates...[/grey78]')
    console.print()

    lock = await read_skill_lock()
    skill_names = list(lock.skills.keys())

    if not skill_names:
        console.print('[dim]No skills tracked in lock file.[/dim]')
        console.print(
            '[dim]Install skills with[/dim] [grey78]skillsmd add <package>[/grey78]'
        )
        return

    # Build check request - only include skills with folder hash
    check_skills = []
    for skill_name in skill_names:
        entry = lock.skills.get(skill_name)
        if entry and entry.skill_folder_hash:
            check_skills.append(
                {
                    'name': skill_name,
                    'source': entry.source,
                    'path': entry.skill_path,
                    'skillFolderHash': entry.skill_folder_hash,
                }
            )

    if not check_skills:
        console.print('[dim]No skills to check.[/dim]')
        return

    updates = []
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                CHECK_UPDATES_API_URL,
                json={'skills': check_skills},
                headers={'Content-Type': 'application/json'},
                timeout=30.0,
            )

            if response.status_code != 200:
                console.print(
                    f'[red]API error: {response.status_code} {response.reason_phrase}[/red]'
                )
                raise typer.Exit(1)

            data = response.json()
            updates = data.get('updates', [])

    except httpx.RequestError as e:
        console.print(f'[red]Error checking for updates: {e}[/red]')
        raise typer.Exit(1)

    if not updates:
        console.print('[grey78]✓ All skills are up to date[/grey78]')
        console.print()
        return

    console.print(f'[grey78]Found {len(updates)} update(s)[/grey78]')
    console.print()

    # Reinstall each skill that has an update
    success_count = 0
    fail_count = 0

    for update in updates:
        skill_name = update['name']
        entry = lock.skills.get(skill_name)
        if not entry:
            continue

        console.print(f'[grey78]Updating {skill_name}...[/grey78]')

        try:
            # Use skillsmd to reinstall
            await run_add(
                source=entry.source_url,
                skill_names=[skill_name],
                is_global=True,
                yes=True,
            )
            success_count += 1
            console.print(f'  [grey78]✓[/grey78] Updated {skill_name}')
        except Exception:
            fail_count += 1
            console.print(f'  [dim]✗ Failed to update {skill_name}[/dim]')

    console.print()
    if success_count > 0:
        console.print(f'[grey78]✓ Updated {success_count} skill(s)[/grey78]')
    if fail_count > 0:
        console.print(f'[dim]Failed to update {fail_count} skill(s)[/dim]')
    console.print()


def main() -> None:
    """Entry point for the CLI."""
    _setup_utf8_encoding()
    app()
