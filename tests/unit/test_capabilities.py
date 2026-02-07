"""Tests for neoskills.capabilities facade layer."""

from pathlib import Path

import pytest

from neoskills.capabilities import discover, evolution, governance, lifecycle
from neoskills.core.workspace import Workspace


@pytest.fixture
def cap_workspace(tmp_path: Path) -> Workspace:
    """Workspace with a sample skill for capability testing."""
    ws = Workspace(root=tmp_path / ".neoskills")
    ws.initialize()

    # Create a valid skill in the bank
    canonical = ws.bank_skills / "test-cap" / "canonical"
    canonical.mkdir(parents=True, exist_ok=True)
    (canonical / "SKILL.md").write_text(
        "---\nname: test-cap\ndescription: A capability test skill\n---\n\n"
        "# Test Cap\n\nCapability testing skill.\n"
    )

    # Register it
    from neoskills.bank.registry import Registry
    from neoskills.bank.store import SkillStore

    store = SkillStore(ws)
    skill = store.get("test-cap")
    if skill:
        Registry(ws).register(skill)

    return ws


class TestDiscover:
    def test_index_skills(self, cap_workspace):
        result = discover.index_skills(root=cap_workspace.root)
        assert result["count"] >= 1
        ids = [s["id"] for s in result["skills"]]
        assert "test-cap" in ids

    def test_validate_skills(self, cap_workspace):
        result = discover.validate_skills(skill_ids=["test-cap"], root=cap_workspace.root)
        assert result["total"] == 1
        assert result["passed"] is True


class TestEvolution:
    def test_create_skill(self, cap_workspace):
        content = "---\nname: new-skill\ndescription: Created via capability\n---\n\nBody.\n"
        result = evolution.create_skill("new-skill", content, root=cap_workspace.root)
        assert result["status"] == "created"
        assert (cap_workspace.bank_skills / "new-skill" / "canonical" / "SKILL.md").exists()

    def test_create_duplicate_errors(self, cap_workspace):
        result = evolution.create_skill("test-cap", "content", root=cap_workspace.root)
        assert "error" in result


class TestGovernance:
    def test_policy_enforce(self, cap_workspace):
        result = governance.policy_enforce(root=cap_workspace.root)
        assert result["total_skills"] >= 1
        assert result["passed"] is True

    def test_compatibility_check(self, cap_workspace):
        # Add a builtin target first
        from neoskills.mappings.target import TargetManager

        mgr = TargetManager(cap_workspace)
        mgr.ensure_builtins()

        result = governance.compatibility_check(
            "test-cap", "claude-code-user", root=cap_workspace.root
        )
        assert result["compatible"] is True
        assert result["has_canonical"] is True
