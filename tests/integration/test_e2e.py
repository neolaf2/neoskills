"""End-to-end integration test: init -> create -> link -> doctor -> unlink."""

from pathlib import Path

import pytest

from neoskills.core.cellar import Cellar
from neoskills.core.frontmatter import write_frontmatter
from neoskills.core.linker import Linker
from neoskills.core.tap import TapManager


class TestEndToEnd:
    """Full workflow: init -> create tap -> add skill -> link -> doctor -> unlink."""

    def test_full_workflow(self, tmp_path: Path):
        root = tmp_path / ".neoskills"
        target_dir = tmp_path / "agent_skills"
        target_dir.mkdir()

        # === INIT ===
        cellar = Cellar(root)
        cellar.initialize()
        assert cellar.is_initialized

        # Configure target to point to our temp dir
        config = cellar.load_config()
        config["targets"] = {"test-target": {"skill_path": str(target_dir)}}
        config["default_target"] = "test-target"
        cellar.save_config(config)

        # === CREATE TAP (local, no git) ===
        tap_dir = cellar.tap_dir("mySkills")
        skills_dir = tap_dir / "skills"
        skills_dir.mkdir(parents=True)

        import yaml
        (tap_dir / "tap.yaml").write_text(yaml.dump({
            "name": "mySkills",
            "description": "Test tap",
            "version": "1.0.0",
        }))

        # Register tap in config
        config = cellar.load_config()
        config["taps"] = {"mySkills": {"default": True}}
        config["default_tap"] = "mySkills"
        cellar.save_config(config)

        # === ADD SKILL ===
        skill_dir = skills_dir / "test-skill"
        skill_dir.mkdir()
        fm = {
            "name": "test-skill",
            "description": "A test skill",
            "version": "1.0.0",
            "tags": ["first-party"],
            "targets": ["test-target"],
        }
        (skill_dir / "SKILL.md").write_text(
            write_frontmatter(fm, "# Test Skill\n\nTest content.\n")
        )

        # === LIST SKILLS ===
        mgr = TapManager(cellar)
        skills = mgr.list_skills("mySkills")
        assert len(skills) == 1
        assert skills[0]["skill_id"] == "test-skill"

        # === LINK ===
        linker = Linker(cellar)
        action = linker.link("test-skill", skill_dir, "test-target")
        assert action.action == "linked"
        assert (target_dir / "test-skill").is_symlink()
        assert (target_dir / "test-skill").resolve() == skill_dir.resolve()

        # === DOCTOR (health check) ===
        health = linker.check_health("test-target")
        assert health["total"] == 1
        assert health["healthy"] == 1
        assert len(health["broken"]) == 0

        # === UNLINK ===
        unlink_action = linker.unlink("test-skill", "test-target")
        assert unlink_action.action == "unlinked"
        assert not (target_dir / "test-skill").exists()

        # === VERIFY CLEAN STATE ===
        links = linker.list_links("test-target")
        assert len(links) == 0
