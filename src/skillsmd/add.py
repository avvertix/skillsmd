"""Add command implementation for the skillsmd CLI."""

import asyncio
import io
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm
from rich.table import Table

from skillsmd.agents import get_agents, detect_installed_agents
from skillsmd.git import clone_repo, cleanup_temp_dir, GitCloneError
from skillsmd.installer import (
    get_canonical_path,
    install_remote_skill_for_agent,
    install_skill_for_agent,
    is_skill_installed,
)
from skillsmd.skills import discover_skills, filter_skills, get_skill_display_name
from skillsmd.source_parser import parse_source, get_owner_repo
from skillsmd.types import InstallMode, Skill, ALL_AGENT_TYPES


def _setup_utf8_encoding() -> None:
    """Ensure UTF-8 encoding for stdout/stderr on Windows."""
    if sys.platform == 'win32':
        if hasattr(sys.stdout, 'buffer') and not isinstance(
            sys.stdout, io.TextIOWrapper
        ):
            sys.stdout = io.TextIOWrapper(
                sys.stdout.buffer, encoding='utf-8', errors='replace'
            )
        if hasattr(sys.stderr, 'buffer') and not isinstance(
            sys.stderr, io.TextIOWrapper
        ):
            sys.stderr = io.TextIOWrapper(
                sys.stderr.buffer, encoding='utf-8', errors='replace'
            )


_setup_utf8_encoding()

console = Console()


def _shorten_path(full_path: str, cwd: str) -> str:
    """Shortens a path for display: replaces homedir with ~ and cwd with ."""
    home = str(Path.home())
    if full_path.startswith(home):
        return '~' + full_path[len(home) :]
    if full_path.startswith(cwd):
        return '.' + full_path[len(cwd) :]
    return full_path


def _format_list(items: list[str], max_show: int = 5) -> str:
    """Formats a list of items, truncating if too many."""
    if len(items) <= max_show:
        return ', '.join(items)
    shown = items[:max_show]
    remaining = len(items) - max_show
    return f'{", ".join(shown)} +{remaining} more'


async def _select_skills_interactive(
    skills: list[Skill],
) -> list[Skill] | None:
    """Interactively select skills to install."""
    console.print('\n[bold]Available Skills:[/bold]')
    for i, skill in enumerate(skills, 1):
        desc = (
            skill.description[:60] + '...'
            if len(skill.description) > 60
            else skill.description
        )
        console.print(f'  {i}. [cyan]{get_skill_display_name(skill)}[/cyan]')
        console.print(f'     [dim]{desc}[/dim]')

    console.print("\nEnter skill numbers (comma-separated) or 'all' for all skills:")
    user_input = console.input('> ').strip()

    if not user_input:
        return None

    if user_input.lower() == 'all':
        return skills

    try:
        indices = [int(x.strip()) - 1 for x in user_input.split(',')]
        return [skills[i] for i in indices if 0 <= i < len(skills)]
    except (ValueError, IndexError):
        console.print('[red]Invalid selection[/red]')
        return None


async def _select_agents_interactive(
    is_global: bool = False,
) -> list[str] | None:
    """Interactively select agents to install to."""
    agents = get_agents()
    agent_list = list(agents.values())

    console.print('\n[bold]Available Agents:[/bold]')
    for i, agent in enumerate(agent_list, 1):
        path = agent.global_skills_dir if is_global else agent.skills_dir
        console.print(f'  {i}. [cyan]{agent.display_name}[/cyan] [dim]({path})[/dim]')

    console.print("\nEnter agent numbers (comma-separated) or 'all' for all agents:")
    user_input = console.input('> ').strip()

    if not user_input:
        return None

    if user_input.lower() == 'all':
        return [a.name for a in agent_list]

    try:
        indices = [int(x.strip()) - 1 for x in user_input.split(',')]
        return [agent_list[i].name for i in indices if 0 <= i < len(agent_list)]
    except (ValueError, IndexError):
        console.print('[red]Invalid selection[/red]')
        return None


