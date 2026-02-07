"""Tests for neoskills.core.linker — Linker symlink manager."""

from pathlib import Path

import pytest
import yaml

from neoskills.core.cellar import Cellar
from neoskills.core.frontmatter import write_frontmatter
from neoskills.core.linker import Linker, LinkAction


@pytest.fixture
def link_env(tmp_path: Path):
    """Set up a Cellar with a tap and a target directory for linking tests."""
    root = tmp_path / ".neoskills"
    target_dir = tmp_path / "agent_skills"
    target_dir.mkdir()

    cellar = Cellar(root)
    cellar.initialize()

    # Configure target
    config = cellar.load_config()
    config["targets"] = {"test-agent": {"skill_path": str(target_dir)}}
    config["default_target"] = "test-agent"
    config["default_tap"] = "mySkills"
    cellar.save_config(config)

    # Create a tap with two skills
    tap_dir = cellar.tap_dir("mySkills")
    skills_dir = tap_dir / "skills"
    for sid in ["skill-a", "skill-b"]:
        d = skills_dir / sid
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text(write_frontmatter(
            {"name": sid, "description": f"Test {sid}"}, f"# {sid}\n"
        ))

    return cellar, target_dir


class TestLink:
    def test_link_creates_symlink(self, link_env):
        cellar, target_dir = link_env
        linker = Linker(cellar)
        source = cellar.tap_skills_dir("mySkills") / "skill-a"

        action = linker.link("skill-a", source, "test-agent")
        assert action.action == "linked"
        assert (target_dir / "skill-a").is_symlink()
        assert (target_dir / "skill-a").resolve() == source.resolve()

    def test_link_skips_if_same(self, link_env):
        cellar, target_dir = link_env
        linker = Linker(cellar)
        source = cellar.tap_skills_dir("mySkills") / "skill-a"

        linker.link("skill-a", source, "test-agent")
        action2 = linker.link("skill-a", source, "test-agent")
        assert action2.action == "skipped"

    def test_link_replaces_different_symlink(self, link_env):
        cellar, target_dir = link_env
        linker = Linker(cellar)
        source_a = cellar.tap_skills_dir("mySkills") / "skill-a"
        source_b = cellar.tap_skills_dir("mySkills") / "skill-b"

        linker.link("skill-a", source_a, "test-agent")
        # Now link the same skill_id but to different source
        action = linker.link("skill-a", source_b, "test-agent")
        assert action.action == "linked"
        assert (target_dir / "skill-a").resolve() == source_b.resolve()

    def test_link_backs_up_real_directory(self, link_env):
        cellar, target_dir = link_env
        linker = Linker(cellar)
        source = cellar.tap_skills_dir("mySkills") / "skill-a"

        # Create a real directory at the target path
        real_dir = target_dir / "skill-a"
        real_dir.mkdir()
        (real_dir / "SKILL.md").write_text("# Existing local skill")

        action = linker.link("skill-a", source, "test-agent")
        assert action.action == "linked"
        assert (target_dir / "skill-a").is_symlink()
        # Backup should exist
        backup = cellar.cache_dir / "backup_skill-a"
        assert backup.exists()
        assert (backup / "SKILL.md").exists()


class TestUnlink:
    def test_unlink_removes_symlink(self, link_env):
        cellar, target_dir = link_env
        linker = Linker(cellar)
        source = cellar.tap_skills_dir("mySkills") / "skill-a"

        linker.link("skill-a", source, "test-agent")
        action = linker.unlink("skill-a", "test-agent")
        assert action.action == "unlinked"
        assert not (target_dir / "skill-a").exists()

    def test_unlink_skips_if_not_symlink(self, link_env):
        cellar, _ = link_env
        linker = Linker(cellar)
        action = linker.unlink("nonexistent", "test-agent")
        assert action.action == "skipped"


