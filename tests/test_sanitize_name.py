"""Unit tests for sanitize_name function in installer.py.

These tests verify the sanitization logic for skill names to ensure:
- Path traversal attacks are prevented
- Names follow kebab-case convention
- Special characters are handled safely
"""

from skillsmd.installer import sanitize_name


class TestBasicTransformations:
    """Basic transformation tests."""

    def test_converts_to_lowercase(self):
        """Should convert names to lowercase."""
        assert sanitize_name('MySkill') == 'myskill'
        assert sanitize_name('UPPERCASE') == 'uppercase'

    def test_replaces_spaces_with_hyphens(self):
        """Should replace spaces with hyphens."""
        assert sanitize_name('my skill') == 'my-skill'
        assert sanitize_name('Convex Best Practices') == 'convex-best-practices'

    def test_replaces_multiple_spaces_with_single_hyphen(self):
        """Should replace multiple spaces with single hyphen."""
        assert sanitize_name('my   skill') == 'my-skill'

    def test_preserves_dots_and_underscores(self):
        """Should preserve dots and underscores."""
        assert sanitize_name('bun.sh') == 'bun.sh'
        assert sanitize_name('my_skill') == 'my_skill'
        assert sanitize_name('skill.v2_beta') == 'skill.v2_beta'

    def test_preserves_numbers(self):
        """Should preserve numbers."""
        assert sanitize_name('skill123') == 'skill123'
        assert sanitize_name('v2.0') == 'v2.0'


class TestSpecialCharacterHandling:
    """Special character handling tests."""

    def test_replaces_special_characters_with_hyphens(self):
        """Should replace special characters with hyphens."""
        assert sanitize_name('skill@name') == 'skill-name'
        assert sanitize_name('skill#name') == 'skill-name'
        assert sanitize_name('skill$name') == 'skill-name'
        assert sanitize_name('skill!name') == 'skill-name'

    def test_collapses_multiple_special_chars_into_single_hyphen(self):
        """Should collapse multiple special chars into single hyphen."""
        assert sanitize_name('skill@#$name') == 'skill-name'
        assert sanitize_name('a!!!b') == 'a-b'


class TestPathTraversalPrevention:
    """Path traversal prevention tests."""

    def test_prevents_path_traversal_with_dot_slash(self):
        """Should prevent path traversal with ../."""
        assert sanitize_name('../etc/passwd') == 'etc-passwd'
        assert sanitize_name('../../secret') == 'secret'

    def test_prevents_path_traversal_with_backslashes(self):
        """Should prevent path traversal with backslashes."""
        assert sanitize_name('..\\..\\secret') == 'secret'

    def test_handles_absolute_paths(self):
        """Should handle absolute paths."""
        assert sanitize_name('/etc/passwd') == 'etc-passwd'
        assert sanitize_name('C:\\Windows\\System32') == 'c-windows-system32'


class TestLeadingTrailingCleanup:
    """Leading/trailing cleanup tests."""

    def test_removes_leading_dots(self):
        """Should remove leading dots."""
        assert sanitize_name('.hidden') == 'hidden'
        assert sanitize_name('..hidden') == 'hidden'
        assert sanitize_name('...skill') == 'skill'

    def test_removes_trailing_dots(self):
        """Should remove trailing dots."""
        assert sanitize_name('skill.') == 'skill'
        assert sanitize_name('skill..') == 'skill'

    def test_removes_leading_hyphens(self):
        """Should remove leading hyphens."""
        assert sanitize_name('-skill') == 'skill'
        assert sanitize_name('--skill') == 'skill'

    def test_removes_trailing_hyphens(self):
        """Should remove trailing hyphens."""
        assert sanitize_name('skill-') == 'skill'
        assert sanitize_name('skill--') == 'skill'

    def test_removes_mixed_leading_dots_and_hyphens(self):
        """Should remove mixed leading dots and hyphens."""
        assert sanitize_name('.-.-skill') == 'skill'
        assert sanitize_name('-.-.skill') == 'skill'


class TestEdgeCases:
    """Edge case tests."""

    def test_returns_unnamed_skill_for_empty_string(self):
        """Should return unnamed-skill for empty string."""
        assert sanitize_name('') == 'unnamed-skill'

    def test_returns_unnamed_skill_when_only_special_chars(self):
        """Should return unnamed-skill when only special chars."""
        assert sanitize_name('...') == 'unnamed-skill'
        assert sanitize_name('---') == 'unnamed-skill'
        assert sanitize_name('@#$%') == 'unnamed-skill'

    def test_handles_very_long_names(self):
        """Should truncate very long names to 255 chars."""
        long_name = 'a' * 300
        result = sanitize_name(long_name)
        assert len(result) == 255
        assert result == 'a' * 255

    def test_handles_unicode_characters(self):
        """Should handle unicode characters."""
        # Unicode gets stripped, leaving just ASCII
        assert sanitize_name('skill日本語') == 'skill'
        # Emoji and accented chars get replaced with hyphens
        result = sanitize_name('émoji🎉skill')
        assert 'skill' in result


class TestRealWorldExamples:
    """Real-world example tests."""

    def test_handles_github_repo_style_names(self):
        """Should handle GitHub repo style names."""
        assert sanitize_name('vercel/next.js') == 'vercel-next.js'
        assert sanitize_name('owner/repo-name') == 'owner-repo-name'

    def test_handles_urls(self):
        """Should handle URLs."""
        assert sanitize_name('https://example.com') == 'https-example.com'

    def test_handles_mintlify_style_names(self):
        """Should handle mintlify style names."""
        assert sanitize_name('docs.example.com') == 'docs.example.com'
        assert sanitize_name('bun.sh') == 'bun.sh'
