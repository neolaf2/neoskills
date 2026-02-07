"""Tests for neoskills.core.tap — TapManager."""

from pathlib import Path

import pytest
import yaml

from neoskills.core.cellar import Cellar
from neoskills.core.frontmatter import write_frontmatter
from neoskills.core.tap import TapManager


@pytest.fixture
def tap_env(tmp_path: Path):
    """Set up a Cellar with a local tap containing test skills."""
    root = tmp_path / ".neoskills"
    cellar = Cellar(root)
    cellar.initialize()

    # Create a local tap (no git, just directories)
    tap_dir = cellar.tap_dir("mySkills")
    skills_dir = tap_dir / "skills"
    skills_dir.mkdir(parents=True)
    (tap_dir / "tap.yaml").write_text(yaml.dump({
        "name": "mySkills", "version": "1.0.0",
    }))

    # Add two skills
    for sid, desc, tags in [
        ("alpha", "Alpha skill for testing", ["first-party", "test"]),
        ("beta", "Beta research tool", ["first-party", "research"]),
    ]:
        d = skills_dir / sid
        d.mkdir()
        (d / "SKILL.md").write_text(write_frontmatter(
            {"name": sid, "description": desc, "tags": tags}, f"# {sid.title()}\n"
        ))

    # Register in config
    config = cellar.load_config()
    config["taps"] = {"mySkills": {"default": True}}
    config["default_tap"] = "mySkills"
    cellar.save_config(config)

    return cellar


class TestListTaps:
    def test_list_taps_with_one(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        taps = mgr.list_taps()
        assert taps == ["mySkills"]

    def test_list_taps_empty(self, tmp_path: Path):
        cellar = Cellar(tmp_path / ".neoskills")
        cellar.initialize()
        mgr = TapManager(cellar)
        assert mgr.list_taps() == []


class TestListSkills:
    def test_list_skills_default_tap(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        skills = mgr.list_skills()
        assert len(skills) == 2
        ids = [s["skill_id"] for s in skills]
        assert "alpha" in ids
        assert "beta" in ids

    def test_list_skills_explicit_tap(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        skills = mgr.list_skills("mySkills")
        assert len(skills) == 2

    def test_list_skills_nonexistent_tap(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        skills = mgr.list_skills("nonexistent")
        assert skills == []

    def test_skill_metadata_parsed(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        skills = mgr.list_skills()
        alpha = next(s for s in skills if s["skill_id"] == "alpha")
        assert alpha["name"] == "alpha"
        assert alpha["description"] == "Alpha skill for testing"
        assert "first-party" in alpha["tags"]


class TestGetSkillPath:
    def test_find_in_default_tap(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        path = mgr.get_skill_path("alpha")
        assert path is not None
        assert path.name == "alpha"
        assert (path / "SKILL.md").exists()

    def test_find_in_explicit_tap(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        path = mgr.get_skill_path("beta", tap_name="mySkills")
        assert path is not None

    def test_not_found(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        assert mgr.get_skill_path("nonexistent") is None

    def test_not_found_in_explicit_tap(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        assert mgr.get_skill_path("alpha", tap_name="nonexistent") is None


class TestSearch:
    def test_search_by_name(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        results = mgr.search("alpha")
        assert len(results) == 1
        assert results[0]["skill_id"] == "alpha"

    def test_search_by_description(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        results = mgr.search("research")
        assert len(results) == 1
        assert results[0]["skill_id"] == "beta"

    def test_search_by_tag(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        results = mgr.search("first-party")
        assert len(results) == 2

    def test_search_case_insensitive(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        results = mgr.search("ALPHA")
        assert len(results) == 1

    def test_search_no_results(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        results = mgr.search("nonexistent-query")
        assert results == []


class TestRemoveTap:
    def test_remove_existing(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        assert mgr.remove("mySkills") is True
        assert not tap_env.tap_dir("mySkills").exists()
        assert mgr.list_taps() == []

    def test_remove_nonexistent(self, tap_env: Cellar):
        mgr = TapManager(tap_env)
        assert mgr.remove("nonexistent") is False
