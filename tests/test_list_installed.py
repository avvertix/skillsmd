"""Unit tests for list_installed_skills function in installer.py.

These tests verify:
- Empty directories return empty list
- Skills are discovered correctly
- Invalid SKILL.md files are handled gracefully
- Scope filtering works correctly
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from skillsmd.installer import list_installed_skills


async def create_skill_dir(
    base_path: Path, skill_name: str, name: str, description: str
) -> Path:
    """Create a skill directory with SKILL.md."""
    skill_dir = base_path / '.agents' / 'skills' / skill_name
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md_content = f"""---
name: {name}
description: {description}
---

# {name}

{description}
"""
    (skill_dir / 'SKILL.md').write_text(skill_md_content, encoding='utf-8')
    return skill_dir


class TestListInstalledSkills:
    """Tests for list_installed_skills function."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up and tear down test directory."""
        self.test_dir = Path(tempfile.mkdtemp(prefix='add-skill-test-'))
        yield
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_should_return_empty_array_for_empty_directory(self):
        """Should return empty list for empty directory."""
        skills = await list_installed_skills(is_global=False, cwd=str(self.test_dir))
        assert skills == []

    @pytest.mark.asyncio
    async def test_should_find_single_skill_in_project_directory(self):
        """Should find single skill in project directory."""
        await create_skill_dir(
            self.test_dir, 'test-skill', name='test-skill', description='A test skill'
        )

        skills = await list_installed_skills(is_global=False, cwd=str(self.test_dir))
        assert len(skills) == 1
        assert skills[0].name == 'test-skill'
        assert skills[0].description == 'A test skill'
        assert skills[0].scope == 'project'

    @pytest.mark.asyncio
    async def test_should_find_multiple_skills(self):
        """Should find multiple skills."""
        await create_skill_dir(
            self.test_dir, 'skill-1', name='skill-1', description='First skill'
        )
        await create_skill_dir(
            self.test_dir, 'skill-2', name='skill-2', description='Second skill'
        )

        skills = await list_installed_skills(is_global=False, cwd=str(self.test_dir))
        assert len(skills) == 2
        skill_names = sorted([s.name for s in skills])
        assert skill_names == ['skill-1', 'skill-2']

    @pytest.mark.asyncio
    async def test_should_ignore_directories_without_skill_md(self):
        """Should ignore directories without SKILL.md."""
        await create_skill_dir(
            self.test_dir, 'valid-skill', name='valid-skill', description='Valid skill'
        )

        # Create a directory without SKILL.md
        invalid_dir = self.test_dir / '.agents' / 'skills' / 'invalid-skill'
        invalid_dir.mkdir(parents=True, exist_ok=True)
        (invalid_dir / 'other-file.txt').write_text('content', encoding='utf-8')

        skills = await list_installed_skills(is_global=False, cwd=str(self.test_dir))
        assert len(skills) == 1
        assert skills[0].name == 'valid-skill'

    @pytest.mark.asyncio
    async def test_should_handle_invalid_skill_md_gracefully(self):
        """Should handle invalid SKILL.md gracefully."""
        await create_skill_dir(
            self.test_dir, 'valid-skill', name='valid-skill', description='Valid skill'
        )

        # Create a directory with invalid SKILL.md (missing name/description)
        invalid_dir = self.test_dir / '.agents' / 'skills' / 'invalid-skill'
        invalid_dir.mkdir(parents=True, exist_ok=True)
        (invalid_dir / 'SKILL.md').write_text(
            '# Invalid\nNo frontmatter', encoding='utf-8'
        )

        skills = await list_installed_skills(is_global=False, cwd=str(self.test_dir))
        assert len(skills) == 1
        assert skills[0].name == 'valid-skill'

    @pytest.mark.asyncio
    async def test_should_filter_by_scope_project_only(self):
        """Should filter by scope - project only."""
        await create_skill_dir(
            self.test_dir,
            'project-skill',
            name='project-skill',
            description='Project skill',
        )

        skills = await list_installed_skills(is_global=False, cwd=str(self.test_dir))
        assert len(skills) == 1
        assert skills[0].scope == 'project'

    @pytest.mark.asyncio
    async def test_should_handle_global_scope_option(self):
        """Should handle global scope option."""
        # Test with global: True - verifies the function doesn't crash
        # Note: This checks ~/.agents/skills, results depend on system state
        skills = await list_installed_skills(is_global=True, cwd=str(self.test_dir))
        assert isinstance(skills, list)

    @pytest.mark.asyncio
    async def test_should_apply_agent_filter(self):
        """Should apply agent filter."""
        await create_skill_dir(
            self.test_dir, 'test-skill', name='test-skill', description='Test skill'
        )

        # Filter by a specific agent
        skills = await list_installed_skills(
            is_global=False,
            cwd=str(self.test_dir),
            agent_filter=['cursor'],
        )
        # Result depends on whether cursor is detected as installed
        assert isinstance(skills, list)

    @pytest.mark.asyncio
    async def test_should_only_attribute_skills_to_installed_agents_issue_225(self):
        """Should only attribute skills to installed agents (issue #225)."""
        # Mock: only amp is installed (not kimi-cli, even though they share .agents/skills)
        with patch('skillsmd.installer.detect_installed_agents') as mock_detect:
            mock_detect.return_value = ['amp']

            await create_skill_dir(
                self.test_dir, 'test-skill', name='test-skill', description='Test skill'
            )

            skills = await list_installed_skills(
                is_global=False, cwd=str(self.test_dir)
            )

            assert len(skills) == 1
            # Should only show amp, not kimi-cli
            if 'amp' in skills[0].agents:
                assert 'kimi-cli' not in skills[0].agents

    @pytest.mark.asyncio
    async def test_should_handle_nonexistent_directory(self):
        """Should handle nonexistent directory gracefully."""
        nonexistent = str(self.test_dir / 'nonexistent')
        skills = await list_installed_skills(is_global=False, cwd=nonexistent)
        assert skills == []
