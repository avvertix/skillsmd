"""Unit tests for the providers module."""

from skillsmd.providers import (
    HuggingFaceProvider,
    MintlifyProvider,
    WellKnownProvider,
    ProviderRegistry,
    find_provider,
    get_providers,
)
from skillsmd.providers.base import ProviderMatch


class TestProviderMatch:
    """Tests for ProviderMatch dataclass."""

    def test_match_with_source_identifier(self):
        """Should create match with source identifier."""
        match = ProviderMatch(matches=True, source_identifier='mintlify/docs.com')
        assert match.matches is True
        assert match.source_identifier == 'mintlify/docs.com'

    def test_no_match(self):
        """Should create non-matching result."""
        match = ProviderMatch(matches=False)
        assert match.matches is False
        assert match.source_identifier is None


class TestMintlifyProviderMatch:
    """Tests for MintlifyProvider.match()."""

    def setup_method(self):
        """Set up provider instance."""
        self.provider = MintlifyProvider()

    def test_matches_skill_md_url(self):
        """Should match URL ending with /skill.md."""
        result = self.provider.match('https://docs.example.com/api/skill.md')
        assert result.matches is True
        assert result.source_identifier == 'mintlify/docs.example.com'

    def test_matches_skill_md_case_insensitive(self):
        """Should match SKILL.md case insensitive."""
        result = self.provider.match('https://docs.example.com/api/SKILL.MD')
        assert result.matches is True

    def test_does_not_match_github(self):
        """Should not match GitHub URLs."""
        result = self.provider.match('https://github.com/owner/repo/skill.md')
        assert result.matches is False

    def test_does_not_match_gitlab(self):
        """Should not match GitLab URLs."""
        result = self.provider.match('https://gitlab.com/owner/repo/skill.md')
        assert result.matches is False

    def test_does_not_match_huggingface(self):
        """Should not match HuggingFace URLs."""
        result = self.provider.match(
            'https://huggingface.co/spaces/owner/repo/skill.md'
        )
        assert result.matches is False

    def test_does_not_match_non_skill_md(self):
        """Should not match URLs not ending with skill.md."""
        result = self.provider.match('https://docs.example.com/api/readme.md')
        assert result.matches is False

    def test_does_not_match_non_http(self):
        """Should not match non-HTTP URLs."""
        result = self.provider.match('git@github.com:owner/repo.git')
        assert result.matches is False


class TestMintlifyProviderUrls:
    """Tests for MintlifyProvider URL methods."""

    def setup_method(self):
        """Set up provider instance."""
        self.provider = MintlifyProvider()

    def test_to_raw_url_returns_same(self):
        """Should return URL unchanged (Mintlify URLs are already raw)."""
        url = 'https://docs.example.com/api/skill.md'
        assert self.provider.to_raw_url(url) == url

    def test_get_source_identifier(self):
        """Should return mintlify/domain format."""
        url = 'https://docs.bun.sh/api/skill.md'
        assert self.provider.get_source_identifier(url) == 'mintlify/docs.bun.sh'


class TestHuggingFaceProviderMatch:
    """Tests for HuggingFaceProvider.match()."""

    def setup_method(self):
        """Set up provider instance."""
        self.provider = HuggingFaceProvider()

    def test_matches_spaces_skill_md(self):
        """Should match HuggingFace Spaces SKILL.md URL."""
        result = self.provider.match(
            'https://huggingface.co/spaces/owner/repo/blob/main/SKILL.md'
        )
        assert result.matches is True
        assert result.source_identifier == 'huggingface/owner/repo'

    def test_matches_skill_md_case_insensitive(self):
        """Should match skill.md case insensitive."""
        result = self.provider.match(
            'https://huggingface.co/spaces/owner/repo/blob/main/skill.md'
        )
        assert result.matches is True

    def test_does_not_match_non_spaces_url(self):
        """Should not match non-spaces HuggingFace URLs."""
        result = self.provider.match(
            'https://huggingface.co/models/owner/repo/skill.md'
        )
        assert result.matches is False

    def test_does_not_match_non_skill_md(self):
        """Should not match URLs not ending with skill.md."""
        result = self.provider.match(
            'https://huggingface.co/spaces/owner/repo/blob/main/README.md'
        )
        assert result.matches is False

    def test_does_not_match_non_huggingface(self):
        """Should not match non-HuggingFace URLs."""
        result = self.provider.match('https://example.com/spaces/owner/repo/skill.md')
        assert result.matches is False


class TestHuggingFaceProviderUrls:
    """Tests for HuggingFaceProvider URL methods."""

    def setup_method(self):
        """Set up provider instance."""
        self.provider = HuggingFaceProvider()

    def test_to_raw_url_converts_blob_to_raw(self):
        """Should convert /blob/ to /raw/ in URL."""
        url = 'https://huggingface.co/spaces/owner/repo/blob/main/SKILL.md'
        expected = 'https://huggingface.co/spaces/owner/repo/raw/main/SKILL.md'
        assert self.provider.to_raw_url(url) == expected

    def test_get_source_identifier(self):
        """Should return huggingface/owner/repo format."""
        url = 'https://huggingface.co/spaces/my-org/my-skills/blob/main/SKILL.md'
        assert (
            self.provider.get_source_identifier(url) == 'huggingface/my-org/my-skills'
        )


