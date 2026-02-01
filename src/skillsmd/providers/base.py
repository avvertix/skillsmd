"""Base types and interfaces for remote skill providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class RemoteSkill:
    """Represents a parsed skill from a remote host."""

    name: str  # Display name (from frontmatter)
    description: str  # Description (from frontmatter)
    content: str  # Full markdown content
    install_name: str  # Installation directory name
    source_url: str  # Original source URL
    metadata: dict[str, Any] | None = None  # Additional frontmatter metadata


@dataclass
class ProviderMatch:
    """Result of URL matching against a provider."""

    matches: bool
    source_identifier: str | None = None  # e.g., "mintlify/bun.com"


class HostProvider(ABC):
    """Base interface for all skill providers."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique identifier for this provider."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable display name."""
        pass

    @abstractmethod
    def match(self, url: str) -> ProviderMatch:
        """Check if this provider can handle the given URL."""
        pass

    @abstractmethod
    async def fetch_skill(self, url: str) -> RemoteSkill | None:
        """Fetch a skill from the given URL."""
        pass

    @abstractmethod
    def to_raw_url(self, url: str) -> str:
        """Convert a user-facing URL to a raw content URL."""
        pass

    @abstractmethod
    def get_source_identifier(self, url: str) -> str:
        """Get a unique identifier for the source (for telemetry/grouping)."""
        pass
