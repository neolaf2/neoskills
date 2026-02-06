"""Claude Code MCP tools for neoskills embedded plugin mode.

These tools are exposed via the MCP protocol so Claude Code can invoke
neoskills operations directly as tool calls.
"""

from neoskills.adapters.factory import get_adapter
from neoskills.bank.store import SkillStore
from neoskills.core.workspace import Workspace
from neoskills.mappings.target import TargetManager


def neoskills_list(query: str = "") -> dict:
    """List skills in the bank, optionally filtered by query.

    Args:
        query: Optional search query to filter skills by name/description/tags.

    Returns:
        Dictionary with skill list and count.
    """
    from neoskills.bank.registry import Registry

    ws = Workspace()
    registry = Registry(ws)

    if query:
        skills = registry.search(query)
    else:
        skills = registry.list_all()

    return {
        "count": len(skills),
        "skills": [
            {"id": sid, "name": info.get("name", sid), "description": info.get("description", "")}
            for sid, info in skills.items()
        ],
    }


def neoskills_scan(target_id: str = "claude-code-user") -> dict:
    """Scan a target for installed skills.

    Args:
        target_id: Target to scan (default: claude-code-user).

    Returns:
        Dictionary with discovered skills.
    """
    ws = Workspace()
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
            {"id": s.skill_id, "name": s.name, "description": s.description} for s in discovered
        ],
    }


def neoskills_deploy(skill_id: str, target_id: str) -> dict:
    """Deploy a skill from the bank to a target.

    Args:
        skill_id: Skill to deploy.
        target_id: Target to deploy to.

    Returns:
        Dictionary with deployment result.
    """
    ws = Workspace()
    store = SkillStore(ws)
    mgr = TargetManager(ws)
    mgr.ensure_builtins()

    skill = store.get(skill_id)
    if not skill:
        return {"error": f"Skill '{skill_id}' not found in bank"}

    target = mgr.get(target_id)
    if not target:
        return {"error": f"Target '{target_id}' not found"}

    adapter = get_adapter(target.agent_type)
    variant_content = store.get_variant_content(skill_id, target.agent_type)
    content = variant_content or adapter.translate(skill, target)
    path = adapter.install(target, skill_id, content)

    return {"status": "deployed", "skill_id": skill_id, "target": target_id, "path": str(path)}


def neoskills_enhance(skill_id: str, operation: str = "audit") -> dict:
    """Enhance a skill using Claude.

    Args:
        skill_id: Skill to enhance.
        operation: Enhancement operation (normalize, audit, add-docs, add-tests, generate-variant).

    Returns:
        Dictionary with enhancement result or error.
    """
    from neoskills.meta.enhancer import Enhancer

    ws = Workspace()
    store = SkillStore(ws)

    skill = store.get(skill_id)
    if not skill:
        return {"error": f"Skill '{skill_id}' not found in bank"}

    enhancer = Enhancer()
    if not enhancer.available:
        return {"error": "No LLM backend available"}

    try:
        result = enhancer.enhance(skill.content, operation)
        return {"status": "success", "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}
