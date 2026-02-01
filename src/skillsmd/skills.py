"""Skill discovery and SKILL.md parsing for the skillsmd CLI."""

import os
from pathlib import Path
from typing import Any

import frontmatter

from skillsmd.types import Skill

SKIP_DIRS = {'node_modules', '.git', 'dist', 'build', '__pycache__', '.venv', 'venv'}


def should_install_internal_skills() -> bool:
    """
    Check if internal skills should be installed.
    Internal skills are hidden by default unless INSTALL_INTERNAL_SKILLS=1 is set.
    """
    env_value = os.environ.get('INSTALL_INTERNAL_SKILLS', '')
    return env_value in ('1', 'true')


async def _has_skill_md(dir_path: Path) -> bool:
    """Check if a directory contains a SKILL.md file."""
    skill_path = dir_path / 'SKILL.md'
    return skill_path.is_file()


async def parse_skill_md(
    skill_md_path: Path,
    include_internal: bool = False,
) -> Skill | None:
    """
    Parse a SKILL.md file and return a Skill object.
    Returns None if the file is invalid or should be skipped.
    """
    try:
        content = skill_md_path.read_text(encoding='utf-8')
        post = frontmatter.loads(content)

        name = post.get('name')
        description = post.get('description')

        if not name or not description:
            return None

        # Check for internal skills
        metadata: dict[str, Any] = post.get('metadata', {}) or {}
        is_internal = metadata.get('internal', False) is True

        if (
            is_internal
            and not should_install_internal_skills()
            and not include_internal
        ):
            return None

        return Skill(
            name=str(name),
            description=str(description),
            path=str(skill_md_path.parent),
            raw_content=content,
            metadata=metadata if metadata else None,
        )
    except Exception:
        return None


async def _find_skill_dirs(
    dir_path: Path,
    depth: int = 0,
    max_depth: int = 5,
) -> list[Path]:
    """Recursively find directories containing SKILL.md files."""
    if depth > max_depth:
        return []

    results: list[Path] = []

    try:
        has_skill = await _has_skill_md(dir_path)
        if has_skill:
            results.append(dir_path)

        # Search subdirectories
        for entry in dir_path.iterdir():
            if entry.is_dir() and entry.name not in SKIP_DIRS:
                sub_results = await _find_skill_dirs(entry, depth + 1, max_depth)
                results.extend(sub_results)
    except Exception:
        pass

    return results


async def discover_skills(
    base_path: str,
    subpath: str | None = None,
    include_internal: bool = False,
    full_depth: bool = False,
) -> list[Skill]:
    """
    Discover skills in a directory.

    Args:
        base_path: The base path to search
        subpath: Optional subpath within base_path
        include_internal: Include internal skills
        full_depth: Search all subdirectories even when a root SKILL.md exists
    """
    skills: list[Skill] = []
    seen_names: set[str] = set()

    search_path = Path(base_path)
    if subpath:
        search_path = search_path / subpath

    # If pointing directly at a skill, add it
    if await _has_skill_md(search_path):
        skill = await parse_skill_md(search_path / 'SKILL.md', include_internal)
        if skill:
            skills.append(skill)
            seen_names.add(skill.name)
            # Return early unless full_depth is set
            if not full_depth:
                return skills

    # Search common skill locations first
    priority_search_dirs = [
        search_path,
        search_path / 'skills',
        search_path / 'skills' / '.curated',
        search_path / 'skills' / '.experimental',
        search_path / 'skills' / '.system',
        search_path / '.agent' / 'skills',
        search_path / '.agents' / 'skills',
        search_path / '.claude' / 'skills',
        search_path / '.cline' / 'skills',
        search_path / '.codebuddy' / 'skills',
        search_path / '.codex' / 'skills',
        search_path / '.commandcode' / 'skills',
        search_path / '.continue' / 'skills',
        search_path / '.cursor' / 'skills',
        search_path / '.github' / 'skills',
        search_path / '.goose' / 'skills',
        search_path / '.iflow' / 'skills',
        search_path / '.junie' / 'skills',
        search_path / '.kilocode' / 'skills',
        search_path / '.kiro' / 'skills',
        search_path / '.mux' / 'skills',
        search_path / '.neovate' / 'skills',
        search_path / '.openclaude' / 'skills',
        search_path / '.opencode' / 'skills',
        search_path / '.openhands' / 'skills',
        search_path / '.pi' / 'skills',
        search_path / '.qoder' / 'skills',
        search_path / '.roo' / 'skills',
        search_path / '.trae' / 'skills',
        search_path / '.windsurf' / 'skills',
        search_path / '.zencoder' / 'skills',
    ]

    for dir_path in priority_search_dirs:
        try:
            if not dir_path.exists() or not dir_path.is_dir():
                continue

            for entry in dir_path.iterdir():
                if entry.is_dir():
                    skill_dir = entry
                    if await _has_skill_md(skill_dir):
                        skill = await parse_skill_md(
                            skill_dir / 'SKILL.md', include_internal
                        )
                        if skill and skill.name not in seen_names:
                            skills.append(skill)
                            seen_names.add(skill.name)
        except Exception:
            pass

    # Fall back to recursive search if nothing found
    if len(skills) == 0:
        all_skill_dirs = await _find_skill_dirs(search_path)

        for skill_dir in all_skill_dirs:
            skill = await parse_skill_md(skill_dir / 'SKILL.md', include_internal)
            if skill and skill.name not in seen_names:
                skills.append(skill)
                seen_names.add(skill.name)

    return skills


def get_skill_display_name(skill: Skill) -> str:
    """Get the display name for a skill."""
    return skill.name or Path(skill.path).name


def filter_skills(skills: list[Skill], input_names: list[str]) -> list[Skill]:
    """
    Filter skills based on user input (case-insensitive direct matching).
    Multi-word skill names must be quoted on the command line.
    """
    normalized_inputs = [n.lower() for n in input_names]

    return [
        skill
        for skill in skills
        if skill.name.lower() in normalized_inputs
        or get_skill_display_name(skill).lower() in normalized_inputs
    ]
