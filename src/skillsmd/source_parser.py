"""Source string parsing for the skillsmd CLI."""

import re
from pathlib import Path

from skillsmd.types import ParsedSource


def get_owner_repo(parsed: ParsedSource) -> str | None:
    """
    Extract owner/repo from a parsed source for telemetry.
    Returns None for local paths or unparseable sources.
    """
    if parsed.type == 'local':
        return None

    # Extract from git URL: https://github.com/owner/repo.git or similar
    match = re.search(r'(?:github|gitlab)\.com/([^/]+)/([^/]+?)(?:\.git)?$', parsed.url)
    if match:
        return f'{match.group(1)}/{match.group(2)}'

    return None


def parse_owner_repo(owner_repo: str) -> tuple[str, str] | None:
    """
    Extract owner and repo from an owner/repo string.
    Returns None if the format is invalid.
    """
    match = re.match(r'^([^/]+)/([^/]+)$', owner_repo)
    if match:
        return (match.group(1), match.group(2))
    return None


def _is_local_path(input_str: str) -> bool:
    """Check if a string represents a local file system path."""
    path = Path(input_str)

    # Check for absolute path
    if path.is_absolute():
        return True

    # Check for relative paths
    if input_str.startswith('./') or input_str.startswith('../'):
        return True

    if input_str in ('.', '..'):
        return True

    # Windows absolute paths like C:\ or D:\
    if re.match(r'^[a-zA-Z]:[/\\]', input_str):
        return True

    return False


def _is_direct_skill_url(input_str: str) -> bool:
    """
    Check if a URL is a direct link to a skill.md file.
    Supports various hosts: Mintlify docs, HuggingFace Spaces, etc.
    """
    if not input_str.startswith('http://') and not input_str.startswith('https://'):
        return False

    # Must end with skill.md (case insensitive)
    if not input_str.lower().endswith('/skill.md'):
        return False

    # Exclude GitHub and GitLab repository URLs - they have their own handling
    if 'github.com/' in input_str and 'raw.githubusercontent.com' not in input_str:
        # Check if it's a blob/raw URL to SKILL.md
        if '/blob/' not in input_str and '/raw/' not in input_str:
            return False

    if 'gitlab.com/' in input_str and '/-/raw/' not in input_str:
        return False

    return True


def _is_well_known_url(input_str: str) -> bool:
    """
    Check if a URL could be a well-known skills endpoint.
    Must be HTTP(S) and not a known git host.
    """
    if not input_str.startswith('http://') and not input_str.startswith('https://'):
        return False

    try:
        # Simple URL parsing
        from urllib.parse import urlparse

        parsed = urlparse(input_str)

        # Exclude known git hosts
        excluded_hosts = [
            'github.com',
            'gitlab.com',
            'huggingface.co',
            'raw.githubusercontent.com',
        ]
        if parsed.hostname in excluded_hosts:
            return False

        # Don't match URLs that look like direct skill.md links
        if input_str.lower().endswith('/skill.md'):
            return False

        # Don't match URLs that look like git repos
        if input_str.endswith('.git'):
            return False

        return True
    except Exception:
        return False