class TestWellKnownProviderMatch:
    """Tests for WellKnownProvider.match()."""

    def setup_method(self):
        """Set up provider instance."""
        self.provider = WellKnownProvider()

    def test_matches_http_url(self):
        """Should match HTTP URLs."""
        result = self.provider.match('https://example.com/docs')
        assert result.matches is True
        assert result.source_identifier == 'example.com'

    def test_does_not_match_github(self):
        """Should not match GitHub URLs."""
        result = self.provider.match('https://github.com/owner/repo')
        assert result.matches is False

    def test_does_not_match_gitlab(self):
        """Should not match GitLab URLs."""
        result = self.provider.match('https://gitlab.com/owner/repo')
        assert result.matches is False

    def test_does_not_match_huggingface(self):
        """Should not match HuggingFace URLs."""
        result = self.provider.match('https://huggingface.co/spaces/owner/repo')
        assert result.matches is False

    def test_does_not_match_skill_md_url(self):
        """Should not match direct SKILL.md URLs (handled by Mintlify)."""
        result = self.provider.match('https://example.com/docs/skill.md')
        assert result.matches is False

    def test_does_not_match_git_url(self):
        """Should not match .git URLs."""
        result = self.provider.match('https://example.com/repo.git')
        assert result.matches is False

    def test_does_not_match_non_http(self):
        """Should not match non-HTTP URLs."""
        result = self.provider.match('git@example.com:repo.git')
        assert result.matches is False


class TestWellKnownProviderUrls:
    """Tests for WellKnownProvider URL methods."""

    def setup_method(self):
        """Set up provider instance."""
        self.provider = WellKnownProvider()

    def test_to_raw_url_returns_same(self):
        """Should return URL unchanged."""
        url = 'https://example.com/docs'
        assert self.provider.to_raw_url(url) == url

    def test_get_source_identifier(self):
        """Should return domain as identifier."""
        url = 'https://docs.example.com/.well-known/skills'
        assert self.provider.get_source_identifier(url) == 'docs.example.com'

    def test_get_well_known_base_simple(self):
        """Should construct well-known base URL."""
        url = 'https://example.com'
        expected = 'https://example.com/.well-known/skills'
        assert self.provider._get_well_known_base(url) == expected

    def test_get_well_known_base_with_path(self):
        """Should construct well-known base URL with existing path."""
        url = 'https://example.com/docs'
        expected = 'https://example.com/docs/.well-known/skills'
        assert self.provider._get_well_known_base(url) == expected

    def test_get_well_known_base_already_has_well_known(self):
        """Should preserve existing well-known path."""
        url = 'https://example.com/.well-known/skills/my-skill'
        expected = 'https://example.com/.well-known/skills'
        assert self.provider._get_well_known_base(url) == expected


class TestProviderRegistry:
    """Tests for ProviderRegistry."""

    def test_register_provider(self):
        """Should register a provider."""
        registry = ProviderRegistry()
        provider = MintlifyProvider()
        registry.register(provider)
        assert provider in registry.get_providers()

    def test_register_duplicate_provider(self):
        """Should not register duplicate providers."""
        registry = ProviderRegistry()
        provider1 = MintlifyProvider()
        provider2 = MintlifyProvider()
        registry.register(provider1)
        registry.register(provider2)
        assert len(registry.get_providers()) == 1

    def test_find_provider_mintlify(self):
        """Should find Mintlify provider for skill.md URLs."""
        registry = ProviderRegistry()
        registry.register(MintlifyProvider())
        registry.register(HuggingFaceProvider())

        provider = registry.find_provider('https://docs.example.com/api/skill.md')
        assert provider is not None
        assert provider.id == 'mintlify'

    def test_find_provider_huggingface(self):
        """Should find HuggingFace provider for HF URLs."""
        registry = ProviderRegistry()
        registry.register(MintlifyProvider())
        registry.register(HuggingFaceProvider())

        provider = registry.find_provider(
            'https://huggingface.co/spaces/owner/repo/blob/main/skill.md'
        )
        assert provider is not None
        assert provider.id == 'huggingface'

    def test_find_provider_returns_none_for_unmatched(self):
        """Should return None for unmatched URLs."""
        registry = ProviderRegistry()
        registry.register(MintlifyProvider())

        provider = registry.find_provider('https://github.com/owner/repo')
        assert provider is None


class TestGlobalRegistry:
    """Tests for global registry functions."""

    def test_find_provider_huggingface(self):
        """Should find HuggingFace provider in global registry."""
        provider = find_provider(
            'https://huggingface.co/spaces/owner/repo/blob/main/skill.md'
        )
        assert provider is not None
        assert provider.id == 'huggingface'

    def test_find_provider_mintlify(self):
        """Should find Mintlify provider in global registry."""
        provider = find_provider('https://docs.example.com/api/skill.md')
        assert provider is not None
        assert provider.id == 'mintlify'

    def test_get_providers_includes_builtin(self):
        """Should include built-in providers."""
        providers = get_providers()
        provider_ids = [p.id for p in providers]
        assert 'huggingface' in provider_ids
        assert 'mintlify' in provider_ids


class TestProviderProperties:
    """Tests for provider property methods."""

    def test_mintlify_id(self):
        """Should return correct ID for Mintlify."""
        assert MintlifyProvider().id == 'mintlify'

    def test_mintlify_display_name(self):
        """Should return correct display name for Mintlify."""
        assert MintlifyProvider().display_name == 'Mintlify'

    def test_huggingface_id(self):
        """Should return correct ID for HuggingFace."""
        assert HuggingFaceProvider().id == 'huggingface'

    def test_huggingface_display_name(self):
        """Should return correct display name for HuggingFace."""
        assert HuggingFaceProvider().display_name == 'HuggingFace'

    def test_wellknown_id(self):
        """Should return correct ID for Well-Known."""
        assert WellKnownProvider().id == 'well-known'

    def test_wellknown_display_name(self):
        """Should return correct display name for Well-Known."""
        assert WellKnownProvider().display_name == 'Well-Known Skills'
