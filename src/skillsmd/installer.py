"""Skill installation for the skillsmd CLI."""

import os
import platform
import re
import shutil
from pathlib import Path

from .agents import get_agents, get_agent_config, detect_installed_agents
from .constants import AGENTS_DIR, SKILLS_SUBDIR
from .skills import parse_skill_md
from .types import (
    InstallMode,
    InstallResult,
    InstalledSkill,
    RemoteSkill,
    Skill,
)

EXCLUDE_FILES = {"README.md", "metadata.json"}
EXCLUDE_DIRS = {".git"}


def sanitize_name(name: str) -> str:
    """
    Sanitizes a filename/directory name to prevent path traversal attacks
    and ensures it follows kebab-case convention.
    """
    # Convert to lowercase and replace non-alphanumeric chars with hyphens
    sanitized = name.lower()
    sanitized = re.sub(r"[^a-z0-9._]+", "-", sanitized)
    # Remove leading/trailing dots and hyphens
    sanitized = re.sub(r"^[.\-]+|[.\-]+$", "", sanitized)
    # Limit to 255 chars and provide fallback
    return sanitized[:255] or "unnamed-skill"


def _is_path_safe(base_path: Path, target_path: Path) -> bool:
    """Validates that a path is within an expected base directory.

    Note: We use strict=False to avoid following symlinks, which would cause
    false positives when checking paths that are symlinks to canonical locations.
    """
    # Normalize paths without resolving symlinks
    # Use os.path.normpath to handle .. and . without following symlinks
    import os
    normalized_base = os.path.normpath(os.path.abspath(str(base_path)))
    normalized_target = os.path.normpath(os.path.abspath(str(target_path)))

    # Check if target starts with base path
    return normalized_target.startswith(normalized_base + os.sep) or normalized_target == normalized_base


def get_canonical_skills_dir(is_global: bool, cwd: str | None = None) -> Path:
    """Gets the canonical .agents/skills directory path."""
    if is_global:
        base_dir = Path.home()
    else:
        base_dir = Path(cwd) if cwd else Path.cwd()
    return base_dir / AGENTS_DIR / SKILLS_SUBDIR


async def _clean_and_create_directory(path: Path) -> None:
    """Cleans and recreates a directory for skill installation."""
    try:
        if path.exists():
            shutil.rmtree(path)
    except Exception:
        pass
    path.mkdir(parents=True, exist_ok=True)


async def _create_symlink(target: Path, link_path: Path) -> bool:
    """
    Creates a symlink, handling cross-platform differences.
    Returns True if symlink was created, False if fallback to copy is needed.
    """
    try:
        resolved_target = target.resolve()
        resolved_link = link_path.resolve()

        if resolved_target == resolved_link:
            return True

        # Remove existing link/directory
        if link_path.exists() or link_path.is_symlink():
            if link_path.is_symlink():
                existing_target = link_path.resolve()
                if existing_target == resolved_target:
                    return True
            if link_path.is_dir() and not link_path.is_symlink():
                shutil.rmtree(link_path)
            else:
                link_path.unlink()

        # Create parent directory
        link_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate relative path for symlink
        try:
            relative_target = os.path.relpath(target, link_path.parent)
        except ValueError:
            # On Windows, relpath fails across drives
            relative_target = str(target)

        # Use junction on Windows, symlink on Unix
        if platform.system() == "Windows":
            # On Windows, use junction for directories
            import subprocess

            result = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link_path), str(target)],
                capture_output=True,
                text=True,
            )
            return result.returncode == 0
        else:
            link_path.symlink_to(relative_target)
            return True

    except Exception:
        return False


def _is_excluded(name: str, is_directory: bool = False) -> bool:
    """Check if a file/directory should be excluded from copying."""
    if name in EXCLUDE_FILES:
        return True
    if name.startswith("_"):
        return True
    if is_directory and name in EXCLUDE_DIRS:
        return True
    return False


async def _copy_directory(src: Path, dest: Path) -> None:
    """Copy a directory recursively, excluding certain files."""
    dest.mkdir(parents=True, exist_ok=True)

    for entry in src.iterdir():
        if _is_excluded(entry.name, entry.is_dir()):
            continue

        src_path = entry
        dest_path = dest / entry.name

        if entry.is_dir():
            await _copy_directory(src_path, dest_path)
        else:
            # Follow symlinks when copying
            if entry.is_symlink():
                real_path = entry.resolve()
                if real_path.is_file():
                    shutil.copy2(real_path, dest_path)
            else:
                shutil.copy2(src_path, dest_path)