def parse_source(input_str: str) -> ParsedSource:
    """
    Parse a source string into a structured format.
    Supports: local paths, GitHub URLs, GitLab URLs, GitHub shorthand,
    direct skill.md URLs, and direct git URLs.
    """
    # Local path: absolute, relative, or current directory
    if _is_local_path(input_str):
        resolved_path = str(Path(input_str).resolve())
        return ParsedSource(
            type='local',
            url=resolved_path,
            local_path=resolved_path,
        )

    # Direct skill.md URL (non-GitHub/GitLab)
    if _is_direct_skill_url(input_str):
        return ParsedSource(
            type='direct-url',
            url=input_str,
        )

    # GitHub URL with path: https://github.com/owner/repo/tree/branch/path/to/skill
    github_tree_with_path = re.search(
        r'github\.com/([^/]+)/([^/]+)/tree/([^/]+)/(.+)', input_str
    )
    if github_tree_with_path:
        owner, repo, ref, subpath = github_tree_with_path.groups()
        return ParsedSource(
            type='github',
            url=f'https://github.com/{owner}/{repo}.git',
            ref=ref,
            subpath=subpath,
        )

    # GitHub URL with branch only: https://github.com/owner/repo/tree/branch
    github_tree = re.search(r'github\.com/([^/]+)/([^/]+)/tree/([^/]+)$', input_str)
    if github_tree:
        owner, repo, ref = github_tree.groups()
        return ParsedSource(
            type='github',
            url=f'https://github.com/{owner}/{repo}.git',
            ref=ref,
        )

    # GitHub URL: https://github.com/owner/repo
    github_repo = re.search(r'github\.com/([^/]+)/([^/]+)', input_str)
    if github_repo:
        owner, repo = github_repo.groups()
        clean_repo = re.sub(r'\.git$', '', repo)
        return ParsedSource(
            type='github',
            url=f'https://github.com/{owner}/{clean_repo}.git',
        )

    # GitLab URL with path: https://gitlab.com/owner/repo/-/tree/branch/path
    gitlab_tree_with_path = re.match(
        r'^(https?):\/\/([^/]+)\/(.+?)\/-\/tree\/([^/]+)\/(.+)', input_str
    )
    if gitlab_tree_with_path:
        protocol, hostname, repo_path, ref, subpath = gitlab_tree_with_path.groups()
        if hostname != 'github.com' and repo_path:
            clean_repo = re.sub(r'\.git$', '', repo_path)
            return ParsedSource(
                type='gitlab',
                url=f'{protocol}://{hostname}/{clean_repo}.git',
                ref=ref,
                subpath=subpath,
            )

    # GitLab URL with branch only: https://gitlab.com/owner/repo/-/tree/branch
    gitlab_tree = re.match(
        r'^(https?):\/\/([^/]+)\/(.+?)\/-\/tree\/([^/]+)$', input_str
    )
    if gitlab_tree:
        protocol, hostname, repo_path, ref = gitlab_tree.groups()
        if hostname != 'github.com' and repo_path:
            clean_repo = re.sub(r'\.git$', '', repo_path)
            return ParsedSource(
                type='gitlab',
                url=f'{protocol}://{hostname}/{clean_repo}.git',
                ref=ref,
            )

    # GitLab.com URL: https://gitlab.com/owner/repo
    gitlab_repo = re.search(r'gitlab\.com/([^/]+)/([^/]+)', input_str)
    if gitlab_repo:
        owner, repo = gitlab_repo.groups()
        clean_repo = re.sub(r'\.git$', '', repo)
        return ParsedSource(
            type='gitlab',
            url=f'https://gitlab.com/{owner}/{clean_repo}.git',
        )

    # GitHub shorthand with @skill syntax: owner/repo@skill-name
    at_skill = re.match(r'^([^/]+)/([^/@]+)@(.+)$', input_str)
    if (
        at_skill
        and ':' not in input_str
        and not input_str.startswith('.')
        and not input_str.startswith('/')
    ):
        owner, repo, skill_filter = at_skill.groups()
        return ParsedSource(
            type='github',
            url=f'https://github.com/{owner}/{repo}.git',
            skill_filter=skill_filter,
        )

    # GitHub shorthand: owner/repo or owner/repo/path
    shorthand = re.match(r'^([^/]+)/([^/]+)(?:/(.+))?$', input_str)
    if (
        shorthand
        and ':' not in input_str
        and not input_str.startswith('.')
        and not input_str.startswith('/')
    ):
        owner, repo, subpath = shorthand.groups()
        return ParsedSource(
            type='github',
            url=f'https://github.com/{owner}/{repo}.git',
            subpath=subpath,
        )

    # Well-known skills endpoint
    if _is_well_known_url(input_str):
        return ParsedSource(
            type='well-known',
            url=input_str,
        )

    # Fallback: treat as direct git URL
    return ParsedSource(
        type='git',
        url=input_str,
    )
