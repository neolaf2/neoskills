"""Tests for bank modules."""

from neoskills.bank.provenance import ProvenanceTracker
from neoskills.bank.registry import Registry
from neoskills.bank.store import SkillStore
from neoskills.core.models import Provenance, SkillFormat
from neoskills.core.workspace import Workspace


class TestSkillStore:
    def test_add_and_get(self, tmp_workspace: Workspace):
        store = SkillStore(tmp_workspace)
        content = "---\nname: test-skill\ndescription: Test\n---\n\n# Test\n"
        skill = store.add("test-skill", content)
        assert skill.skill_id == "test-skill"
        assert skill.metadata.name == "test-skill"

        retrieved = store.get("test-skill")
        assert retrieved is not None
        assert retrieved.metadata.name == "test-skill"

    def test_list_skills(self, tmp_workspace: Workspace):
        store = SkillStore(tmp_workspace)
        store.add("skill-a", "---\nname: a\n---\n\n# A")
        store.add("skill-b", "---\nname: b\n---\n\n# B")
        assert store.list_skills() == ["skill-a", "skill-b"]

    def test_remove_skill(self, tmp_workspace: Workspace):
        store = SkillStore(tmp_workspace)
        store.add("to-remove", "---\nname: remove\n---\n\n# Remove")
        assert store.remove("to-remove") is True
        assert store.get("to-remove") is None

    def test_add_with_variant(self, tmp_workspace: Workspace):
        store = SkillStore(tmp_workspace)
        content = "---\nname: test\n---\n\n# Test"
        store.add("test", content, source_format=SkillFormat.CLAUDE_CODE)
        variants = store.list_variants("test")
        assert "claude-code" in variants

    def test_add_variant(self, tmp_workspace: Workspace):
        store = SkillStore(tmp_workspace)
        store.add("test", "---\nname: test\n---\n\n# Test")
        store.add_variant("test", "opencode", "---\nname: test-oc\n---\n\n# OpenCode Test")
        assert store.get_variant_content("test", "opencode") is not None

    def test_get_nonexistent(self, tmp_workspace: Workspace):
        store = SkillStore(tmp_workspace)
        assert store.get("nonexistent") is None


class TestRegistry:
    def test_register_and_list(self, tmp_workspace: Workspace):
        store = SkillStore(tmp_workspace)
        registry = Registry(tmp_workspace)

        skill = store.add("reg-test", "---\nname: reg-test\n---\n\n# Test")
        registry.register(skill)

        all_skills = registry.list_all()
        assert "reg-test" in all_skills

    def test_unregister(self, tmp_workspace: Workspace):
        store = SkillStore(tmp_workspace)
        registry = Registry(tmp_workspace)

        skill = store.add("to-unreg", "---\nname: to-unreg\n---\n\n# Test")
        registry.register(skill)
        assert registry.unregister("to-unreg") is True
        assert "to-unreg" not in registry.list_all()

    def test_search(self, tmp_workspace: Workspace):
        store = SkillStore(tmp_workspace)
        registry = Registry(tmp_workspace)

        s1 = store.add("python-helper", "---\nname: python-helper\ndescription: Helps with Python\ntags:\n  - python\n---\n\n# Help")
        s2 = store.add("js-helper", "---\nname: js-helper\ndescription: Helps with JavaScript\ntags:\n  - javascript\n---\n\n# Help")

        registry.register(s1)
        registry.register(s2)

        results = registry.search("python")
        assert "python-helper" in results
        assert "js-helper" not in results


class TestProvenance:
    def test_record_and_get(self, tmp_workspace: Workspace):
        tracker = ProvenanceTracker(tmp_workspace.bank_skills)
        # Need to create the skill directory first
        (tmp_workspace.bank_skills / "test-prov").mkdir(parents=True, exist_ok=True)

        prov = Provenance(
            skill_id="test-prov",
            source_type="target",
            source_location="~/.claude/skills",
            source_target="claude-code-user",
            original_checksum="abc123",
        )
        tracker.record(prov)

        retrieved = tracker.get("test-prov")
        assert retrieved is not None
        assert retrieved.source_type == "target"
        assert retrieved.source_target == "claude-code-user"
