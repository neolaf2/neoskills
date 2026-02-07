"""Shared fixtures for neoskills tests."""

import pytest
from pathlib import Path

from neoskills.core.cellar import Cellar


@pytest.fixture
def tmp_cellar(tmp_path: Path) -> Cellar:
    """Create a temporary neoskills workspace using the new Cellar."""
    cellar = Cellar(root=tmp_path / ".neoskills")
    cellar.initialize()
    return cellar


@pytest.fixture
def mock_claude_skills(tmp_path: Path) -> Path:
    """Create mock Claude Code skills directory."""
    skills_dir = tmp_path / "claude_skills"
    skills_dir.mkdir()

    # Create a directory-based skill with frontmatter
    skill_a = skills_dir / "test-skill-a"
    skill_a.mkdir()
    (skill_a / "SKILL.md").write_text(
        "---\n"
        "name: test-skill-a\n"
        "description: A test skill for unit testing\n"
        "tags:\n  - test\n  - demo\n"
        "---\n\n"
        "# Test Skill A\n\nThis is a test skill.\n"
    )

    # Create a directory-based skill without frontmatter
    skill_b = skills_dir / "test-skill-b"
    skill_b.mkdir()
    (skill_b / "SKILL.md").write_text(
        "# Test Skill B\n\nNo frontmatter here.\n"
    )

    # Create a standalone .md file skill
    (skills_dir / "test-skill-c.md").write_text(
        "---\nname: test-skill-c\ndescription: Standalone file skill\n---\n\n"
        "# Test Skill C\n"
    )

    return skills_dir
