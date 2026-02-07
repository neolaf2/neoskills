"""Governance capability — version checks, compatibility, and policy enforcement."""

from __future__ import annotations

from pathlib import Path

from neoskills.core.workspace import Workspace


def version_check(skill_id: str, target_id: str = "claude-code-user", root: str | None = None) -> dict:
    """Compare a bank skill's version against its deployed version.

    Returns dict with 'skill_id', 'bank_checksum', 'deployed_checksum', 'in_sync'.
    """
    from neoskills.bank.store import SkillStore
    from neoskills.core.checksum import checksum_directory
    from neoskills.mappings.target import TargetManager

    ws = Workspace() if root is None else Workspace(root)
    store = SkillStore(ws)

    if not store.exists(skill_id):
        return {"error": f"Skill '{skill_id}' not found in bank"}

    bank_cksum = store.dir_checksum(skill_id)

    mgr = TargetManager(ws)
    mgr.ensure_builtins()
    target = mgr.get(target_id)
    if not target or not target.install_paths:
        return {"error": f"Target '{target_id}' not found"}

    agent_path = Path(target.install_paths[0]).expanduser() / skill_id
    if not agent_path.exists():
        return {
            "skill_id": skill_id,
            "bank_checksum": bank_cksum,
            "deployed_checksum": None,
            "in_sync": False,
            "status": "not_deployed",
        }

    # If symlink, resolve to actual path
    resolved = agent_path.resolve()
    deployed_cksum = checksum_directory(resolved) if resolved.is_dir() else None

    return {
        "skill_id": skill_id,
        "bank_checksum": bank_cksum,
        "deployed_checksum": deployed_cksum,
        "in_sync": bank_cksum == deployed_cksum,
    }


def compatibility_check(skill_id: str, target_id: str = "claude-code-user", root: str | None = None) -> dict:
    """Check if a skill has a variant compatible with the target agent type.

    Returns dict with 'skill_id', 'target', 'has_variant', 'has_canonical'.
    """
    from neoskills.bank.store import SkillStore
    from neoskills.mappings.target import TargetManager

    ws = Workspace() if root is None else Workspace(root)
    store = SkillStore(ws)
    mgr = TargetManager(ws)
    mgr.ensure_builtins()

    target = mgr.get(target_id)
    if not target:
        return {"error": f"Target '{target_id}' not found"}

    if not store.exists(skill_id):
        return {"error": f"Skill '{skill_id}' not found in bank"}

    variant_dir = store.variant_dir(skill_id, target.agent_type)
    has_variant = (variant_dir / "SKILL.md").exists()
    has_canonical = (store.canonical_dir(skill_id) / "SKILL.md").exists()

    return {
        "skill_id": skill_id,
        "target": target_id,
        "agent_type": target.agent_type,
        "has_variant": has_variant,
        "has_canonical": has_canonical,
        "compatible": has_variant or has_canonical,
    }


def policy_enforce(root: str | None = None) -> dict:
    """Run governance checks on the entire bank.

    Returns dict with validation summary.
    """
    from neoskills.bank.validator import SkillValidator

    ws = Workspace() if root is None else Workspace(root)
    validator = SkillValidator(ws)
    report = validator.validate_all()

    return {
        "total_skills": report.total_skills,
        "passed": report.passed,
        "errors": len(report.errors),
        "warnings": len(report.warnings),
        "policy": "All skills must have name, description, and valid references",
    }
