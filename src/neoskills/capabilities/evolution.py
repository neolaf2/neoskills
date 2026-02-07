"""Evolution capability — create, refactor, and specialize skills."""

from __future__ import annotations

from neoskills.core.workspace import Workspace


def create_skill(skill_id: str, content: str, root: str | None = None) -> dict:
    """Create a new skill in the bank.

    Args:
        skill_id: Unique skill identifier.
        content: SKILL.md content (frontmatter + body).

    Returns dict with 'status', 'skill_id', 'path'.
    """
    from neoskills.bank.registry import Registry
    from neoskills.bank.store import SkillStore

    ws = Workspace() if root is None else Workspace(root)
    store = SkillStore(ws)

    if store.exists(skill_id):
        return {"error": f"Skill '{skill_id}' already exists. Use refactor to update."}

    skill = store.add(skill_id, content)
    Registry(ws).register(skill)

    return {"status": "created", "skill_id": skill_id, "path": str(store.canonical_dir(skill_id))}


def refactor_skill(skill_id: str, new_content: str, root: str | None = None) -> dict:
    """Update an existing skill's content.

    Returns dict with 'status', 'skill_id'.
    """
    from neoskills.bank.store import SkillStore

    ws = Workspace() if root is None else Workspace(root)
    store = SkillStore(ws)

    if not store.exists(skill_id):
        return {"error": f"Skill '{skill_id}' not found in bank"}

    skill_file = store.canonical_dir(skill_id) / "SKILL.md"
    skill_file.write_text(new_content)

    return {"status": "refactored", "skill_id": skill_id}


def specialize_skill(
    skill_id: str, agent_type: str, variant_content: str, root: str | None = None
) -> dict:
    """Create an agent-specific variant of a skill.

    Returns dict with 'status', 'skill_id', 'agent_type', 'path'.
    """
    from neoskills.bank.store import SkillStore

    ws = Workspace() if root is None else Workspace(root)
    store = SkillStore(ws)

    if not store.exists(skill_id):
        return {"error": f"Skill '{skill_id}' not found in bank"}

    variant_dir = store.variant_dir(skill_id, agent_type)
    variant_dir.mkdir(parents=True, exist_ok=True)
    (variant_dir / "SKILL.md").write_text(variant_content)

    return {
        "status": "specialized",
        "skill_id": skill_id,
        "agent_type": agent_type,
        "path": str(variant_dir),
    }