class TestLinkAll:
    def test_link_all_links_both_skills(self, link_env):
        cellar, target_dir = link_env
        linker = Linker(cellar)
        skills_dir = cellar.tap_skills_dir("mySkills")

        actions = linker.link_all(skills_dir, "test-agent")
        assert len(actions) == 2
        assert all(a.action == "linked" for a in actions)
        assert (target_dir / "skill-a").is_symlink()
        assert (target_dir / "skill-b").is_symlink()

    def test_link_all_empty_dir(self, link_env):
        cellar, _ = link_env
        linker = Linker(cellar)
        empty = cellar.root / "empty"
        empty.mkdir()
        actions = linker.link_all(empty, "test-agent")
        assert actions == []

    def test_link_all_nonexistent_dir(self, link_env):
        cellar, _ = link_env
        linker = Linker(cellar)
        actions = linker.link_all(cellar.root / "missing", "test-agent")
        assert actions == []


class TestUnlinkAll:
    def test_unlink_all(self, link_env):
        cellar, target_dir = link_env
        linker = Linker(cellar)
        skills_dir = cellar.tap_skills_dir("mySkills")

        linker.link_all(skills_dir, "test-agent")
        actions = linker.unlink_all("test-agent")
        assert len(actions) == 2
        assert all(a.action == "unlinked" for a in actions)
        assert not (target_dir / "skill-a").exists()
        assert not (target_dir / "skill-b").exists()


class TestListLinks:
    def test_list_links_shows_symlinks(self, link_env):
        cellar, target_dir = link_env
        linker = Linker(cellar)
        source = cellar.tap_skills_dir("mySkills") / "skill-a"
        linker.link("skill-a", source, "test-agent")

        links = linker.list_links("test-agent")
        assert len(links) == 1
        assert links[0]["skill_id"] == "skill-a"
        assert links[0]["linked"] is True
        assert links[0]["managed"] is True

    def test_list_links_shows_local_skills(self, link_env):
        cellar, target_dir = link_env
        linker = Linker(cellar)

        # Create a local (non-symlink) skill
        local = target_dir / "local-skill"
        local.mkdir()
        (local / "SKILL.md").write_text("# Local\n")

        links = linker.list_links("test-agent")
        assert len(links) == 1
        assert links[0]["skill_id"] == "local-skill"
        assert links[0]["linked"] is False

    def test_list_links_empty_target(self, link_env):
        cellar, _ = link_env
        linker = Linker(cellar)
        assert linker.list_links("test-agent") == []


class TestCheckHealth:
    def test_healthy_system(self, link_env):
        cellar, _ = link_env
        linker = Linker(cellar)
        skills_dir = cellar.tap_skills_dir("mySkills")
        linker.link_all(skills_dir, "test-agent")

        health = linker.check_health("test-agent")
        assert health["total"] == 2
        assert health["healthy"] == 2
        assert health["broken"] == []
        assert health["unmanaged"] == []
        assert health["local"] == []

    def test_broken_symlink_detected(self, link_env):
        cellar, target_dir = link_env
        linker = Linker(cellar)
        source = cellar.tap_skills_dir("mySkills") / "skill-a"
        linker.link("skill-a", source, "test-agent")

        # Remove the source to make symlink broken
        import shutil
        shutil.rmtree(source)

        health = linker.check_health("test-agent")
        assert len(health["broken"]) == 1
        assert health["broken"][0]["skill_id"] == "skill-a"

    def test_mixed_health(self, link_env):
        cellar, target_dir = link_env
        linker = Linker(cellar)
        source = cellar.tap_skills_dir("mySkills") / "skill-a"
        linker.link("skill-a", source, "test-agent")

        # Add a local skill
        local = target_dir / "local-skill"
        local.mkdir()
        (local / "SKILL.md").write_text("# Local\n")

        health = linker.check_health("test-agent")
        assert health["total"] == 2
        assert health["healthy"] == 1
        assert len(health["local"]) == 1
