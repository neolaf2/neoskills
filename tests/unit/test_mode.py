"""Tests for neoskills.core.mode and neoskills.core.namespace."""

from neoskills.core.mode import ExecutionMode, detect_mode
from neoskills.core.namespace import NamespaceManager
from neoskills.plugin.plugin_context import PluginContext
from neoskills.plugin.schema import validate_plugin_yaml


class TestExecutionMode:
    def test_default_is_agent(self, monkeypatch):
        monkeypatch.delenv("NEOSKILLS_MODE", raising=False)
        monkeypatch.delenv("CLAUDE_CODE_ENTRY", raising=False)
        assert detect_mode() == ExecutionMode.AGENT

    def test_env_var_plugin(self, monkeypatch):
        monkeypatch.setenv("NEOSKILLS_MODE", "plugin")
        assert detect_mode() == ExecutionMode.PLUGIN

    def test_env_var_agent(self, monkeypatch):
        monkeypatch.setenv("NEOSKILLS_MODE", "agent")
        assert detect_mode() == ExecutionMode.AGENT


class TestNamespaceManager:
    def test_qualify_plugin_mode(self):
        ns = NamespaceManager(mode=ExecutionMode.PLUGIN)
        assert ns.qualify("find_skills") == "plugin/neoskills/find_skills"

    def test_qualify_agent_mode(self):
        ns = NamespaceManager(mode=ExecutionMode.AGENT)
        assert ns.qualify("find_skills") == "find_skills"

    def test_qualify_already_qualified(self):
        ns = NamespaceManager(mode=ExecutionMode.PLUGIN)
        assert ns.qualify("plugin/neoskills/find_skills") == "plugin/neoskills/find_skills"

    def test_is_own(self):
        ns = NamespaceManager(mode=ExecutionMode.PLUGIN)
        assert ns.is_own("plugin/neoskills/find_skills") is True
        assert ns.is_own("find_skills") is False
        assert ns.is_own("plugin/other/find_skills") is False

    def test_strip(self):
        ns = NamespaceManager(mode=ExecutionMode.PLUGIN)
        assert ns.strip("plugin/neoskills/find_skills") == "find_skills"
        assert ns.strip("find_skills") == "find_skills"


class TestPluginContext:
    def test_creation(self):
        ctx = PluginContext(host_agent="claude-code")
        assert ctx.host_agent == "claude-code"
        assert ctx.namespace.mode == ExecutionMode.PLUGIN
        assert ctx.has_capability("discover") is True
        assert ctx.has_capability("nonexistent") is False

    def test_qualify(self):
        ctx = PluginContext(host_agent="opencode")
        assert ctx.qualify("find_skills") == "plugin/neoskills/find_skills"


class TestPluginSchema:
    def test_valid_plugin_yaml(self, tmp_path):
        yaml_path = tmp_path / "plugin.yaml"
        yaml_path.write_text(
            "name: neoskills\n"
            "version: '0.2.1'\n"
            "namespace: plugin/neoskills\n"
            "capabilities:\n  - discover\n  - lifecycle\n"
        )
        result = validate_plugin_yaml(yaml_path)
        assert result["valid"] is True
        assert result["errors"] == []

    def test_missing_required_fields(self, tmp_path):
        yaml_path = tmp_path / "plugin.yaml"
        yaml_path.write_text("name: neoskills\n")
        result = validate_plugin_yaml(yaml_path)
        assert result["valid"] is False
        assert any("version" in e for e in result["errors"])

    def test_invalid_namespace(self, tmp_path):
        yaml_path = tmp_path / "plugin.yaml"
        yaml_path.write_text(
            "name: neoskills\nversion: '0.2.1'\nnamespace: bad/namespace\n"
        )
        result = validate_plugin_yaml(yaml_path)
        assert result["valid"] is False
        assert any("plugin/" in e for e in result["errors"])

    def test_missing_file(self, tmp_path):
        result = validate_plugin_yaml(tmp_path / "nope.yaml")
        assert result["valid"] is False
