"""Lifecycle capability — install, uninstall, upgrade skills."""

from __future__ import annotations

from pathlib import Path

from neoskills.core.workspace import Workspace


def install_skill(skill_id: str, target_id: str = "claude-code-user", root: str | None = None) -> dict:
    """Install a skill from the bank to a target (symlink-based embed).

    Returns dict with 'status', 'skill_id', 'target', 'path'.
    """
    from neoskills.bank.store import SkillStore
    from neoskills.mappings.resolver import SymlinkResolver
    from neoskills.mappings.target import TargetManager

    ws = Workspace() if root is None else Workspace(root)
    store = SkillStore(ws)
    mgr = TargetManager(ws)
    mgr.ensure_builtins()

    if not store.exists(skill_id):
        return {"error": f"Skill '{skill_id}' not found in bank"}

    target = mgr.get(target_id)
    if not target or not target.install_paths:
        return {"error": f"Target '{target_id}' not found or has no install paths"}

    install_base = Path(target.install_paths[0]).expanduser()
    install_base.mkdir(parents=True, exist_ok=True)

    variant_dir = store.variant_dir(skill_id, target.agent_type)
    canonical = store.canonical_dir(skill_id)
    bank_path = variant_dir if (variant_dir / "SKILL.md").exists() else canonical

    agent_path = install_base / skill_id
    resolver = SymlinkResolver(ws)
    action = resolver.create_symlink(skill_id, bank_path, agent_path)
    resolver.save_state([action])

    return {
        "status": "installed",
        "skill_id": skill_id,
        "target": target_id,
        "path": str(agent_path),
    }


def uninstall_skill(skill_id: str, target_id: str = "claude-code-user", root: str | None = None) -> dict:
    """Remove a skill's symlink from a target.

    Returns dict with 'status', 'skill_id', 'target'.
    """
    from neoskills.mappings.resolver import SymlinkResolver
    from neoskills.mappings.target import TargetManager

    ws = Workspace() if root is None else Workspace(root)
    mgr = TargetManager(ws)
    mgr.ensure_builtins()

    target = mgr.get(target_id)
    if not target or not target.install_paths:
        return {"error": f"Target '{target_id}' not found or has no install paths"}

    install_base = Path(target.install_paths[0]).expanduser()
    agent_path = install_base / skill_id

    if not agent_path.exists() and not agent_path.is_symlink():
        return {"status": "not_installed", "skill_id": skill_id, "target": target_id}

    resolver = SymlinkResolver(ws)
    resolver.remove_symlinks([skill_id])

    return {"status": "uninstalled", "skill_id": skill_id, "target": target_id}


def upgrade_skill(skill_id: str, target_id: str = "claude-code-user", root: str | None = None) -> dict:
    """Re-link a skill to pick up bank changes (uninstall + install).

    Returns dict with 'status', 'skill_id', 'target'.
    """
    uninstall_skill(skill_id, target_id, root)
    return install_skill(skill_id, target_id, root)
