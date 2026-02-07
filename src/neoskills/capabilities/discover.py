"""Discover capability — find, index, and validate skills."""

from __future__ import annotations

from neoskills.core.workspace import Workspace


def find_skills(target_id: str = "claude-code-user", root: str | None = None) -> dict:
    """Discover skills installed in a target agent.

    Returns dict with 'target', 'count', and 'skills' list.
    """
    from neoskills.adapters.factory import get_adapter
    from neoskills.mappings.target import TargetManager

    ws = Workspace() if root is None else Workspace(root)
    mgr = TargetManager(ws)
    mgr.ensure_builtins()
    target = mgr.get(target_id)
    if not target:
        return {"error": f"Target '{target_id}' not found"}

    adapter = get_adapter(target.agent_type)
    discovered = adapter.discover(target)
    return {
        "target": target_id,
        "count": len(discovered),
        "skills": [
            {"id": s.skill_id, "name": s.name, "description": s.description}
            for s in discovered
        ],
    }


def index_skills(root: str | None = None) -> dict:
    """List all skills in the bank registry.

    Returns dict with 'count' and 'skills'.
    """
    from neoskills.bank.registry import Registry

    ws = Workspace() if root is None else Workspace(root)
    registry = Registry(ws)
    skills = registry.list_all()
    return {
        "count": len(skills),
        "skills": [
            {"id": sid, "name": info.get("name", sid), "description": info.get("description", "")}
            for sid, info in skills.items()
        ],
    }


def validate_skills(skill_ids: list[str] | None = None, root: str | None = None) -> dict:
    """Validate skills in the bank.

    Args:
        skill_ids: Specific skills to validate. If None, validates all.

    Returns dict with 'total', 'passed', 'errors', 'warnings'.
    """
    from neoskills.bank.validator import SkillValidator

    ws = Workspace() if root is None else Workspace(root)
    validator = SkillValidator(ws)

    if skill_ids:
        issues = []
        for sid in skill_ids:
            report = validator.validate_one(sid)
            issues.extend(
                {"skill_id": i.skill_id, "severity": i.severity.value, "message": i.message}
                for i in report.issues
            )
        return {
            "total": len(skill_ids),
            "passed": all(i["severity"] != "error" for i in issues),
            "issues": issues,
        }

    report = validator.validate_all()
    return {
        "total": report.total_skills,
        "passed": report.passed,
        "errors": len(report.errors),
        "warnings": len(report.warnings),
        "issues": [
            {"skill_id": i.skill_id, "severity": i.severity.value, "message": i.message}
            for i in report.issues
        ],
    }
