"""Init command implementation for the skillsmd CLI."""

from pathlib import Path

from rich.console import Console

console = Console()

SKILL_TEMPLATE = """---
name: {name}
description: A brief description of what this skill does
---

# {name}

Instructions for the agent to follow when this skill is activated.

## When to use

Describe when this skill should be used.

## Instructions

1. First step
2. Second step
3. Additional steps as needed
"""


def run_init(name: str | None = None) -> None:
    """Run the init command to create a SKILL.md template."""
    cwd = Path.cwd()
    skill_name = name or cwd.name
    has_name = name is not None

    skill_dir = cwd / skill_name if has_name else cwd
    skill_file = skill_dir / 'SKILL.md'
    display_path = f'{skill_name}/SKILL.md' if has_name else 'SKILL.md'

    if skill_file.exists():
        console.print(f'Skill already exists at [dim]{display_path}[/dim]')
        return

    if has_name:
        skill_dir.mkdir(parents=True, exist_ok=True)

    skill_content = SKILL_TEMPLATE.format(name=skill_name)
    skill_file.write_text(skill_content, encoding='utf-8')

    console.print(f'Initialized skill: [dim]{skill_name}[/dim]')
    console.print()
    console.print('[dim]Created:[/dim]')
    console.print(f'  {display_path}')
    console.print()
    console.print('[dim]Next steps:[/dim]')
    console.print(
        f'  1. Edit [cyan]{display_path}[/cyan] to define your skill instructions'
    )
    console.print(
        f'  2. Update the [cyan]name[/cyan] and [cyan]description[/cyan] in the frontmatter'
    )
    console.print()
    console.print('[dim]Publishing:[/dim]')
    console.print(
        f'  [dim]GitHub:[/dim]  Push to a repo, then [cyan]skillsmd add <owner>/<repo>[/cyan]'
    )
    console.print(
        f'  [dim]URL:[/dim]     Host the file, then [cyan]skillsmd add https://example.com/{display_path}[/cyan]'
    )
    console.print()
    console.print(
        f'Browse existing skills for inspiration at [cyan]https://skills.sh/[/cyan]'
    )
    console.print()
