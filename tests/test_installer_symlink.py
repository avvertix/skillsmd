"""Regression tests for symlink installs when canonical and agent paths match.

These tests verify:
- Self-loops are not created when canonical and agent paths would be the same
- Pre-existing self-loop symlinks are cleaned up during installation
"""

import os
import shutil
import tempfile
from pathlib import Path

import pytest

from skillsmd.installer import install_skill_for_agent
from skillsmd.types import Skill


def make_skill_source(root: Path, name: str) -> str:
    """Create a mock skill source directory with SKILL.md."""
    skill_dir = root / 'source-skill'
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = f'---\nname: {name}\ndescription: test\n---\n'
    (skill_dir / 'SKILL.md').write_text(skill_md, encoding='utf-8')
    return str(skill_dir)


class TestInstallerSymlinkRegression:
    """Installer symlink regression tests."""

    @pytest.mark.asyncio
    async def test_does_not_create_self_loop_when_canonical_and_agent_paths_match(self):
        """Should not create self-loop when canonical and agent paths match."""
        root = Path(tempfile.mkdtemp(prefix='add-skill-'))
        project_dir = root / 'project'
        project_dir.mkdir(parents=True, exist_ok=True)

        skill_name = 'self-loop-skill'
        skill_dir = make_skill_source(root, skill_name)

        try:
            result = await install_skill_for_agent(
                Skill(name=skill_name, description='test', path=skill_dir),
                'amp',
                is_global=False,
                cwd=str(project_dir),
                mode='symlink',
            )

            assert result.success is True
            assert result.symlink_failed is None or result.symlink_failed is False

            installed_path = project_dir / '.agents' / 'skills' / skill_name
            assert installed_path.exists()
            # After installation, canonical and agent paths may be different
            # The key is that the installation succeeds without creating a self-loop
            assert installed_path.is_dir()

            # Verify SKILL.md exists and has correct content
            skill_md_path = installed_path / 'SKILL.md'
            assert skill_md_path.exists()
            contents = skill_md_path.read_text(encoding='utf-8')
            assert f'name: {skill_name}' in contents
        finally:
            shutil.rmtree(root, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_cleans_pre_existing_self_loop_symlink_in_canonical_dir(self):
        """Should clean pre-existing self-loop symlink in canonical dir."""
        root = Path(tempfile.mkdtemp(prefix='add-skill-'))
        project_dir = root / 'project'
        project_dir.mkdir(parents=True, exist_ok=True)

        skill_name = 'self-loop-skill'
        skill_dir = make_skill_source(root, skill_name)
        canonical_dir = project_dir / '.agents' / 'skills' / skill_name

        try:
            # Create a self-loop symlink manually
            (project_dir / '.agents' / 'skills').mkdir(parents=True, exist_ok=True)

            # Create a symlink that points to itself (self-loop)
            # On Windows, we use os.symlink with target_is_directory=True
            if os.name == 'nt':
                try:
                    os.symlink(skill_name, str(canonical_dir), target_is_directory=True)
                except OSError:
                    # Symlinks may require elevated privileges on Windows
                    pytest.skip(
                        'Symlink creation requires elevated privileges on Windows'
                    )
            else:
                os.symlink(skill_name, str(canonical_dir))

            # Verify pre-existing symlink
            assert canonical_dir.is_symlink()

            result = await install_skill_for_agent(
                Skill(name=skill_name, description='test', path=skill_dir),
                'amp',
                is_global=False,
                cwd=str(project_dir),
                mode='symlink',
            )

            assert result.success is True

            # After installation, the self-loop should be replaced
            # The path should now be a directory (not a self-referencing symlink)
            assert canonical_dir.is_dir()
        finally:
            shutil.rmtree(root, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_copy_mode_works_correctly(self):
        """Should install correctly in copy mode."""
        root = Path(tempfile.mkdtemp(prefix='add-skill-'))
        project_dir = root / 'project'
        project_dir.mkdir(parents=True, exist_ok=True)

        skill_name = 'copy-test-skill'
        skill_dir = make_skill_source(root, skill_name)

        try:
            result = await install_skill_for_agent(
                Skill(name=skill_name, description='test', path=skill_dir),
                'amp',
                is_global=False,
                cwd=str(project_dir),
                mode='copy',
            )

            assert result.success is True
            assert result.mode == 'copy'

            # In copy mode, the skill should be copied directly to agent location
            installed_path = Path(result.path)
            assert installed_path.exists()
            assert installed_path.is_dir()
            assert not installed_path.is_symlink()

            # Verify SKILL.md exists
            skill_md_path = installed_path / 'SKILL.md'
            assert skill_md_path.exists()
        finally:
            shutil.rmtree(root, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_unknown_agent_returns_error(self):
        """Should return error for unknown agent."""
        root = Path(tempfile.mkdtemp(prefix='add-skill-'))
        project_dir = root / 'project'
        project_dir.mkdir(parents=True, exist_ok=True)

        skill_name = 'test-skill'
        skill_dir = make_skill_source(root, skill_name)

        try:
            result = await install_skill_for_agent(
                Skill(name=skill_name, description='test', path=skill_dir),
                'nonexistent-agent',
                is_global=False,
                cwd=str(project_dir),
                mode='symlink',
            )

            assert result.success is False
            assert 'Unknown agent' in result.error
        finally:
            shutil.rmtree(root, ignore_errors=True)
