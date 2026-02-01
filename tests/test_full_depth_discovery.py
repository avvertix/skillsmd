"""Tests for the full_depth option in skill discovery.

When a repository has both a root SKILL.md and nested skills in subdirectories,
the full_depth flag allows discovering all skills instead of just the root one.
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from skillsmd.skills import discover_skills


class TestDiscoverSkillsWithFullDepth:
    """Tests for discover_skills with full_depth option."""

    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Set up and tear down test directory."""
        self.test_dir = Path(tempfile.mkdtemp(prefix='skills-full-depth-test-'))
        yield
        shutil.rmtree(self.test_dir, ignore_errors=True)

    @pytest.mark.asyncio
    async def test_should_only_return_root_skill_when_full_depth_is_false(self):
        """Should only return root skill when full_depth is False."""
        # Create root SKILL.md
        (self.test_dir / 'SKILL.md').write_text(
            """---
name: root-skill
description: Root level skill
---

# Root Skill
""",
            encoding='utf-8',
        )

        # Create nested skill in skills/ directory
        nested_dir = self.test_dir / 'skills' / 'nested-skill'
        nested_dir.mkdir(parents=True, exist_ok=True)
        (nested_dir / 'SKILL.md').write_text(
            """---
name: nested-skill
description: Nested skill
---

# Nested Skill
""",
            encoding='utf-8',
        )

        skills = await discover_skills(str(self.test_dir), full_depth=False)

        assert len(skills) == 1
        assert skills[0].name == 'root-skill'

    @pytest.mark.asyncio
    async def test_should_return_all_skills_when_full_depth_is_true(self):
        """Should return all skills when full_depth is True."""
        # Create root SKILL.md
        (self.test_dir / 'SKILL.md').write_text(
            """---
name: root-skill
description: Root level skill
---

# Root Skill
""",
            encoding='utf-8',
        )

        # Create nested skills in skills/ directory
        nested_dir1 = self.test_dir / 'skills' / 'nested-skill-1'
        nested_dir1.mkdir(parents=True, exist_ok=True)
        (nested_dir1 / 'SKILL.md').write_text(
            """---
name: nested-skill-1
description: Nested skill 1
---

# Nested Skill 1
""",
            encoding='utf-8',
        )

        nested_dir2 = self.test_dir / 'skills' / 'nested-skill-2'
        nested_dir2.mkdir(parents=True, exist_ok=True)
        (nested_dir2 / 'SKILL.md').write_text(
            """---
name: nested-skill-2
description: Nested skill 2
---

# Nested Skill 2
""",
            encoding='utf-8',
        )

        skills = await discover_skills(str(self.test_dir), full_depth=True)

        assert len(skills) == 3
        names = sorted([s.name for s in skills])
        assert names == ['nested-skill-1', 'nested-skill-2', 'root-skill']

    @pytest.mark.asyncio
    async def test_should_default_to_early_return_when_no_option_is_provided(self):
        """Should default to early return (full_depth: False behavior) when no option provided."""
        # Create root SKILL.md
        (self.test_dir / 'SKILL.md').write_text(
            """---
name: root-skill
description: Root level skill
---

# Root Skill
""",
            encoding='utf-8',
        )

        # Create nested skill
        nested_dir = self.test_dir / 'skills' / 'nested-skill'
        nested_dir.mkdir(parents=True, exist_ok=True)
        (nested_dir / 'SKILL.md').write_text(
            """---
name: nested-skill
description: Nested skill
---

# Nested Skill
""",
            encoding='utf-8',
        )

        # No options passed - should default to early return
        skills = await discover_skills(str(self.test_dir))

        assert len(skills) == 1
        assert skills[0].name == 'root-skill'

    @pytest.mark.asyncio
    async def test_should_find_all_skills_when_no_root_skill_md_exists(self):
        """Should find all skills when no root SKILL.md exists (regardless of full_depth)."""
        # No root SKILL.md, just nested skills

        skill_dir1 = self.test_dir / 'skills' / 'skill-1'
        skill_dir1.mkdir(parents=True, exist_ok=True)
        (skill_dir1 / 'SKILL.md').write_text(
            """---
name: skill-1
description: Skill 1
---

# Skill 1
""",
            encoding='utf-8',
        )

        skill_dir2 = self.test_dir / 'skills' / 'skill-2'
        skill_dir2.mkdir(parents=True, exist_ok=True)
        (skill_dir2 / 'SKILL.md').write_text(
            """---
name: skill-2
description: Skill 2
---

# Skill 2
""",
            encoding='utf-8',
        )

        # Without full_depth
        skills_default = await discover_skills(str(self.test_dir))
        assert len(skills_default) == 2

        # With full_depth
        skills_full_depth = await discover_skills(str(self.test_dir), full_depth=True)
        assert len(skills_full_depth) == 2

    @pytest.mark.asyncio
    async def test_should_not_duplicate_skills_when_root_and_nested_have_same_name(
        self,
    ):
        """Should not duplicate skills when root and nested have the same name."""
        # Edge case: root SKILL.md and a nested skill with the same name
        (self.test_dir / 'SKILL.md').write_text(
            """---
name: my-skill
description: Root level skill
---

# Root Skill
""",
            encoding='utf-8',
        )

        # Create nested skill with same name
        nested_dir = self.test_dir / 'skills' / 'my-skill'
        nested_dir.mkdir(parents=True, exist_ok=True)
        (nested_dir / 'SKILL.md').write_text(
            """---
name: my-skill
description: Nested skill with same name
---

# Nested Skill
""",
            encoding='utf-8',
        )

        skills = await discover_skills(str(self.test_dir), full_depth=True)

        # Should only have one skill (deduplication by name)
        assert len(skills) == 1
        assert skills[0].name == 'my-skill'

    @pytest.mark.asyncio
    async def test_should_find_skills_in_curated_directory(self):
        """Should find skills in .curated subdirectory."""
        # Create skill in .curated directory
        curated_dir = self.test_dir / 'skills' / '.curated' / 'curated-skill'
        curated_dir.mkdir(parents=True, exist_ok=True)
        (curated_dir / 'SKILL.md').write_text(
            """---
name: curated-skill
description: A curated skill
---

# Curated Skill
""",
            encoding='utf-8',
        )

        skills = await discover_skills(str(self.test_dir))

        assert len(skills) == 1
        assert skills[0].name == 'curated-skill'
