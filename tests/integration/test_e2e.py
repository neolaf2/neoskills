"""End-to-end integration test: init -> scan -> import -> deploy -> embed."""

from pathlib import Path

import pytest

from neoskills.adapters.claude.adapter import ClaudeCodeAdapter
from neoskills.bank.provenance import ProvenanceTracker
from neoskills.bank.registry import Registry
from neoskills.bank.store import SkillStore
from neoskills.bundles.manager import BundleManager
from neoskills.core.models import Bundle, Provenance, SkillFormat, Target
from neoskills.core.workspace import Workspace
from neoskills.mappings.resolver import SymlinkResolver
from neoskills.mappings.target import TargetManager


class TestEndToEnd:
    """Full workflow: init -> scan -> import -> bundle -> deploy -> embed -> unembed."""

    def test_full_workflow(self, tmp_path: Path, mock_claude_skills: Path):
        # === INIT ===
        ws = Workspace(tmp_path / ".neoskills")
        result = ws.initialize()
        assert ws.is_initialized
        assert (ws.my_memory / "AGENTS.md").exists()

        # === TARGET SETUP ===
        mgr = TargetManager(ws)
        target = Target(
            target_id="test-claude",
            agent_type="claude-code",
            display_name="Test Claude",
            discovery_paths=[str(mock_claude_skills)],
            install_paths=[str(tmp_path / "agent_skills")],
            writable=True,
        )
        mgr.add(target)
        assert mgr.get("test-claude") is not None

        # === SCAN ===
        adapter = ClaudeCodeAdapter()
        discovered = adapter.discover(target)
        assert len(discovered) == 3  # a (dir), b (dir), c (file)

        # === IMPORT ===
        store = SkillStore(ws)
        registry = Registry(ws)
        prov_tracker = ProvenanceTracker(ws.bank_skills)

        exported = adapter.export(target, ["test-skill-a"])
        assert len(exported) == 1

        skill_id, content = exported[0]
        skill = store.add(skill_id, content, source_format=SkillFormat.CLAUDE_CODE)
        registry.register(skill)

        prov = Provenance(
            skill_id=skill_id,
            source_type="target",
            source_location=str(mock_claude_skills),
            source_target="test-claude",
            original_checksum=skill.checksum,
        )
        prov_tracker.record(prov)

        # Verify bank
        assert "test-skill-a" in store.list_skills()
        assert "test-skill-a" in registry.list_all()
        assert prov_tracker.get("test-skill-a") is not None

        # === BUNDLE ===
        bmgr = BundleManager(ws)
        bundle = Bundle(
            bundle_id="test-bundle",
            name="Test Bundle",
            skill_ids=["test-skill-a"],
        )
        bmgr.create(bundle)
        assert bmgr.get("test-bundle") is not None

        # === DEPLOY ===
        install_dir = tmp_path / "agent_skills"
        variant_content = store.get_variant_content(skill_id, "claude-code")
        deploy_content = variant_content or skill.content
        path = adapter.install(target, skill_id, deploy_content)
        assert path.exists()

        # === EMBED ===
        resolver = SymlinkResolver(ws)
        bank_path = store.canonical_dir(skill_id)
        agent_path = install_dir / skill_id

        # Agent path was just created by deploy, embed should back it up
        action = resolver.create_symlink(skill_id, bank_path, agent_path)
        assert agent_path.is_symlink()
        assert action.backup is not None

        resolver.save_state([action])
        state = resolver.load_state()
        assert skill_id in state

        # === UNEMBED ===
        resolver.remove_symlink(skill_id, agent_path)
        assert not agent_path.is_symlink()
        resolver.clear_state([skill_id])
        assert skill_id not in resolver.load_state()
