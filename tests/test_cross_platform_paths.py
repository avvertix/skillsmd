"""Cross-platform path handling tests.

These tests verify that path operations work correctly on both Unix and Windows.
They test the actual logic used in the codebase for path manipulation.
"""

import os


def shorten_path(full_path: str, cwd: str, home: str, path_sep: str) -> str:
    """Simulate the shorten_path function from add.py (cross-platform version)."""
    # Ensure we match complete path segments by checking for separator after the prefix
    if full_path == home or full_path.startswith(home + path_sep):
        return '~' + full_path[len(home) :]
    if full_path == cwd or full_path.startswith(cwd + path_sep):
        return '.' + full_path[len(cwd) :]
    return full_path


def is_valid_skill_file(file: str) -> bool:
    """Simulate the path validation from wellknown.ts.

    Note: The actual validation uses simple `includes('..')` which will match
    filenames like '...dots'. This is intentional - it's stricter security.
    """
    if not isinstance(file, str):
        return False
    # Files must not start with / or \ or contain .. (path traversal prevention)
    if file.startswith('/') or file.startswith('\\') or '..' in file:
        return False
    return True


def normalize_skill_path(skill_path: str) -> str:
    """Simulate the SKILL.md path normalization from skill-lock.ts."""
    folder_path = skill_path

    # Handle both forward and backslash separators for cross-platform compatibility
    if folder_path.endswith('/SKILL.md') or folder_path.endswith('\\SKILL.md'):
        folder_path = folder_path[:-9]
    elif folder_path.endswith('SKILL.md'):
        folder_path = folder_path[:-8]

    if folder_path.endswith('/') or folder_path.endswith('\\'):
        folder_path = folder_path[:-1]

    # Convert to forward slashes for GitHub API
    return folder_path.replace('\\', '/')


def calculate_relative_path(
    temp_dir: str | None, skill_path: str, path_sep: str = os.sep
) -> str | None:
    """Simulate the relativePath calculation from add.ts (cross-platform version)."""
    if temp_dir and skill_path == temp_dir:
        # Skill is at root level of repo
        return 'SKILL.md'
    elif temp_dir and skill_path.startswith(temp_dir + path_sep):
        # Compute path relative to repo root (temp_dir)
        # Use forward slashes for telemetry (URL-style paths)
        relative = skill_path[len(temp_dir) + 1 :].replace(path_sep, '/')
        return f'{relative}/SKILL.md'
    else:
        # Local path - skip telemetry
        return None


class TestShortenPathUnix:
    """Unix path shortening tests."""

    path_sep = '/'
    home = '/Users/test'
    cwd = '/Users/test/projects/myproject'

    def test_replaces_home_directory_with_tilde(self):
        """Should replace home directory with ~."""
        result = shorten_path(
            '/Users/test/documents/file.txt', self.cwd, self.home, self.path_sep
        )
        assert result == '~/documents/file.txt'

    def test_prefers_home_over_cwd_when_cwd_is_under_home(self):
        """Should prefer home over cwd when cwd is under home."""
        # When cwd is under home, home is checked first and matches
        # This is the expected behavior - displays as ~/projects/myproject/...
        result = shorten_path(
            '/Users/test/projects/myproject/src/file.ts',
            self.cwd,
            self.home,
            self.path_sep,
        )
        assert result == '~/projects/myproject/src/file.ts'

    def test_replaces_cwd_with_dot_when_cwd_is_not_under_home(self):
        """Should replace cwd with . when cwd is not under home."""
        # When cwd is outside home, cwd can match
        outside_home = '/var/www/myproject'
        result = shorten_path(
            '/var/www/myproject/src/file.ts', outside_home, self.home, self.path_sep
        )
        assert result == './src/file.ts'

    def test_returns_path_unchanged_if_not_under_home_or_cwd(self):
        """Should return path unchanged if not under home or cwd."""
        result = shorten_path('/var/log/system.log', self.cwd, self.home, self.path_sep)
        assert result == '/var/log/system.log'

    def test_handles_exact_home_directory_match(self):
        """Should handle exact home directory match."""
        result = shorten_path('/Users/test', self.cwd, self.home, self.path_sep)
        assert result == '~'

    def test_handles_exact_cwd_match_when_cwd_is_under_home(self):
        """Should handle exact cwd match when cwd is under home."""
        # Since cwd is under home, home matches first
        result = shorten_path(
            '/Users/test/projects/myproject', self.cwd, self.home, self.path_sep
        )
        assert result == '~/projects/myproject'

    def test_handles_exact_cwd_match_when_cwd_is_outside_home(self):
        """Should handle exact cwd match when cwd is outside home."""
        outside_home = '/var/www/myproject'
        result = shorten_path(
            '/var/www/myproject', outside_home, self.home, self.path_sep
        )
        assert result == '.'

    def test_does_not_match_partial_directory_names_home(self):
        """Should not match partial directory names (home)."""
        # /Users/tester should NOT match /Users/test
        result = shorten_path(
            '/Users/tester/file.txt', self.cwd, self.home, self.path_sep
        )
        assert result == '/Users/tester/file.txt'

    def test_does_not_match_partial_directory_names_cwd(self):
        """Should not match partial directory names (cwd)."""
        # /Users/test/projects/myproject2 should NOT match /Users/test/projects/myproject
        result = shorten_path(
            '/Users/test/projects/myproject2/file.txt',
            self.cwd,
            self.home,
            self.path_sep,
        )
        # It should still match home though
        assert result == '~/projects/myproject2/file.txt'


