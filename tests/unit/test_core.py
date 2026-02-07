"""Tests for core modules."""

from pathlib import Path

from neoskills.core.cellar import Cellar
from neoskills.core.checksum import checksum_string, checksum_file
from neoskills.core.config import Config
from neoskills.core.frontmatter import parse_frontmatter, write_frontmatter, extract_skill_name
from neoskills.core.models import SkillSpec


class TestFrontmatter:
    def test_parse_with_frontmatter(self):
        content = "---\nname: test\ndescription: A test\n---\n\n# Body\n"
        meta, body = parse_frontmatter(content)
        assert meta["name"] == "test"
        assert meta["description"] == "A test"
        assert "# Body" in body

    def test_parse_without_frontmatter(self):
        content = "# Just a heading\n\nSome body text."
        meta, body = parse_frontmatter(content)
        assert meta == {}
        assert "# Just a heading" in body

    def test_write_frontmatter(self):
        result = write_frontmatter({"name": "test", "version": "1.0"}, "# Hello")
        assert result.startswith("---\n")
        assert "name: test" in result
        assert "# Hello" in result

    def test_extract_skill_name_from_frontmatter(self):
        content = "---\nname: my-skill\n---\n\n# Title"
        assert extract_skill_name(content) == "my-skill"

    def test_extract_skill_name_from_heading(self):
        content = "# My Cool Skill\n\nBody text."
        assert extract_skill_name(content) == "my-cool-skill"

    def test_extract_skill_name_fallback(self):
        content = "Just some text with no structure."
        assert extract_skill_name(content) == "unnamed"


class TestChecksum:
    def test_checksum_string(self):
        h1 = checksum_string("hello")
        h2 = checksum_string("hello")
        h3 = checksum_string("world")
        assert h1 == h2
        assert h1 != h3
        assert len(h1) == 64  # SHA256 hex

    def test_checksum_file(self, tmp_path: Path):
        f = tmp_path / "test.txt"
        f.write_text("test content")
        assert len(checksum_file(f)) == 64


class TestConfig:
    def test_set_and_get(self, tmp_path: Path):
        cfg_path = tmp_path / "config.yaml"
        cfg = Config(cfg_path)
        cfg.set("foo", "bar")
        cfg.save()

        cfg2 = Config(cfg_path)
        assert cfg2.get("foo") == "bar"

    def test_dotted_key(self, tmp_path: Path):
        cfg_path = tmp_path / "config.yaml"
        cfg = Config(cfg_path)
        cfg.set("auth.mode", "api_key")
        cfg.save()

        cfg2 = Config(cfg_path)
        assert cfg2.get("auth.mode") == "api_key"

    def test_get_default(self, tmp_path: Path):
        cfg = Config(tmp_path / "missing.yaml")
        assert cfg.get("nonexistent", "default") == "default"


class TestCellar:
    def test_initialize(self, tmp_path: Path):
        cellar = Cellar(tmp_path / ".neoskills")
        result = cellar.initialize()
        assert len(result["directories"]) == 3  # root, taps, cache
        assert len(result["files"]) == 2  # config.yaml, .gitignore
        assert cellar.is_initialized

    def test_idempotent_init(self, tmp_path: Path):
        cellar = Cellar(tmp_path / ".neoskills")
        cellar.initialize()
        result = cellar.initialize()
        assert len(result["directories"]) == 0
        assert len(result["files"]) == 0

    def test_load_save_config(self, tmp_path: Path):
        cellar = Cellar(tmp_path / ".neoskills")
        cellar.initialize()
        config = cellar.load_config()
        assert config["version"] == "0.3.0"
        assert config["default_tap"] == "mySkills"

        config["default_target"] = "opencode"
        cellar.save_config(config)

        reloaded = cellar.load_config()
        assert reloaded["default_target"] == "opencode"

    def test_target_path(self, tmp_path: Path):
        cellar = Cellar(tmp_path / ".neoskills")
        cellar.initialize()
        path = cellar.target_path("claude-code")
        assert str(path).endswith("/.claude/skills")

    def test_tap_dirs(self, tmp_path: Path):
        cellar = Cellar(tmp_path / ".neoskills")
        cellar.initialize()
        assert cellar.tap_dir("mySkills") == cellar.taps_dir / "mySkills"
        assert cellar.tap_skills_dir("mySkills") == cellar.taps_dir / "mySkills" / "skills"


class TestSkillSpec:
    def test_from_skill_dir(self, tmp_path: Path):
        skill_dir = tmp_path / "test-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text(
            "---\nname: test-skill\ndescription: A test\ntags:\n  - first-party\n---\n\n# Test\n"
        )
        spec = SkillSpec.from_skill_dir(skill_dir, tap_name="mySkills")
        assert spec.skill_id == "test-skill"
        assert spec.name == "test-skill"
        assert spec.description == "A test"
        assert "first-party" in spec.tags
        assert spec.tap == "mySkills"

    def test_from_skill_dir_no_frontmatter(self, tmp_path: Path):
        skill_dir = tmp_path / "bare-skill"
        skill_dir.mkdir()
        (skill_dir / "SKILL.md").write_text("# Bare Skill\n\nNo frontmatter.\n")
        spec = SkillSpec.from_skill_dir(skill_dir)
        assert spec.skill_id == "bare-skill"
        assert spec.name == "bare-skill"
