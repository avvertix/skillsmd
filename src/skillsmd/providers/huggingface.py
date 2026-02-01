"""HuggingFace Spaces provider for skills."""

import re
from typing import Any
from urllib.parse import urlparse

import frontmatter
import httpx

from skillsmd.providers.base import HostProvider, ProviderMatch, RemoteSkill


class HuggingFaceProvider(HostProvider):
    """Provider for HuggingFace Spaces with SKILL.md files."""

    @property
    def id(self) -> str:
        return 'huggingface'

    @property
    def display_name(self) -> str:
        return 'HuggingFace'

    def _parse_url(self, url: str) -> dict[str, str] | None:
        """Parse owner and repo from a HuggingFace Spaces URL."""
        # Pattern: /spaces/{owner}/{repo}/...
        match = re.search(r'/spaces/([^/]+)/([^/]+)', url)
        if match:
            return {'owner': match.group(1), 'repo': match.group(2)}
        return None

    def match(self, url: str) -> ProviderMatch:
        """Match HuggingFace Spaces URLs ending with /skill.md."""
        if not url.startswith('http://') and not url.startswith('https://'):
            return ProviderMatch(matches=False)

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ''

            # Must be huggingface.co
            if hostname != 'huggingface.co':
                return ProviderMatch(matches=False)

            # Must be a spaces URL
            if '/spaces/' not in url:
                return ProviderMatch(matches=False)

            # Must end with /skill.md (case insensitive)
            if not url.lower().endswith('/skill.md'):
                return ProviderMatch(matches=False)

            return ProviderMatch(
                matches=True,
                source_identifier=self.get_source_identifier(url),
            )
        except Exception:
            return ProviderMatch(matches=False)

    def to_raw_url(self, url: str) -> str:
        """Convert blob URL to raw URL for HuggingFace."""
        # Convert: /blob/main/ -> /raw/main/
        return url.replace('/blob/', '/raw/')

    def get_source_identifier(self, url: str) -> str:
        """Return huggingface/owner/repo as source identifier."""
        info = self._parse_url(url)
        if info:
            return f'huggingface/{info["owner"]}/{info["repo"]}'
        return 'huggingface'

    async def fetch_skill(self, url: str) -> RemoteSkill | None:
        """Fetch a skill from a HuggingFace Spaces repository."""
        try:
            # Convert to raw URL
            raw_url = self.to_raw_url(url)

            async with httpx.AsyncClient() as client:
                response = await client.get(
                    raw_url,
                    timeout=30.0,
                    follow_redirects=True,
                )

                if response.status_code != 200:
                    return None

                content = response.text
                post = frontmatter.loads(content)

                # Extract required fields
                name = post.get('name')
                description = post.get('description')

                if not name or not description:
                    return None

                # Build metadata from frontmatter
                metadata: dict[str, Any] = {}
                for key, value in post.metadata.items():
                    if key not in ('name', 'description'):
                        metadata[key] = value

                # Get install name from metadata or derive from repo
                install_name = None

                # Check for install-name in metadata
                if 'metadata' in post.metadata:
                    meta = post.metadata.get('metadata', {})
                    if isinstance(meta, dict):
                        install_name = meta.get('install-name')

                # Fallback to repo name
                if not install_name:
                    info = self._parse_url(url)
                    if info:
                        install_name = info['repo']
                    else:
                        install_name = name.lower().replace(' ', '-')

                return RemoteSkill(
                    name=name,
                    description=description,
                    content=content,
                    install_name=install_name,
                    source_url=url,
                    metadata=metadata if metadata else None,
                )

        except (httpx.RequestError, ValueError):
            return None
