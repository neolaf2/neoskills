"""Tests for adapter modules."""

from pathlib import Path

from neoskills.adapters.claude.adapter import ClaudeCodeAdapter
from neoskills.adapters.factory import get_adapter, list_adapter_types
from neoskills.core.models import Target, TransportType


class TestAdapterFactory:
    def test_list_types(self):
        types = list_adapter_types()
        assert "claude-code" in types
        assert "opencode" in types
        assert "openclaw" in types

    def test_get_adapter(self):
        adapter = get_adapter("claude-code")
        assert isinstance(adapter, ClaudeCodeAdapter)

    def test_unknown_adapter(self):
        import pytest

        with pytest.raises(ValueError, match="No adapter"):
            get_adapter("unknown-agent")


class TestClaudeCodeAdapter:
    def test_discover(self, mock_claude_skills: Path):
        adapter = ClaudeCodeAdapter()
        target = Target(
            target_id="test",
            agent_type="claude-code",
            discovery_paths=[str(mock_claude_skills)],
        )
        discovered = adapter.discover(target)
        # Should find: test-skill-a (dir), test-skill-b (dir), test-skill-c (file)
        ids = [s.skill_id for s in discovered]
        assert "test-skill-a" in ids
        assert "test-skill-b" in ids
        assert "test-skill-c" in ids

    def test_discover_frontmatter(self, mock_claude_skills: Path):
        adapter = ClaudeCodeAdapter()
        target = Target(
            target_id="test",
            agent_type="claude-code",
            discovery_paths=[str(mock_claude_skills)],
        )
        discovered = adapter.discover(target)
        by_id = {s.skill_id: s for s in discovered}
        assert by_id["test-skill-a"].has_frontmatter is True
        assert by_id["test-skill-b"].has_frontmatter is False

    def test_export(self, mock_claude_skills: Path):
        adapter = ClaudeCodeAdapter()
        target = Target(
            target_id="test",
            agent_type="claude-code",
            discovery_paths=[str(mock_claude_skills)],
        )
        exported = adapter.export(target, ["test-skill-a"])
        assert len(exported) == 1
        assert exported[0][0] == "test-skill-a"
        assert "test-skill-a" in exported[0][1]

    def test_install(self, tmp_path: Path, mock_claude_skills: Path):
        adapter = ClaudeCodeAdapter()
        install_dir = tmp_path / "install"
        target = Target(
            target_id="test",
            agent_type="claude-code",
            install_paths=[str(install_dir)],
        )
        path = adapter.install(target, "new-skill", "# New Skill")
        assert path.exists()
        assert path.read_text() == "# New Skill"
