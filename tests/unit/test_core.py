"""Tests for core modules."""

from pathlib import Path

from neoskills.core.checksum import checksum_string, checksum_file
from neoskills.core.config import Config
from neoskills.core.frontmatter import parse_frontmatter, write_frontmatter, extract_skill_name
from neoskills.core.models import Skill, SkillMetadata, Target, Bundle
from neoskills.core.workspace import Workspace


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


class TestWorkspace:
    def test_initialize(self, tmp_path: Path):
        ws = Workspace(tmp_path / ".neoskills")
        result = ws.initialize()
        assert len(result["directories"]) > 0
        assert len(result["memory_files"]) == 6
        assert len(result["config_files"]) == 3
        assert ws.is_initialized

    def test_idempotent_init(self, tmp_path: Path):
        ws = Workspace(tmp_path / ".neoskills")
        ws.initialize()
        result = ws.initialize()
        assert len(result["directories"]) == 0
        assert len(result["memory_files"]) == 0
        assert len(result["config_files"]) == 0

    def test_my_memory_never_overwritten(self, tmp_path: Path):
        ws = Workspace(tmp_path / ".neoskills")
        ws.initialize()
        # Modify a memory file
        agents_file = ws.my_memory / "AGENTS.md"
        agents_file.write_text("Custom content")
        # Re-initialize
        ws.ensure_my_memory()
        assert agents_file.read_text() == "Custom content"


class TestModels:
    def test_skill_creation(self):
        meta = SkillMetadata(name="test", description="A test skill")
        skill = Skill(skill_id="test", metadata=meta, content="# Test")
        assert skill.skill_id == "test"
        assert skill.metadata.name == "test"

    def test_target_creation(self):
        target = Target(
            target_id="claude-code-user",
            agent_type="claude-code",
            discovery_paths=["~/.claude/skills"],
        )
        assert target.target_id == "claude-code-user"
        assert target.writable is True

    def test_bundle_creation(self):
        bundle = Bundle(
            bundle_id="research",
            name="Research Bundle",
            skill_ids=["skill-a", "skill-b"],
        )
        assert len(bundle.skill_ids) == 2