async def run_add(
    source: str,
    is_global: bool = False,
    agent_names: list[str] | None = None,
    skill_names: list[str] | None = None,
    list_only: bool = False,
    yes: bool = False,
    all_mode: bool = False,
    full_depth: bool = False,
) -> None:
    """Run the add command."""
    agents = get_agents()
    cwd = str(Path.cwd())
    temp_dir: str | None = None

    # --all implies --skill '*' and --agent '*' and -y
    if all_mode:
        skill_names = ['*']
        agent_names = ['*']
        yes = True

    try:
        with console.status('[bold blue]Parsing source...'):
            parsed = parse_source(source)

        source_info = parsed.local_path if parsed.type == 'local' else parsed.url
        if parsed.ref:
            source_info += f' @ [yellow]{parsed.ref}[/yellow]'
        if parsed.subpath:
            source_info += f' ({parsed.subpath})'
        if parsed.skill_filter:
            source_info += f' [dim]@[/dim][cyan]{parsed.skill_filter}[/cyan]'

        console.print(f'Source: {source_info}')

        # Handle different source types
        if parsed.type == 'direct-url':
            console.print(
                '[yellow]Direct URL skills not yet implemented in Python port[/yellow]'
            )
            return

        if parsed.type == 'well-known':
            console.print(
                '[yellow]Well-known skills not yet implemented in Python port[/yellow]'
            )
            return

        # Get skills directory
        if parsed.type == 'local':
            if not Path(parsed.local_path or '').exists():
                console.print(
                    f'[red]Local path does not exist: {parsed.local_path}[/red]'
                )
                return
            skills_dir = parsed.local_path or ''
        else:
            with console.status('[bold blue]Cloning repository...'):
                temp_dir = await clone_repo(parsed.url, parsed.ref)
            skills_dir = temp_dir

        # Merge skill filter from @skill syntax
        if parsed.skill_filter:
            skill_names = skill_names or []
            if parsed.skill_filter not in skill_names:
                skill_names.append(parsed.skill_filter)

        # Include internal skills when explicitly requested
        include_internal = bool(skill_names and len(skill_names) > 0)

        with console.status('[bold blue]Discovering skills...'):
            skills = await discover_skills(
                skills_dir,
                parsed.subpath,
                include_internal=include_internal,
                full_depth=full_depth,
            )

        if not skills:
            console.print(
                '[red]No valid skills found. Skills require a SKILL.md with name and description.[/red]'
            )
            return

        console.print(
            f'Found [green]{len(skills)}[/green] skill{"s" if len(skills) > 1 else ""}'
        )

        # List mode
        if list_only:
            console.print('\n[bold]Available Skills:[/bold]')
            for skill in skills:
                console.print(f'  [cyan]{get_skill_display_name(skill)}[/cyan]')
                console.print(f'    [dim]{skill.description}[/dim]')
            console.print('\nUse --skill <name> to install specific skills')
            return

        # Select skills
        selected_skills: list[Skill]

        if skill_names and '*' in skill_names:
            selected_skills = skills
            console.print(f'Installing all {len(skills)} skills')
        elif skill_names:
            selected_skills = filter_skills(skills, skill_names)
            if not selected_skills:
                console.print(
                    f'[red]No matching skills found for: {", ".join(skill_names)}[/red]'
                )
                console.print('Available skills:')
                for s in skills:
                    console.print(f'  - {get_skill_display_name(s)}')
                return
            skill_display = ', '.join(
                [f'[cyan]{get_skill_display_name(s)}[/cyan]' for s in selected_skills]
            )
            console.print(
                f'Selected {len(selected_skills)} skill{"s" if len(selected_skills) > 1 else ""}: {skill_display}'
            )
        elif len(skills) == 1:
            selected_skills = skills
            console.print(f'Skill: [cyan]{get_skill_display_name(skills[0])}[/cyan]')
            console.print(f'[dim]{skills[0].description}[/dim]')
        elif yes:
            selected_skills = skills
            console.print(f'Installing all {len(skills)} skills')
        else:
            result = await _select_skills_interactive(skills)
            if not result:
                console.print('[yellow]Installation cancelled[/yellow]')
                return
            selected_skills = result

        # Select agents
        target_agents: list[str]
        valid_agents = list(agents.keys())

        if agent_names and '*' in agent_names:
            target_agents = valid_agents
            console.print(f'Installing to all {len(target_agents)} agents')
        elif agent_names:
            invalid = [a for a in agent_names if a not in valid_agents]
            if invalid:
                console.print(f'[red]Invalid agents: {", ".join(invalid)}[/red]')
                console.print(f'[dim]Valid agents: {", ".join(valid_agents)}[/dim]')
                return
            target_agents = agent_names
        else:
            with console.status('[bold blue]Detecting installed agents...'):
                installed_agents = await detect_installed_agents()

            if not installed_agents:
                if yes:
                    target_agents = valid_agents
                    console.print('Installing to all agents')
                else:
                    result = await _select_agents_interactive(is_global)
                    if not result:
                        console.print('[yellow]Installation cancelled[/yellow]')
                        return
                    target_agents = result
            elif len(installed_agents) == 1 or yes:
                target_agents = installed_agents
                if len(installed_agents) == 1:
                    console.print(
                        f'Installing to: [cyan]{agents[installed_agents[0]].display_name}[/cyan]'
                    )
                else:
                    agent_display = ', '.join(
                        [
                            f'[cyan]{agents[a].display_name}[/cyan]'
                            for a in installed_agents
                        ]
                    )
                    console.print(f'Installing to: {agent_display}')
            else:
                result = await _select_agents_interactive(is_global)
                if not result:
                    console.print('[yellow]Installation cancelled[/yellow]')
                    return
                target_agents = result

        # Determine installation scope
        install_globally = is_global

        # Check if any selected agents support global installation
        supports_global = any(
            agents[a].global_skills_dir is not None for a in target_agents
        )

        if not is_global and not yes and supports_global:
            install_globally = Confirm.ask(
                'Install globally? (available across all projects)',
                default=False,
            )

        # Determine install mode
        install_mode: InstallMode = 'symlink'

        if not yes:
            use_copy = Confirm.ask(
                'Use copy mode? (creates independent copies for each agent)',
                default=False,
            )
            if use_copy:
                install_mode = 'copy'

        # Build installation summary
        console.print('\n[bold]Installation Summary:[/bold]')
        agent_names_display = [agents[a].display_name for a in target_agents]

        for skill in selected_skills:
            if install_mode == 'symlink':
                canonical_path = get_canonical_path(skill.name, install_globally, cwd)
                short_path = _shorten_path(str(canonical_path), cwd)
                console.print(f'  [cyan]{short_path}[/cyan]')
                console.print(
                    f'    [dim]symlink ->[/dim] {_format_list(agent_names_display)}'
                )
            else:
                console.print(f'  [cyan]{get_skill_display_name(skill)}[/cyan]')
                console.print(
                    f'    [dim]copy ->[/dim] {_format_list(agent_names_display)}'
                )

        # Confirm installation
        if not yes:
            if not Confirm.ask('\nProceed with installation?', default=True):
                console.print('[yellow]Installation cancelled[/yellow]')
                return

        # Install skills
        with console.status('[bold blue]Installing skills...'):
            results = []

            for skill in selected_skills:
                for agent_type in target_agents:
                    result = await install_skill_for_agent(
                        skill,
                        agent_type,
                        is_global=install_globally,
                        cwd=cwd,
                        mode=install_mode,
                    )
                    results.append(
                        {
                            'skill': get_skill_display_name(skill),
                            'agent': agents[agent_type].display_name,
                            **vars(result),
                        }
                    )

        # Show results
        console.print()
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]

        if successful:
            skill_count = len(set(r['skill'] for r in successful))
            agent_count = len(set(r['agent'] for r in successful))
            console.print(
                f'[green]Installed {skill_count} skill{"s" if skill_count > 1 else ""} to {agent_count} agent{"s" if agent_count > 1 else ""}[/green]'
            )

            for skill_name in set(r['skill'] for r in successful):
                skill_results = [r for r in successful if r['skill'] == skill_name]
                first_result = skill_results[0]

                if first_result['mode'] == 'copy':
                    console.print(
                        f'  [green]✓[/green] {skill_name} [dim](copied)[/dim]'
                    )
                    for r in skill_results:
                        short_path = _shorten_path(r['path'], cwd)
                        console.print(f'    [dim]→[/dim] {short_path}')
                else:
                    if first_result.get('canonical_path'):
                        short_path = _shorten_path(first_result['canonical_path'], cwd)
                        console.print(f'  [green]✓[/green] {short_path}')
                    else:
                        console.print(f'  [green]✓[/green] {skill_name}')

                    symlinked = [
                        r['agent'] for r in skill_results if not r.get('symlink_failed')
                    ]
                    copied = [
                        r['agent'] for r in skill_results if r.get('symlink_failed')
                    ]

                    if symlinked:
                        console.print(
                            f'    [dim]symlink →[/dim] {_format_list(symlinked)}'
                        )
                    if copied:
                        console.print(
                            f'    [yellow]copied →[/yellow] {_format_list(copied)}'
                        )

            # Symlink failure warning
            symlink_failures = [r for r in successful if r.get('symlink_failed')]
            if symlink_failures:
                failed_agents = [r['agent'] for r in symlink_failures]
                console.print(
                    f'\n[yellow]Symlinks failed for: {_format_list(failed_agents)}[/yellow]'
                )
                console.print(
                    '[dim]  Files were copied instead. On Windows, enable Developer Mode for symlink support.[/dim]'
                )

        if failed:
            console.print(f'\n[red]Failed to install {len(failed)}[/red]')
            for r in failed:
                console.print(
                    f'  [red]✗[/red] {r["skill"]} → {r["agent"]}: [dim]{r.get("error", "Unknown error")}[/dim]'
                )

        console.print('\n[green]Done![/green]')

    except GitCloneError as e:
        console.print('[red]Failed to clone repository[/red]')
        for line in str(e).split('\n'):
            console.print(f'[dim]{line}[/dim]')
        console.print(
            '\n[dim]Tip: use the --yes (-y) and --global (-g) flags to install without prompts.[/dim]'
        )

    except Exception as e:
        console.print(f'[red]Error: {e}[/red]')

    finally:
        if temp_dir:
            try:
                await cleanup_temp_dir(temp_dir)
            except Exception:
                pass