class TestShortenPathWindows:
    """Windows path shortening tests."""

    path_sep = '\\'
    home = 'C:\\Users\\test'
    cwd = 'C:\\Users\\test\\projects\\myproject'

    def test_replaces_home_directory_with_tilde(self):
        """Should replace home directory with ~."""
        result = shorten_path(
            'C:\\Users\\test\\documents\\file.txt', self.cwd, self.home, self.path_sep
        )
        assert result == '~\\documents\\file.txt'

    def test_prefers_home_over_cwd_when_cwd_is_under_home(self):
        """Should prefer home over cwd when cwd is under home."""
        # When cwd is under home, home is checked first and matches
        result = shorten_path(
            'C:\\Users\\test\\projects\\myproject\\src\\file.ts',
            self.cwd,
            self.home,
            self.path_sep,
        )
        assert result == '~\\projects\\myproject\\src\\file.ts'

    def test_replaces_cwd_with_dot_when_cwd_is_not_under_home(self):
        """Should replace cwd with . when cwd is not under home."""
        # When cwd is outside home, cwd can match
        outside_home = 'D:\\projects\\myproject'
        result = shorten_path(
            'D:\\projects\\myproject\\src\\file.ts',
            outside_home,
            self.home,
            self.path_sep,
        )
        assert result == '.\\src\\file.ts'

    def test_returns_path_unchanged_if_not_under_home_or_cwd(self):
        """Should return path unchanged if not under home or cwd."""
        result = shorten_path(
            'D:\\logs\\system.log', self.cwd, self.home, self.path_sep
        )
        assert result == 'D:\\logs\\system.log'

    def test_handles_exact_home_directory_match(self):
        """Should handle exact home directory match."""
        result = shorten_path('C:\\Users\\test', self.cwd, self.home, self.path_sep)
        assert result == '~'

    def test_handles_exact_cwd_match_when_cwd_is_under_home(self):
        """Should handle exact cwd match when cwd is under home."""
        # Since cwd is under home, home matches first
        result = shorten_path(
            'C:\\Users\\test\\projects\\myproject', self.cwd, self.home, self.path_sep
        )
        assert result == '~\\projects\\myproject'

    def test_handles_exact_cwd_match_when_cwd_is_outside_home(self):
        """Should handle exact cwd match when cwd is outside home."""
        outside_home = 'D:\\projects\\myproject'
        result = shorten_path(
            'D:\\projects\\myproject', outside_home, self.home, self.path_sep
        )
        assert result == '.'

    def test_does_not_match_partial_directory_names_home(self):
        """Should not match partial directory names (home)."""
        # C:\Users\tester should NOT match C:\Users\test
        result = shorten_path(
            'C:\\Users\\tester\\file.txt', self.cwd, self.home, self.path_sep
        )
        assert result == 'C:\\Users\\tester\\file.txt'