async def install_skill_for_agent(
    skill: Skill,
    agent_type: str,
    is_global: bool = False,
    cwd: str | None = None,
    mode: InstallMode = "symlink",
) -> InstallResult:
    """Install a skill for a specific agent."""
    agents = get_agents()
    agent = agents.get(agent_type)

    if not agent:
        return InstallResult(
            success=False,
            path="",
            mode=mode,
            error=f"Unknown agent: {agent_type}",
        )

    working_dir = cwd or str(Path.cwd())

    # Check if agent supports global installation
    if is_global and agent.global_skills_dir is None:
        return InstallResult(
            success=False,
            path="",
            mode=mode,
            error=f"{agent.display_name} does not support global skill installation",
        )

    # Sanitize skill name
    raw_skill_name = skill.name or Path(skill.path).name
    skill_name = sanitize_name(raw_skill_name)

    # Canonical location: .agents/skills/<skill-name>
    canonical_base = get_canonical_skills_dir(is_global, working_dir)
    canonical_dir = canonical_base / skill_name

    # Agent-specific location
    if is_global:
        agent_base = Path(agent.global_skills_dir)  # type: ignore
    else:
        agent_base = Path(working_dir) / agent.skills_dir
    agent_dir = agent_base / skill_name

    # Validate paths
    if not _is_path_safe(canonical_base, canonical_dir):
        return InstallResult(
            success=False,
            path=str(agent_dir),
            mode=mode,
            error="Invalid skill name: potential path traversal detected",
        )

    if not _is_path_safe(agent_base, agent_dir):
        return InstallResult(
            success=False,
            path=str(agent_dir),
            mode=mode,
            error="Invalid skill name: potential path traversal detected",
        )

    try:
        skill_path = Path(skill.path)

        # For copy mode, skip canonical directory and copy directly
        if mode == "copy":
            await _clean_and_create_directory(agent_dir)
            await _copy_directory(skill_path, agent_dir)

            return InstallResult(
                success=True,
                path=str(agent_dir),
                mode="copy",
            )

        # Symlink mode: copy to canonical location and symlink to agent location
        await _clean_and_create_directory(canonical_dir)
        await _copy_directory(skill_path, canonical_dir)

        symlink_created = await _create_symlink(canonical_dir, agent_dir)

        if not symlink_created:
            # Symlink failed, fall back to copy
            await _clean_and_create_directory(agent_dir)
            await _copy_directory(skill_path, agent_dir)

            return InstallResult(
                success=True,
                path=str(agent_dir),
                canonical_path=str(canonical_dir),
                mode="symlink",
                symlink_failed=True,
            )

        return InstallResult(
            success=True,
            path=str(agent_dir),
            canonical_path=str(canonical_dir),
            mode="symlink",
        )

    except Exception as e:
        return InstallResult(
            success=False,
            path=str(agent_dir),
            mode=mode,
            error=str(e),
        )


async def install_remote_skill_for_agent(
    skill: RemoteSkill,
    agent_type: str,
    is_global: bool = False,
    cwd: str | None = None,
    mode: InstallMode = "symlink",
) -> InstallResult:
    """Install a remote skill for a specific agent."""
    agents = get_agents()
    agent = agents.get(agent_type)

    if not agent:
        return InstallResult(
            success=False,
            path="",
            mode=mode,
            error=f"Unknown agent: {agent_type}",
        )

    working_dir = cwd or str(Path.cwd())

    # Check if agent supports global installation
    if is_global and agent.global_skills_dir is None:
        return InstallResult(
            success=False,
            path="",
            mode=mode,
            error=f"{agent.display_name} does not support global skill installation",
        )

    # Sanitize skill name
    skill_name = sanitize_name(skill.install_name)

    # Canonical location: .agents/skills/<skill-name>
    canonical_base = get_canonical_skills_dir(is_global, working_dir)
    canonical_dir = canonical_base / skill_name

    # Agent-specific location
    if is_global:
        agent_base = Path(agent.global_skills_dir)  # type: ignore
    else:
        agent_base = Path(working_dir) / agent.skills_dir
    agent_dir = agent_base / skill_name

    # Validate paths
    if not _is_path_safe(canonical_base, canonical_dir):
        return InstallResult(
            success=False,
            path=str(agent_dir),
            mode=mode,
            error="Invalid skill name: potential path traversal detected",
        )

    if not _is_path_safe(agent_base, agent_dir):
        return InstallResult(
            success=False,
            path=str(agent_dir),
            mode=mode,
            error="Invalid skill name: potential path traversal detected",
        )

    try:
        # For copy mode, write directly to agent location
        if mode == "copy":
            await _clean_and_create_directory(agent_dir)
            skill_md_path = agent_dir / "SKILL.md"
            skill_md_path.write_text(skill.content, encoding="utf-8")

            return InstallResult(
                success=True,
                path=str(agent_dir),
                mode="copy",
            )

        # Symlink mode: write to canonical location and symlink
        await _clean_and_create_directory(canonical_dir)
        skill_md_path = canonical_dir / "SKILL.md"
        skill_md_path.write_text(skill.content, encoding="utf-8")

        symlink_created = await _create_symlink(canonical_dir, agent_dir)

        if not symlink_created:
            # Symlink failed, fall back to copy
            await _clean_and_create_directory(agent_dir)
            agent_skill_md = agent_dir / "SKILL.md"
            agent_skill_md.write_text(skill.content, encoding="utf-8")

            return InstallResult(
                success=True,
                path=str(agent_dir),
                canonical_path=str(canonical_dir),
                mode="symlink",
                symlink_failed=True,
            )

        return InstallResult(
            success=True,
            path=str(agent_dir),
            canonical_path=str(canonical_dir),
            mode="symlink",
        )

    except Exception as e:
        return InstallResult(
            success=False,
            path=str(agent_dir),
            mode=mode,
            error=str(e),
        )


