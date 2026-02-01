"""Remove command implementation for the skillsmd CLI."""

import io
import shutil
import sys
from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm

from .agents import get_agents, detect_installed_agents
from .installer import (
    get_canonical_path,
    get_canonical_skills_dir,
    get_install_path,
)


def _setup_utf8_encoding() -> None:
    """Ensure UTF-8 encoding for stdout/stderr on Windows."""
    if sys.platform == "win32":
        if hasattr(sys.stdout, "buffer") and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        if hasattr(sys.stderr, "buffer") and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


_setup_utf8_encoding()

console = Console()


async def run_remove(
    skill_names: list[str] | None = None,
    is_global: bool = False,
    agent_names: list[str] | None = None,
    yes: bool = False,
    all_mode: bool = False,
) -> None:
    """Run the remove command."""
    agents = get_agents()
    cwd = str(Path.cwd())

    with console.status("[bold blue]Scanning for installed skills..."):
        skill_names_set: set[str] = set()

        async def scan_dir(dir_path: Path) -> None:
            try:
                if not dir_path.exists():
                    return
                for entry in dir_path.iterdir():
                    if entry.is_dir():
                        skill_names_set.add(entry.name)
            except Exception as e:
                console.print(f"[yellow]Could not scan directory {dir_path}: {e}[/yellow]")

        if is_global:
            await scan_dir(get_canonical_skills_dir(True, cwd))
            for agent in agents.values():
                if agent.global_skills_dir:
                    await scan_dir(Path(agent.global_skills_dir))
        else:
            await scan_dir(get_canonical_skills_dir(False, cwd))
            for agent in agents.values():
                await scan_dir(Path(cwd) / agent.skills_dir)

    installed_skills = sorted(skill_names_set)
    console.print(f"Found {len(installed_skills)} unique installed skill(s)")

    if not installed_skills:
        console.print("[yellow]No skills found to remove.[/yellow]")
        return

    # Validate agent options
    if agent_names:
        valid_agents = list(agents.keys())
        invalid = [a for a in agent_names if a not in valid_agents]
        if invalid:
            console.print(f"[red]Invalid agents: {', '.join(invalid)}[/red]")
            console.print(f"[dim]Valid agents: {', '.join(valid_agents)}[/dim]")
            return

    # Select skills to remove
    selected_skills: list[str]

    if all_mode:
        selected_skills = installed_skills
    elif skill_names:
        selected_skills = [
            s for s in installed_skills
            if any(name.lower() == s.lower() for name in skill_names)
        ]
        if not selected_skills:
            console.print(f"[red]No matching skills found for: {', '.join(skill_names)}[/red]")
            return
    else:
        # Interactive selection
        console.print("\n[bold]Installed Skills:[/bold]")
        for i, skill in enumerate(installed_skills, 1):
            console.print(f"  {i}. [cyan]{skill}[/cyan]")

        console.print("\nEnter skill numbers to remove (comma-separated) or 'all' for all:")
        user_input = console.input("> ").strip()

        if not user_input:
            console.print("[yellow]Removal cancelled[/yellow]")
            return

        if user_input.lower() == "all":
            selected_skills = installed_skills
        else:
            try:
                indices = [int(x.strip()) - 1 for x in user_input.split(",")]
                selected_skills = [installed_skills[i] for i in indices if 0 <= i < len(installed_skills)]
            except (ValueError, IndexError):
                console.print("[red]Invalid selection[/red]")
                return

    # Determine target agents
    target_agents: list[str]
    if agent_names:
        target_agents = agent_names
    else:
        with console.status("[bold blue]Detecting installed agents..."):
            detected = await detect_installed_agents()
        target_agents = detected if detected else list(agents.keys())

    # Confirm removal
    if not yes:
        console.print("\n[bold]Skills to remove:[/bold]")
        for skill in selected_skills:
            console.print(f"  [red]•[/red] {skill}")

        if not Confirm.ask(f"\nAre you sure you want to uninstall {len(selected_skills)} skill(s)?", default=False):
            console.print("[yellow]Removal cancelled[/yellow]")
            return

    # Remove skills
    with console.status("[bold blue]Removing skills..."):
        results: list[dict] = []

        for skill_name in selected_skills:
            try:
                # Remove from each agent
                for agent_type in target_agents:
                    agent = agents.get(agent_type)
                    if not agent:
                        continue

                    try:
                        skill_path = get_install_path(skill_name, agent_type, is_global, cwd)
                        if skill_path.exists() or skill_path.is_symlink():
                            # On Windows, junctions are created which shutil.rmtree can't handle
                            # Check if it's a symlink/junction by checking if it's a reparse point
                            if skill_path.is_symlink():
                                skill_path.unlink()
                            elif sys.platform == "win32" and skill_path.is_dir():
                                # On Windows, try to detect junctions
                                import ctypes
                                FILE_ATTRIBUTE_REPARSE_POINT = 0x400
                                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(skill_path))
                                if attrs != -1 and (attrs & FILE_ATTRIBUTE_REPARSE_POINT):
                                    # It's a junction, remove it like a symlink
                                    import subprocess
                                    subprocess.run(["cmd", "/c", "rmdir", str(skill_path)], check=True)
                                else:
                                    shutil.rmtree(skill_path)
                            else:
                                shutil.rmtree(skill_path)
                    except Exception as e:
                        console.print(
                            f"[yellow]Could not remove skill from {agent.display_name}: {e}[/yellow]"
                        )

                # Remove canonical path
                canonical_path = get_canonical_path(skill_name, is_global, cwd)
                if canonical_path.exists():
                    shutil.rmtree(canonical_path)

                results.append({
                    "skill": skill_name,
                    "success": True,
                })

            except Exception as e:
                results.append({
                    "skill": skill_name,
                    "success": False,
                    "error": str(e),
                })

    # Show results
    successful = [r for r in results if r["success"]]
    failed = [r for r in results if not r["success"]]

    if successful:
        console.print(f"[green]Successfully removed {len(successful)} skill(s)[/green]")

    if failed:
        console.print(f"[red]Failed to remove {len(failed)} skill(s)[/red]")
        for r in failed:
            console.print(f"  [red]✗[/red] {r['skill']}: {r.get('error', 'Unknown error')}")

    console.print("\n[green]Done![/green]")