class TestIsValidSkillFile:
    """Tests for skill file path validation."""

    def test_accepts_valid_relative_paths(self):
        """Should accept valid relative paths."""
        assert is_valid_skill_file('SKILL.md') is True
        assert is_valid_skill_file('src/helper.ts') is True
        assert is_valid_skill_file('assets/logo.png') is True

    def test_rejects_paths_starting_with_forward_slash(self):
        """Should reject paths starting with forward slash."""
        assert is_valid_skill_file('/etc/passwd') is False
        assert is_valid_skill_file('/SKILL.md') is False

    def test_rejects_paths_starting_with_backslash(self):
        """Should reject paths starting with backslash."""
        assert is_valid_skill_file('\\Windows\\System32') is False
        assert is_valid_skill_file('\\SKILL.md') is False

    def test_rejects_paths_with_directory_traversal(self):
        """Should reject paths with directory traversal."""
        assert is_valid_skill_file('../../../etc/passwd') is False
        assert is_valid_skill_file('foo/../../../etc/passwd') is False
        assert is_valid_skill_file('..\\..\\Windows\\System32') is False

    def test_allows_dots_in_filenames(self):
        """Should allow dots in filenames (not traversal)."""
        assert is_valid_skill_file('file.name.txt') is True
        assert is_valid_skill_file('.hidden') is True
        # Note: '...dots' contains '..' which is rejected for security
        assert is_valid_skill_file('.config') is True

    def test_rejects_filenames_containing_double_dots(self):
        """Should reject filenames containing .. (strict security)."""
        # Even innocent-looking filenames with .. are rejected for security
        assert is_valid_skill_file('...dots') is False
        assert is_valid_skill_file('file..name') is False


class TestNormalizeSkillPath:
    """Tests for skill path normalization."""

    def test_removes_skill_md_suffix_unix(self):
        """Should remove /SKILL.md suffix (Unix)."""
        result = normalize_skill_path('skills/my-skill/SKILL.md')
        assert result == 'skills/my-skill'

    def test_removes_skill_md_suffix_windows(self):
        """Should remove \\SKILL.md suffix (Windows)."""
        result = normalize_skill_path('skills\\my-skill\\SKILL.md')
        assert result == 'skills/my-skill'

    def test_removes_skill_md_without_path_separator(self):
        """Should remove SKILL.md without path separator."""
        result = normalize_skill_path('SKILL.md')
        assert result == ''

    def test_removes_trailing_forward_slash(self):
        """Should remove trailing forward slash."""
        result = normalize_skill_path('skills/my-skill/')
        assert result == 'skills/my-skill'

    def test_removes_trailing_backslash(self):
        """Should remove trailing backslash."""
        result = normalize_skill_path('skills\\my-skill\\')
        assert result == 'skills/my-skill'

    def test_converts_windows_paths_to_forward_slashes(self):
        """Should convert Windows paths to forward slashes."""
        result = normalize_skill_path('skills\\.curated\\advanced-skill\\SKILL.md')
        assert result == 'skills/.curated/advanced-skill'

    def test_handles_mixed_separators(self):
        """Should handle mixed separators."""
        result = normalize_skill_path('skills/category\\my-skill/SKILL.md')
        assert result == 'skills/category/my-skill'

    def test_handles_root_level_skill(self):
        """Should handle root-level skill."""
        result = normalize_skill_path('/SKILL.md')
        assert result == ''

    def test_handles_deep_nested_paths_windows(self):
        """Should handle deep nested paths (Windows)."""
        result = normalize_skill_path('a\\b\\c\\d\\e\\SKILL.md')
        assert result == 'a/b/c/d/e'


class TestCalculateRelativePathUnix:
    """Tests for relative path calculation (Unix paths)."""

    unix_sep = '/'

    def test_skill_at_repo_root(self):
        """Should return SKILL.md for skill at repo root."""
        temp_dir = '/tmp/abc123'
        skill_path = '/tmp/abc123'
        result = calculate_relative_path(temp_dir, skill_path, self.unix_sep)
        assert result == 'SKILL.md'

    def test_skill_in_skills_subdirectory(self):
        """Should return correct path for skill in skills/ subdirectory."""
        temp_dir = '/tmp/abc123'
        skill_path = '/tmp/abc123/skills/my-skill'
        result = calculate_relative_path(temp_dir, skill_path, self.unix_sep)
        assert result == 'skills/my-skill/SKILL.md'

    def test_skill_in_claude_skills_directory(self):
        """Should return correct path for skill in .claude/skills/ directory."""
        temp_dir = '/tmp/abc123'
        skill_path = '/tmp/abc123/.claude/skills/my-skill'
        result = calculate_relative_path(temp_dir, skill_path, self.unix_sep)
        assert result == '.claude/skills/my-skill/SKILL.md'

    def test_skill_in_nested_subdirectory(self):
        """Should return correct path for skill in nested subdirectory."""
        temp_dir = '/tmp/abc123'
        skill_path = '/tmp/abc123/skills/.curated/advanced-skill'
        result = calculate_relative_path(temp_dir, skill_path, self.unix_sep)
        assert result == 'skills/.curated/advanced-skill/SKILL.md'

    def test_local_path_returns_none(self):
        """Should return None for local path."""
        temp_dir = None
        skill_path = '/Users/me/projects/my-skill'
        result = calculate_relative_path(temp_dir, skill_path, self.unix_sep)
        assert result is None

    def test_path_not_under_temp_dir_returns_none(self):
        """Should return None for path not under temp_dir."""
        temp_dir = '/tmp/abc123'
        skill_path = '/tmp/other/my-skill'
        result = calculate_relative_path(temp_dir, skill_path, self.unix_sep)
        assert result is None

    def test_onmax_nuxt_skills_ts_library(self):
        """Should handle onmax/nuxt-skills: skill in skills/ts-library."""
        temp_dir = '/tmp/clone-xyz'
        # discoverSkills finds /tmp/clone-xyz/skills/ts-library/SKILL.md
        # skill.path = dirname(skillMdPath) = /tmp/clone-xyz/skills/ts-library
        skill_path = '/tmp/clone-xyz/skills/ts-library'
        result = calculate_relative_path(temp_dir, skill_path, self.unix_sep)
        assert result == 'skills/ts-library/SKILL.md'