async def is_skill_installed(
    skill_name: str,
    agent_type: str,
    is_global: bool = False,
    cwd: str | None = None,
) -> bool:
    """Check if a skill is installed for an agent."""
    agents = get_agents()
    agent = agents.get(agent_type)

    if not agent:
        return False

    sanitized = sanitize_name(skill_name)
    working_dir = cwd or str(Path.cwd())

    # Agent doesn't support global installation
    if is_global and agent.global_skills_dir is None:
        return False

    if is_global:
        target_base = Path(agent.global_skills_dir)  # type: ignore
    else:
        target_base = Path(working_dir) / agent.skills_dir

    skill_dir = target_base / sanitized

    if not _is_path_safe(target_base, skill_dir):
        return False

    return skill_dir.exists()


def get_install_path(
    skill_name: str,
    agent_type: str,
    is_global: bool = False,
    cwd: str | None = None,
) -> Path:
    """Get the installation path for a skill."""
    agents = get_agents()
    agent = agents.get(agent_type)

    if not agent:
        raise ValueError(f"Unknown agent: {agent_type}")

    working_dir = cwd or str(Path.cwd())
    sanitized = sanitize_name(skill_name)

    if is_global and agent.global_skills_dir is not None:
        target_base = Path(agent.global_skills_dir)
    else:
        target_base = Path(working_dir) / agent.skills_dir

    install_path = target_base / sanitized

    if not _is_path_safe(target_base, install_path):
        raise ValueError("Invalid skill name: potential path traversal detected")

    return install_path


def get_canonical_path(
    skill_name: str,
    is_global: bool = False,
    cwd: str | None = None,
) -> Path:
    """Gets the canonical .agents/skills/<skill> path."""
    sanitized = sanitize_name(skill_name)
    canonical_base = get_canonical_skills_dir(is_global, cwd)
    canonical_path = canonical_base / sanitized

    if not _is_path_safe(canonical_base, canonical_path):
        raise ValueError("Invalid skill name: potential path traversal detected")

    return canonical_path


async def list_installed_skills(
    is_global: bool | None = None,
    cwd: str | None = None,
    agent_filter: list[str] | None = None,
) -> list[InstalledSkill]:
    """Lists all installed skills from canonical locations."""
    working_dir = cwd or str(Path.cwd())
    installed_skills: list[InstalledSkill] = []
    scopes: list[tuple[bool, Path]] = []

    # Detect which agents are actually installed
    detected_agents = await detect_installed_agents()
    agents = get_agents()

    # Determine which scopes to scan
    if is_global is None:
        # Scan both project and global
        scopes.append((False, get_canonical_skills_dir(False, working_dir)))
        scopes.append((True, get_canonical_skills_dir(True, working_dir)))
    else:
        scopes.append((is_global, get_canonical_skills_dir(is_global, working_dir)))

    for scope_global, scope_path in scopes:
        try:
            if not scope_path.exists():
                continue

            for entry in scope_path.iterdir():
                if not entry.is_dir():
                    continue

                skill_md_path = entry / "SKILL.md"

                if not skill_md_path.exists():
                    continue

                skill = await parse_skill_md(skill_md_path)
                if not skill:
                    continue

                # Find which agents have this skill installed
                sanitized_skill_name = sanitize_name(skill.name)
                installed_agents: list[str] = []

                agents_to_check = agent_filter or detected_agents

                for agent_type in agents_to_check:
                    if agent_type not in detected_agents:
                        continue

                    agent = agents.get(agent_type)
                    if not agent:
                        continue

                    # Skip agents that don't support global installation
                    if scope_global and agent.global_skills_dir is None:
                        continue

                    if scope_global:
                        agent_base = Path(agent.global_skills_dir)  # type: ignore
                    else:
                        agent_base = Path(working_dir) / agent.skills_dir

                    # Check multiple possible names
                    possible_names = [
                        entry.name,
                        sanitized_skill_name,
                        skill.name.lower().replace(" ", "-"),
                    ]

                    found = False
                    for possible_name in set(possible_names):
                        agent_skill_dir = agent_base / possible_name
                        if _is_path_safe(agent_base, agent_skill_dir):
                            if agent_skill_dir.exists():
                                found = True
                                break

                    if found:
                        installed_agents.append(agent_type)

                installed_skills.append(
                    InstalledSkill(
                        name=skill.name,
                        description=skill.description,
                        path=str(entry),
                        canonical_path=str(entry),
                        scope="global" if scope_global else "project",
                        agents=installed_agents,
                    )
                )

        except Exception:
            pass

    return installed_skills
