"""Unit tests for filter_skills function in skills.py.

These tests verify the skill matching logic. Multi-word skill names
must be quoted on the command line (e.g., --skill "Convex Best Practices").
"""

from skillsmd.skills import filter_skills
from skillsmd.types import Skill


def make_skill(name: str, path: str = '/tmp/skill') -> Skill:
    """Mock skill factory."""
    return Skill(name=name, description='desc', path=path)


# Test fixtures
skills = [
    make_skill('convex-best-practices'),
    make_skill('Convex Best Practices'),
    make_skill('simple-skill'),
    make_skill('foo'),
    make_skill('bar'),
]


class TestDirectMatching:
    """Direct matching tests."""

    def test_matches_exact_name(self):
        """Should match exact name."""
        result = filter_skills(skills, ['foo'])
        assert len(result) == 1
        assert result[0].name == 'foo'

    def test_matches_case_insensitive(self):
        """Should match case insensitive."""
        result = filter_skills(skills, ['FOO'])
        assert len(result) == 1
        assert result[0].name == 'foo'

    def test_matches_kebab_case_skill_name(self):
        """Should match kebab-case skill name."""
        result = filter_skills(skills, ['convex-best-practices'])
        assert len(result) == 1
        assert result[0].name == 'convex-best-practices'

    def test_matches_multiple_skills(self):
        """Should match multiple skills."""
        result = filter_skills(skills, ['foo', 'bar'])
        assert len(result) == 2
        names = sorted([s.name for s in result])
        assert names == ['bar', 'foo']


class TestQuotedMultiWordNames:
    """Quoted multi-word names tests."""

    def test_matches_quoted_multi_word_name(self):
        """Should match quoted multi-word name (simulates: --skill "Convex Best Practices")."""
        result = filter_skills(skills, ['Convex Best Practices'])
        assert len(result) == 1
        assert result[0].name == 'Convex Best Practices'

    def test_matches_quoted_multi_word_name_case_insensitive(self):
        """Should match quoted multi-word name case insensitive."""
        result = filter_skills(skills, ['convex best practices'])
        assert len(result) == 1
        assert result[0].name == 'Convex Best Practices'


class TestUnquotedMultiWordNames:
    """Unquoted multi-word names tests (should not match)."""

    def test_does_not_match_unquoted_multi_word_args(self):
        """Should not match unquoted multi-word args (shell splits into 3 args)."""
        # Simulates: --skill Convex Best Practices (unquoted)
        # This should NOT match - users must quote multi-word names
        result = filter_skills(skills, ['Convex', 'Best', 'Practices'])
        assert len(result) == 0

    def test_does_not_match_partial_words(self):
        """Should not match partial words."""
        result = filter_skills(skills, ['Convex', 'Best'])
        assert len(result) == 0


class TestNoMatches:
    """No matches tests."""

    def test_returns_empty_array_when_no_matches(self):
        """Should return empty list when no matches."""
        result = filter_skills(skills, ['nonexistent'])
        assert len(result) == 0

    def test_returns_empty_array_for_empty_input(self):
        """Should return empty list for empty input."""
        result = filter_skills(skills, [])
        assert len(result) == 0
