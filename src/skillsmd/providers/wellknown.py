"""Well-known skills provider implementing RFC 8615 well-known URIs."""

import asyncio
from dataclasses import dataclass, field
from typing import Any
from urllib.parse import urlparse

import frontmatter
import httpx

from skillsmd.providers.base import HostProvider, ProviderMatch, RemoteSkill

# Hosts that have their own dedicated providers
EXCLUDED_HOSTS = [
    'github.com',
    'gitlab.com',
    'huggingface.co',
    'raw.githubusercontent.com',
]


@dataclass
class WellKnownSkillEntry:
    """A skill entry from the well-known index."""

    name: str  # Skill identifier (lowercase alphanumeric + hyphens)
    description: str  # Brief description
    files: list[str] = field(default_factory=list)  # Files in skill directory


@dataclass
class WellKnownIndex:
    """The index.json structure for well-known skills."""

    skills: list[WellKnownSkillEntry] = field(default_factory=list)


@dataclass
class WellKnownSkill(RemoteSkill):
    """A skill fetched from a well-known endpoint with all files."""

    files: dict[str, str] = field(default_factory=dict)  # filename -> content
    index_entry: WellKnownSkillEntry | None = None


class WellKnownProvider(HostProvider):
    """Provider for RFC 8615 well-known skills endpoints."""

    @property
    def id(self) -> str:
        return 'well-known'

    @property
    def display_name(self) -> str:
        return 'Well-Known Skills'

    def match(self, url: str) -> ProviderMatch:
        """Match any HTTP(S) URL not handled by other providers."""
        if not url.startswith('http://') and not url.startswith('https://'):
            return ProviderMatch(matches=False)

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ''

            # Exclude known git hosts
            if hostname in EXCLUDED_HOSTS:
                return ProviderMatch(matches=False)

            # Don't match direct SKILL.md links (handled by direct-url type)
            if url.lower().endswith('/skill.md'):
                return ProviderMatch(matches=False)

            # Don't match git repo URLs
            if url.endswith('.git'):
                return ProviderMatch(matches=False)

            return ProviderMatch(
                matches=True,
                source_identifier=self.get_source_identifier(url),
            )
        except Exception:
            return ProviderMatch(matches=False)

    def to_raw_url(self, url: str) -> str:
        """Convert URL to raw content URL (identity for well-known)."""
        return url

    def get_source_identifier(self, url: str) -> str:
        """Return domain as source identifier."""
        try:
            parsed = urlparse(url)
            return parsed.hostname or url
        except Exception:
            return url

    def _get_well_known_base(self, url: str) -> str:
        """Get the base URL for well-known skills endpoint."""
        parsed = urlparse(url)

        # If URL already contains .well-known/skills, use it as base
        path = parsed.path.rstrip('/')
        if '/.well-known/skills' in path:
            # Find the .well-known/skills part and use everything up to it
            idx = path.find('/.well-known/skills')
            base_path = path[: idx + len('/.well-known/skills')]
            return f'{parsed.scheme}://{parsed.netloc}{base_path}'

        # Otherwise, construct the well-known URL
        base_path = path if path else ''
        return f'{parsed.scheme}://{parsed.netloc}{base_path}/.well-known/skills'

    async def fetch_index(self, base_url: str) -> WellKnownIndex | None:
        """Fetch the skills index from a well-known endpoint."""
        well_known_base = self._get_well_known_base(base_url)
        index_url = f'{well_known_base}/index.json'

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    index_url,
                    timeout=30.0,
                    follow_redirects=True,
                )

                if response.status_code != 200:
                    return None

                data = response.json()
                skills = []

                for entry in data.get('skills', []):
                    skills.append(
                        WellKnownSkillEntry(
                            name=entry.get('name', ''),
                            description=entry.get('description', ''),
                            files=entry.get('files', []),
                        )
                    )

                return WellKnownIndex(skills=skills)

        except (httpx.RequestError, ValueError):
            return None

    async def has_skills_index(self, url: str) -> bool:
        """Check if a URL has a skills index."""
        index = await self.fetch_index(url)
        return index is not None and len(index.skills) > 0

    async def fetch_skill_by_entry(
        self, base_url: str, entry: WellKnownSkillEntry
    ) -> WellKnownSkill | None:
        """Fetch a skill by its index entry."""
        well_known_base = self._get_well_known_base(base_url)
        skill_base_url = f'{well_known_base}/{entry.name}'

        try:
            async with httpx.AsyncClient() as client:
                # Fetch SKILL.md (required)
                skill_md_url = f'{skill_base_url}/SKILL.md'
                response = await client.get(
                    skill_md_url,
                    timeout=30.0,
                    follow_redirects=True,
                )

                if response.status_code != 200:
                    return None

                content = response.text
                post = frontmatter.loads(content)

                name = post.get('name', entry.name)
                description = post.get('description', entry.description)

                # Build metadata from frontmatter
                metadata: dict[str, Any] = {}
                for key, value in post.metadata.items():
                    if key not in ('name', 'description'):
                        metadata[key] = value

                # Fetch additional files in parallel
                files: dict[str, str] = {'SKILL.md': content}

                if entry.files:
                    other_files = [f for f in entry.files if f != 'SKILL.md']

                    async def fetch_file(filename: str) -> tuple[str, str | None]:
                        try:
                            file_url = f'{skill_base_url}/{filename}'
                            resp = await client.get(
                                file_url,
                                timeout=30.0,
                                follow_redirects=True,
                            )
                            if resp.status_code == 200:
                                return (filename, resp.text)
                        except Exception:
                            pass
                        return (filename, None)

                    results = await asyncio.gather(
                        *[fetch_file(f) for f in other_files]
                    )
                    for filename, file_content in results:
                        if file_content is not None:
                            files[filename] = file_content

                return WellKnownSkill(
                    name=name,
                    description=description,
                    content=content,
                    install_name=entry.name,
                    source_url=skill_md_url,
                    metadata=metadata if metadata else None,
                    files=files,
                    index_entry=entry,
                )

        except (httpx.RequestError, ValueError):
            return None

    async def fetch_skill(self, url: str) -> RemoteSkill | None:
        """Fetch a single skill from a URL."""
        # First try to get the index
        index = await self.fetch_index(url)

        if index and index.skills:
            # Look for skill name in path (after .well-known/skills/)
            skill_name = None
            if '/.well-known/skills/' in url:
                idx = url.find('/.well-known/skills/')
                remainder = url[idx + len('/.well-known/skills/') :].strip('/')
                if remainder and '/' not in remainder:
                    skill_name = remainder

            if skill_name:
                # Find the specific skill
                for entry in index.skills:
                    if entry.name == skill_name:
                        return await self.fetch_skill_by_entry(url, entry)
                return None

            # Return first skill if no specific skill requested
            if index.skills:
                return await self.fetch_skill_by_entry(url, index.skills[0])

        return None

    async def fetch_all_skills(self, url: str) -> list[WellKnownSkill]:
        """Fetch all skills from a well-known endpoint."""
        index = await self.fetch_index(url)

        if not index or not index.skills:
            return []

        # Fetch all skills in parallel
        tasks = [self.fetch_skill_by_entry(url, entry) for entry in index.skills]
        results = await asyncio.gather(*tasks)

        return [skill for skill in results if skill is not None]
