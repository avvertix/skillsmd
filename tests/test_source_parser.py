"""Unit tests for source_parser.py.

These tests verify the URL parsing logic - they don't make network requests
or clone repositories. They ensure that given a URL string, the parser
correctly extracts type, url, ref (branch), and subpath.
"""

import sys


from skillsmd.source_parser import parse_source, get_owner_repo

is_windows = sys.platform == 'win32'


class TestGitHubURLTests:
    """GitHub URL tests."""

    def test_github_url_basic_repo(self):
        """Should parse basic GitHub repo URL."""
        result = parse_source('https://github.com/owner/repo')
        assert result.type == 'github'
        assert result.url == 'https://github.com/owner/repo.git'
        assert result.ref is None
        assert result.subpath is None

    def test_github_url_with_git_suffix(self):
        """Should parse GitHub URL with .git suffix."""
        result = parse_source('https://github.com/owner/repo.git')
        assert result.type == 'github'
        assert result.url == 'https://github.com/owner/repo.git'

    def test_github_url_tree_with_branch_only(self):
        """Should parse GitHub URL with tree/branch."""
        result = parse_source('https://github.com/owner/repo/tree/feature-branch')
        assert result.type == 'github'
        assert result.url == 'https://github.com/owner/repo.git'
        assert result.ref == 'feature-branch'
        assert result.subpath is None

    def test_github_url_tree_with_branch_and_path(self):
        """Should parse GitHub URL with tree/branch/path."""
        result = parse_source('https://github.com/owner/repo/tree/main/skills/my-skill')
        assert result.type == 'github'
        assert result.url == 'https://github.com/owner/repo.git'
        assert result.ref == 'main'
        assert result.subpath == 'skills/my-skill'

    def test_github_url_tree_with_slash_in_path(self):
        """Should handle ambiguous branch/path with slash."""
        # Note: Branch names with slashes are ambiguous.
        # The parser treats the first segment as branch and rest as path.
        result = parse_source('https://github.com/owner/repo/tree/feature/my-feature')
        assert result.type == 'github'
        assert result.url == 'https://github.com/owner/repo.git'
        assert result.ref == 'feature'
        assert result.subpath == 'my-feature'


class TestGitLabURLTests:
    """GitLab URL tests."""

    def test_gitlab_url_basic_repo(self):
        """Should parse basic GitLab repo URL."""
        result = parse_source('https://gitlab.com/owner/repo')
        assert result.type == 'gitlab'
        assert result.url == 'https://gitlab.com/owner/repo.git'
        assert result.ref is None

    def test_gitlab_url_tree_with_branch_only(self):
        """Should parse GitLab URL with tree/branch."""
        result = parse_source('https://gitlab.com/owner/repo/-/tree/develop')
        assert result.type == 'gitlab'
        assert result.url == 'https://gitlab.com/owner/repo.git'
        assert result.ref == 'develop'
        assert result.subpath is None

    def test_gitlab_url_tree_with_branch_and_path(self):
        """Should parse GitLab URL with tree/branch/path."""
        result = parse_source('https://gitlab.com/owner/repo/-/tree/main/src/skills')
        assert result.type == 'gitlab'
        assert result.url == 'https://gitlab.com/owner/repo.git'
        assert result.ref == 'main'
        assert result.subpath == 'src/skills'


class TestGitHubShorthandTests:
    """GitHub shorthand tests."""

    def test_github_shorthand_owner_repo(self):
        """Should parse owner/repo shorthand."""
        result = parse_source('owner/repo')
        assert result.type == 'github'
        assert result.url == 'https://github.com/owner/repo.git'
        assert result.ref is None
        assert result.subpath is None

    def test_github_shorthand_owner_repo_path(self):
        """Should parse owner/repo/path shorthand."""
        result = parse_source('owner/repo/skills/my-skill')
        assert result.type == 'github'
        assert result.url == 'https://github.com/owner/repo.git'
        assert result.subpath == 'skills/my-skill'

    def test_github_shorthand_owner_repo_at_skill(self):
        """Should parse owner/repo@skill filter syntax."""
        result = parse_source('owner/repo@my-skill')
        assert result.type == 'github'
        assert result.url == 'https://github.com/owner/repo.git'
        assert result.skill_filter == 'my-skill'
        assert result.subpath is None

    def test_github_shorthand_with_hyphenated_skill_name(self):
        """Should parse shorthand with hyphenated skill name."""
        result = parse_source('vercel-labs/agent-skills@find-skills')
        assert result.type == 'github'
        assert result.url == 'https://github.com/vercel-labs/agent-skills.git'
        assert result.skill_filter == 'find-skills'


