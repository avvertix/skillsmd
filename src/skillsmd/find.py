"""Find/search command implementation for the skillsmd CLI."""

import sys
from dataclasses import dataclass

import httpx
from rich.console import Console
from rich.prompt import Prompt

# API endpoint for skills search
SEARCH_API_BASE = 'https://skills.sh'


@dataclass
class SearchSkill:
    """A skill from the search API."""

    name: str
    slug: str
    source: str
    installs: int


console = Console()


async def search_skills_api(query: str, limit: int = 10) -> list[SearchSkill]:
    """Search for skills via the skills.sh API."""
    try:
        url = f'{SEARCH_API_BASE}/api/search'
        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                params={'q': query, 'limit': limit},
                timeout=30.0,
            )

            if response.status_code != 200:
                return []

            data = response.json()
            skills = []
            for skill in data.get('skills', []):
                skills.append(
                    SearchSkill(
                        name=skill.get('name', ''),
                        slug=skill.get('id', ''),
                        source=skill.get('topSource') or '',
                        installs=skill.get('installs', 0),
                    )
                )
            return skills
    except (httpx.RequestError, ValueError):
        return []


def _get_owner_repo_from_string(pkg: str) -> dict[str, str] | None:
    """Parse owner/repo from a package string."""
    # Handle owner/repo or owner/repo@skill
    at_index = pkg.rfind('@')
    repo_path = pkg[:at_index] if at_index > 0 else pkg

    parts = repo_path.split('/')
    if len(parts) == 2:
        return {'owner': parts[0], 'repo': parts[1]}
    return None


async def run_interactive_search(initial_query: str = '') -> SearchSkill | None:
    """
    Run an interactive search prompt.

    This is a simplified version that doesn't use raw terminal mode
    (which is complex in Python). Instead, it uses a simple input loop.
    """
    query = initial_query
    results: list[SearchSkill] = []
    selected_index = 0

    def render() -> None:
        """Render the search results."""
        console.print()
        console.print(f'[bold]Search skills:[/bold] {query}')
        console.print()

        if not query or len(query) < 2:
            console.print('[dim]Start typing to search (min 2 chars)[/dim]')
        elif not results:
            console.print('[dim]No skills found[/dim]')
        else:
            max_visible = 8
            visible = results[:max_visible]

            for i, skill in enumerate(visible):
                is_selected = i == selected_index
                arrow = '[bold]>[/bold]' if is_selected else ' '
                name = (
                    f'[bold]{skill.name}[/bold]'
                    if is_selected
                    else f'[grey78]{skill.name}[/grey78]'
                )
                source = f' [dim]{skill.source}[/dim]' if skill.source else ''
                console.print(f'  {arrow} {name}{source}')

        console.print()
        console.print(
            '[dim]Enter number to select, "q" to quit, or new query to search[/dim]'
        )

    # Initial search if query provided
    if query and len(query) >= 2:
        with console.status('[bold blue]Searching...'):
            results = await search_skills_api(query)

    render()

    while True:
        try:
            user_input = Prompt.ask('>', default='').strip()

            if not user_input:
                continue

            if user_input.lower() == 'q':
                return None

            # Try to parse as a number (selection)
            try:
                idx = int(user_input) - 1
                if 0 <= idx < len(results):
                    return results[idx]
                else:
                    console.print('[red]Invalid selection[/red]')
                    continue
            except ValueError:
                pass

            # Treat as a new search query
            query = user_input
            if len(query) >= 2:
                with console.status('[bold blue]Searching...'):
                    results = await search_skills_api(query)
                selected_index = 0
                render()
            else:
                console.print('[dim]Query must be at least 2 characters[/dim]')

        except (KeyboardInterrupt, EOFError):
            return None


async def run_find(query: str | None = None) -> None:
    """Run the find command."""
    is_non_interactive = not sys.stdin.isatty()

    # Non-interactive mode with query: just print results
    if query:
        with console.status('[bold blue]Searching...'):
            results = await search_skills_api(query)

        if not results:
            console.print(f'[dim]No skills found for "{query}"[/dim]')
            return

        console.print('[dim]Install with[/dim] skillsmd add <owner/repo@skill>')
        console.print()

        for skill in results[:6]:
            pkg = skill.source or skill.slug
            console.print(f'[grey78]{pkg}@{skill.name}[/grey78]')
            console.print(f'[dim]└ https://skills.sh/{pkg}/{skill.slug}[/dim]')
            console.print()
        return

    # Interactive mode
    if is_non_interactive:
        console.print(
            '[dim]Tip: if running in a coding agent, follow these steps:[/dim]'
        )
        console.print('[dim]  1) skillsmd find [query][/dim]')
        console.print('[dim]  2) skillsmd add <owner/repo@skill>[/dim]')
        console.print()

    selected = await run_interactive_search()

    if not selected:
        console.print('[dim]Search cancelled[/dim]')
        console.print()
        return

    # Build install command info
    pkg = selected.source or selected.slug
    skill_name = selected.name

    console.print()
    console.print(
        f'[grey78]Installing [bold]{skill_name}[/bold] from [dim]{pkg}[/dim]...[/grey78]'
    )
    console.print()

    # Import here to avoid circular imports
    from skillsmd.add import run_add

    await run_add(
        source=pkg,
        skill_names=[skill_name],
        is_global=False,
        yes=False,
    )

    console.print()

    # Show link to skill page
    info = _get_owner_repo_from_string(pkg)
    if info:
        console.print(
            f'[dim]View the skill at[/dim] [grey78]https://skills.sh/{info["owner"]}/{info["repo"]}/{selected.slug}[/grey78]'
        )
    else:
        console.print(
            '[dim]Discover more skills at[/dim] [grey78]https://skills.sh[/grey78]'
        )

    console.print()
