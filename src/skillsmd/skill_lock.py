"""Skill lock file management for tracking installed skills and updates."""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

import httpx

from skillsmd.constants import AGENTS_DIR

LOCK_FILE = '.skill-lock.json'
CURRENT_VERSION = 3  # v3 adds skillFolderHash support


@dataclass
class SkillLockEntry:
    """Represents a single installed skill entry in the lock file."""

    source: str  # Normalized source identifier (e.g., "owner/repo")
    source_type: str  # Provider type (e.g., "github", "mintlify")
    source_url: str  # Original URL for re-fetching updates
    skill_folder_hash: str  # GitHub tree SHA for the skill folder
    installed_at: str  # ISO timestamp when first installed
    updated_at: str  # ISO timestamp when last updated
    skill_path: str | None = None  # Subpath within the source repo


@dataclass
class DismissedPrompts:
    """Tracks dismissed prompts so they're not shown again."""

    find_skills_prompt: bool = False


@dataclass
class SkillLockFile:
    """The structure of the skill lock file."""

    version: int = CURRENT_VERSION
    skills: dict[str, SkillLockEntry] = field(default_factory=dict)
    dismissed: DismissedPrompts = field(default_factory=DismissedPrompts)
    last_selected_agents: list[str] | None = None


def get_skill_lock_path() -> Path:
    """Get the path to the global skill lock file (~/.agents/.skill-lock.json)."""
    return Path.home() / AGENTS_DIR / LOCK_FILE


def _lock_entry_to_dict(entry: SkillLockEntry) -> dict[str, Any]:
    """Convert a SkillLockEntry to a JSON-serializable dict."""
    result = {
        'source': entry.source,
        'sourceType': entry.source_type,
        'sourceUrl': entry.source_url,
        'skillFolderHash': entry.skill_folder_hash,
        'installedAt': entry.installed_at,
        'updatedAt': entry.updated_at,
    }
    if entry.skill_path:
        result['skillPath'] = entry.skill_path
    return result


def _dict_to_lock_entry(data: dict[str, Any]) -> SkillLockEntry:
    """Convert a dict to a SkillLockEntry."""
    return SkillLockEntry(
        source=data.get('source', ''),
        source_type=data.get('sourceType', ''),
        source_url=data.get('sourceUrl', ''),
        skill_folder_hash=data.get('skillFolderHash', ''),
        installed_at=data.get('installedAt', ''),
        updated_at=data.get('updatedAt', ''),
        skill_path=data.get('skillPath'),
    )


def _lock_file_to_dict(lock: SkillLockFile) -> dict[str, Any]:
    """Convert a SkillLockFile to a JSON-serializable dict."""
    result: dict[str, Any] = {
        'version': lock.version,
        'skills': {
            name: _lock_entry_to_dict(entry) for name, entry in lock.skills.items()
        },
    }
    if lock.dismissed:
        result['dismissed'] = {
            'findSkillsPrompt': lock.dismissed.find_skills_prompt,
        }
    if lock.last_selected_agents:
        result['lastSelectedAgents'] = lock.last_selected_agents
    return result


def _dict_to_lock_file(data: dict[str, Any]) -> SkillLockFile:
    """Convert a dict to a SkillLockFile."""
    skills = {}
    for name, entry_data in data.get('skills', {}).items():
        skills[name] = _dict_to_lock_entry(entry_data)

    dismissed_data = data.get('dismissed', {})
    dismissed = DismissedPrompts(
        find_skills_prompt=dismissed_data.get('findSkillsPrompt', False),
    )

    return SkillLockFile(
        version=data.get('version', CURRENT_VERSION),
        skills=skills,
        dismissed=dismissed,
        last_selected_agents=data.get('lastSelectedAgents'),
    )


def _create_empty_lock_file() -> SkillLockFile:
    """Create an empty lock file structure."""
    return SkillLockFile()


async def read_skill_lock() -> SkillLockFile:
    """
    Read the skill lock file.

    Returns an empty lock file structure if the file doesn't exist.
    Wipes the lock file if it's an old format (version < CURRENT_VERSION).
    """
    lock_path = get_skill_lock_path()

    try:
        content = lock_path.read_text(encoding='utf-8')
        data = json.loads(content)

        # Validate version - wipe if old format
        if not isinstance(data.get('version'), int) or 'skills' not in data:
            return _create_empty_lock_file()

        # If old version, wipe and start fresh
        if data['version'] < CURRENT_VERSION:
            return _create_empty_lock_file()

        return _dict_to_lock_file(data)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return _create_empty_lock_file()