class TestLocalPathTests:
    """Local path tests."""

    def test_local_path_relative_with_dot_slash(self):
        """Should parse relative path with ./."""
        result = parse_source('./my-skills')
        assert result.type == 'local'
        assert 'my-skills' in result.local_path

    def test_local_path_relative_with_parent(self):
        """Should parse relative path with ../."""
        result = parse_source('../other-skills')
        assert result.type == 'local'
        assert 'other-skills' in result.local_path

    def test_local_path_current_directory(self):
        """Should parse current directory."""
        result = parse_source('.')
        assert result.type == 'local'
        assert result.local_path is not None

    def test_local_path_absolute(self):
        """Should parse absolute path."""
        if is_windows:
            test_path = 'C:\\Users\\test\\skills'
        else:
            test_path = '/home/user/skills'
        result = parse_source(test_path)
        assert result.type == 'local'
        assert result.local_path == test_path


class TestGitURLFallbackTests:
    """Git URL fallback tests."""

    def test_git_url_ssh_format(self):
        """Should parse SSH git URL."""
        result = parse_source('git@github.com:owner/repo.git')
        assert result.type == 'git'
        assert result.url == 'git@github.com:owner/repo.git'

    def test_git_url_custom_host(self):
        """Should parse custom host git URL."""
        result = parse_source('https://git.example.com/owner/repo.git')
        assert result.type == 'git'
        assert result.url == 'https://git.example.com/owner/repo.git'


class TestGetOwnerRepo:
    """Tests for get_owner_repo function."""

    def test_github_url(self):
        """Should extract owner/repo from GitHub URL."""
        parsed = parse_source('https://github.com/owner/repo')
        assert get_owner_repo(parsed) == 'owner/repo'

    def test_github_url_with_git(self):
        """Should extract owner/repo from GitHub URL with .git."""
        parsed = parse_source('https://github.com/owner/repo.git')
        assert get_owner_repo(parsed) == 'owner/repo'

    def test_github_url_with_tree_branch_path(self):
        """Should extract owner/repo from GitHub tree URL."""
        parsed = parse_source('https://github.com/owner/repo/tree/main/skills/my-skill')
        assert get_owner_repo(parsed) == 'owner/repo'

    def test_github_shorthand(self):
        """Should extract owner/repo from shorthand."""
        parsed = parse_source('owner/repo')
        assert get_owner_repo(parsed) == 'owner/repo'

    def test_github_shorthand_with_subpath(self):
        """Should extract owner/repo from shorthand with subpath."""
        parsed = parse_source('owner/repo/skills/my-skill')
        assert get_owner_repo(parsed) == 'owner/repo'

    def test_gitlab_url(self):
        """Should extract owner/repo from GitLab URL."""
        parsed = parse_source('https://gitlab.com/owner/repo')
        assert get_owner_repo(parsed) == 'owner/repo'

    def test_gitlab_url_with_tree(self):
        """Should extract owner/repo from GitLab tree URL."""
        parsed = parse_source('https://gitlab.com/owner/repo/-/tree/main/skills')
        assert get_owner_repo(parsed) == 'owner/repo'

    def test_local_path_returns_none(self):
        """Should return None for local path."""
        parsed = parse_source('./my-skills')
        assert get_owner_repo(parsed) is None

    def test_absolute_local_path_returns_none(self):
        """Should return None for absolute local path."""
        parsed = parse_source('/home/user/skills')
        assert get_owner_repo(parsed) is None

    def test_custom_git_host_returns_none(self):
        """Should return None for custom git host."""
        parsed = parse_source('https://git.example.com/owner/repo.git')
        assert get_owner_repo(parsed) is None

    def test_ssh_format_returns_none(self):
        """Should return None for SSH format."""
        parsed = parse_source('git@github.com:owner/repo.git')
        assert get_owner_repo(parsed) is None
