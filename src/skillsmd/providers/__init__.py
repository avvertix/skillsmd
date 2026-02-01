"""Remote skill providers for skillsmd.

This module provides a registry of providers for fetching skills from various
remote sources like Mintlify documentation sites, HuggingFace Spaces, and
any site implementing the RFC 8615 well-known skills standard.
"""

from skillsmd.providers.base import (
    HostProvider,
    ProviderMatch,
    RemoteSkill,
)
from skillsmd.providers.huggingface import HuggingFaceProvider
from skillsmd.providers.mintlify import MintlifyProvider
from skillsmd.providers.wellknown import (
    WellKnownProvider,
    WellKnownIndex,
    WellKnownSkill,
    WellKnownSkillEntry,
)


class ProviderRegistry:
    """Registry for managing skill providers."""

    def __init__(self) -> None:
        self._providers: list[HostProvider] = []

    def register(self, provider: HostProvider) -> None:
        """Register a provider with the registry."""
        # Avoid duplicates
        for existing in self._providers:
            if existing.id == provider.id:
                return
        self._providers.append(provider)

    def find_provider(self, url: str) -> HostProvider | None:
        """Find a provider that can handle the given URL."""
        for provider in self._providers:
            match = provider.match(url)
            if match.matches:
                return provider
        return None

    def get_providers(self) -> list[HostProvider]:
        """Get all registered providers."""
        return list(self._providers)


# Global registry instance
registry = ProviderRegistry()


def register_provider(provider: HostProvider) -> None:
    """Register a provider with the global registry."""
    registry.register(provider)


def find_provider(url: str) -> HostProvider | None:
    """Find a provider that can handle the given URL."""
    return registry.find_provider(url)


def get_providers() -> list[HostProvider]:
    """Get all registered providers."""
    return registry.get_providers()


# Create singleton instances
mintlify_provider = MintlifyProvider()
huggingface_provider = HuggingFaceProvider()
wellknown_provider = WellKnownProvider()

# Register built-in providers (order matters - more specific first)
# Note: WellKnownProvider is NOT auto-registered as it's a fallback
register_provider(huggingface_provider)
register_provider(mintlify_provider)


async def fetch_remote_skill(url: str) -> RemoteSkill | None:
    """
    Fetch a skill from a remote URL using the appropriate provider.

    This function tries registered providers first, then falls back to
    the well-known provider if no specific provider matches.
    """
    # Try registered providers first
    provider = find_provider(url)
    if provider:
        return await provider.fetch_skill(url)

    # Fall back to well-known provider
    match = wellknown_provider.match(url)
    if match.matches:
        return await wellknown_provider.fetch_skill(url)

    return None


__all__ = [
    # Base types
    'HostProvider',
    'ProviderMatch',
    'RemoteSkill',
    # Well-known types
    'WellKnownIndex',
    'WellKnownSkill',
    'WellKnownSkillEntry',
    # Provider classes
    'HuggingFaceProvider',
    'MintlifyProvider',
    'WellKnownProvider',
    # Registry
    'ProviderRegistry',
    'registry',
    'register_provider',
    'find_provider',
    'get_providers',
    # Singleton instances
    'huggingface_provider',
    'mintlify_provider',
    'wellknown_provider',
    # High-level function
    'fetch_remote_skill',
]