async def write_skill_lock(lock: SkillLockFile) -> None:
    """
    Write the skill lock file.

    Creates the directory if it doesn't exist.
    """
    lock_path = get_skill_lock_path()

    # Ensure directory exists
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    # Write with pretty formatting
    content = json.dumps(_lock_file_to_dict(lock), indent=2)
    lock_path.write_text(content, encoding='utf-8')


def compute_content_hash(content: str) -> str:
    """Compute SHA-256 hash of content."""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


async def fetch_skill_folder_hash(owner_repo: str, skill_path: str) -> str | None:
    """
    Fetch the tree SHA (folder hash) for a skill folder using GitHub's Trees API.

    Args:
        owner_repo: GitHub owner/repo (e.g., "vercel-labs/agent-skills")
        skill_path: Path to skill folder or SKILL.md

    Returns:
        The tree SHA for the skill folder, or None if not found
    """
    # Normalize to forward slashes
    folder_path = skill_path.replace('\\', '/')

    # Remove SKILL.md suffix to get folder path
    if folder_path.endswith('/SKILL.md'):
        folder_path = folder_path[:-9]
    elif folder_path.endswith('SKILL.md'):
        folder_path = folder_path[:-8]

    # Remove trailing slash
    folder_path = folder_path.rstrip('/')

    branches = ['main', 'master']

    async with httpx.AsyncClient() as client:
        for branch in branches:
            try:
                url = f'https://api.github.com/repos/{owner_repo}/git/trees/{branch}?recursive=1'
                response = await client.get(
                    url,
                    headers={
                        'Accept': 'application/vnd.github.v3+json',
                        'User-Agent': 'skillsmd',
                    },
                    timeout=30.0,
                )

                if response.status_code != 200:
                    continue

                data = response.json()

                # If folder_path is empty, this is a root-level skill
                if not folder_path:
                    return data.get('sha')

                # Find the tree entry for the skill folder
                for entry in data.get('tree', []):
                    if entry.get('type') == 'tree' and entry.get('path') == folder_path:
                        return entry.get('sha')
            except (httpx.RequestError, json.JSONDecodeError):
                continue

    return None


async def add_skill_to_lock(
    skill_name: str,
    source: str,
    source_type: str,
    source_url: str,
    skill_folder_hash: str = '',
    skill_path: str | None = None,
) -> None:
    """Add or update a skill entry in the lock file."""
    lock = await read_skill_lock()
    now = datetime.now().isoformat()

    existing = lock.skills.get(skill_name)

    lock.skills[skill_name] = SkillLockEntry(
        source=source,
        source_type=source_type,
        source_url=source_url,
        skill_folder_hash=skill_folder_hash,
        installed_at=existing.installed_at if existing else now,
        updated_at=now,
        skill_path=skill_path,
    )

    await write_skill_lock(lock)


async def remove_skill_from_lock(skill_name: str) -> bool:
    """Remove a skill from the lock file."""
    lock = await read_skill_lock()

    if skill_name not in lock.skills:
        return False

    del lock.skills[skill_name]
    await write_skill_lock(lock)
    return True


async def get_skill_from_lock(skill_name: str) -> SkillLockEntry | None:
    """Get a skill entry from the lock file."""
    lock = await read_skill_lock()
    return lock.skills.get(skill_name)


async def get_all_locked_skills() -> dict[str, SkillLockEntry]:
    """Get all skills from the lock file."""
    lock = await read_skill_lock()
    return lock.skills


async def get_skills_by_source() -> dict[str, dict[str, Any]]:
    """Get skills grouped by source for batch update operations."""
    lock = await read_skill_lock()
    by_source: dict[str, dict[str, Any]] = {}

    for skill_name, entry in lock.skills.items():
        if entry.source in by_source:
            by_source[entry.source]['skills'].append(skill_name)
        else:
            by_source[entry.source] = {'skills': [skill_name], 'entry': entry}

    return by_source


async def is_prompt_dismissed(prompt_key: Literal['find_skills_prompt']) -> bool:
    """Check if a prompt has been dismissed."""
    lock = await read_skill_lock()
    if prompt_key == 'find_skills_prompt':
        return lock.dismissed.find_skills_prompt
    return False


async def dismiss_prompt(prompt_key: Literal['find_skills_prompt']) -> None:
    """Mark a prompt as dismissed."""
    lock = await read_skill_lock()
    if prompt_key == 'find_skills_prompt':
        lock.dismissed.find_skills_prompt = True
    await write_skill_lock(lock)


async def get_last_selected_agents() -> list[str] | None:
    """Get the last selected agents."""
    lock = await read_skill_lock()
    return lock.last_selected_agents


async def save_selected_agents(agents: list[str]) -> None:
    """Save the selected agents to the lock file."""
    lock = await read_skill_lock()
    lock.last_selected_agents = agents
    await write_skill_lock(lock)