class TestCalculateRelativePathWindows:
    """Tests for relative path calculation (Windows paths)."""

    def test_skill_at_repo_root_windows(self):
        """Should return SKILL.md for skill at repo root (Windows)."""
        temp_dir = 'C:\\Users\\test\\AppData\\Local\\Temp\\abc123'
        skill_path = 'C:\\Users\\test\\AppData\\Local\\Temp\\abc123'
        result = calculate_relative_path(temp_dir, skill_path, '\\')
        assert result == 'SKILL.md'

    def test_skill_in_skills_subdirectory_windows(self):
        """Should return correct path for skill in skills\\ subdirectory (Windows)."""
        temp_dir = 'C:\\Users\\test\\AppData\\Local\\Temp\\abc123'
        skill_path = 'C:\\Users\\test\\AppData\\Local\\Temp\\abc123\\skills\\my-skill'
        result = calculate_relative_path(temp_dir, skill_path, '\\')
        assert result == 'skills/my-skill/SKILL.md'

    def test_skill_in_claude_skills_directory_windows(self):
        """Should return correct path for skill in .claude\\skills\\ directory (Windows)."""
        temp_dir = 'C:\\Users\\test\\AppData\\Local\\Temp\\abc123'
        skill_path = (
            'C:\\Users\\test\\AppData\\Local\\Temp\\abc123\\.claude\\skills\\my-skill'
        )
        result = calculate_relative_path(temp_dir, skill_path, '\\')
        assert result == '.claude/skills/my-skill/SKILL.md'

    def test_skill_in_nested_subdirectory_windows(self):
        """Should return correct path for skill in nested subdirectory (Windows)."""
        temp_dir = 'C:\\Users\\test\\AppData\\Local\\Temp\\abc123'
        skill_path = 'C:\\Users\\test\\AppData\\Local\\Temp\\abc123\\skills\\.curated\\advanced-skill'
        result = calculate_relative_path(temp_dir, skill_path, '\\')
        assert result == 'skills/.curated/advanced-skill/SKILL.md'

    def test_path_not_under_temp_dir_returns_none_windows(self):
        """Should return None for path not under temp_dir (Windows)."""
        temp_dir = 'C:\\Users\\test\\AppData\\Local\\Temp\\abc123'
        skill_path = 'C:\\Users\\test\\AppData\\Local\\Temp\\other\\my-skill'
        result = calculate_relative_path(temp_dir, skill_path, '\\')
        assert result is None

    def test_handles_similar_path_prefixes_correctly_windows(self):
        """Should handle similar path prefixes correctly (Windows)."""
        # This tests that we don't match partial directory names
        temp_dir = 'C:\\Users\\test\\AppData\\Local\\Temp\\abc'
        skill_path = 'C:\\Users\\test\\AppData\\Local\\Temp\\abc123\\skills\\my-skill'
        result = calculate_relative_path(temp_dir, skill_path, '\\')
        assert result is None


class TestPlatformDetection:
    """Platform detection tests."""

    def test_sep_is_correct_for_current_platform(self):
        """os.sep should be correct for current platform."""
        # This will be '/' on Unix/Mac and '\\' on Windows
        assert os.sep in ['/', '\\']
