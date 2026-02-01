"""Mintlify documentation provider for skills."""

from typing import Any
from urllib.parse import urlparse

import frontmatter
import httpx

from skillsmd.providers.base import HostProvider, ProviderMatch, RemoteSkill

# Hosts that should not be matched by Mintlify provider
EXCLUDED_HOSTS = [
    'github.com',
    'gitlab.com',
    'huggingface.co',
    'raw.githubusercontent.com',
]


class MintlifyProvider(HostProvider):
    """Provider for Mintlify documentation sites with SKILL.md files."""

    @property
    def id(self) -> str:
        return 'mintlify'

    @property
    def display_name(self) -> str:
        return 'Mintlify'

    def match(self, url: str) -> ProviderMatch:
        """Match HTTP(S) URLs ending with /skill.md (excluding git hosts)."""
        if not url.startswith('http://') and not url.startswith('https://'):
            return ProviderMatch(matches=False)

        # Must end with /skill.md (case insensitive)
        if not url.lower().endswith('/skill.md'):
            return ProviderMatch(matches=False)

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ''

            # Exclude known git hosts
            if hostname in EXCLUDED_HOSTS:
                return ProviderMatch(matches=False)

            return ProviderMatch(
                matches=True,
                source_identifier=self.get_source_identifier(url),
            )
        except Exception:
            return ProviderMatch(matches=False)

    def to_raw_url(self, url: str) -> str:
        """Mintlify URLs are already raw content URLs."""
        return url

    def get_source_identifier(self, url: str) -> str:
        """Return mintlify/domain as source identifier."""
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or 'com'
            return f'mintlify/{hostname}'
        except Exception:
            return 'mintlify/com'

    async def fetch_skill(self, url: str) -> RemoteSkill | None:
        """Fetch a skill from a Mintlify documentation site."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    url,
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

                # Get install name from metadata.mintlify-proj or derive from name
                metadata: dict[str, Any] = {}
                for key, value in post.metadata.items():
                    if key not in ('name', 'description'):
                        metadata[key] = value

                # Check for mintlify-proj in metadata
                install_name = None
                if 'metadata' in post.metadata:
                    meta = post.metadata.get('metadata', {})
                    if isinstance(meta, dict):
                        install_name = meta.get('mintlify-proj')

                # Fallback to name-based install name
                if not install_name:
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
