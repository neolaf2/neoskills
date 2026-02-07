"""Claude Code MCP tools for neoskills embedded plugin mode.

These tools are exposed via the MCP protocol so Claude Code can invoke
neoskills operations directly as tool calls. In plugin mode, results
are namespace-qualified to avoid collisions with host agent skills.
"""

from neoskills.adapters.factory import get_adapter
from neoskills.bank.store import SkillStore
from neoskills.core.mode import detect_mode
from neoskills.core.namespace import NamespaceManager
from neoskills.core.workspace import Workspace
from neoskills.mappings.target import TargetManager

_ns = NamespaceManager(mode=detect_mode())


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
        "mode": detect_mode().value,
        "count": len(skills),
        "skills": [
            {
                "id": _ns.qualify(sid),
                "name": info.get("name", sid),
                "description": info.get("description", ""),
            }
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
        skill_id: Skill to deploy (bare or namespace-qualified).
        target_id: Target to deploy to.

    Returns:
        Dictionary with deployment result.
    """
    # Strip namespace prefix if present
    bare_id = _ns.strip(skill_id)

    ws = Workspace()
    store = SkillStore(ws)
    mgr = TargetManager(ws)
    mgr.ensure_builtins()

    skill = store.get(bare_id)
    if not skill:
        return {"error": f"Skill '{bare_id}' not found in bank"}

    target = mgr.get(target_id)
    if not target:
        return {"error": f"Target '{target_id}' not found"}

    adapter = get_adapter(target.agent_type)
    variant_content = store.get_variant_content(bare_id, target.agent_type)
    content = variant_content or adapter.translate(skill, target)
    path = adapter.install(target, bare_id, content)

    return {"status": "deployed", "skill_id": _ns.qualify(bare_id), "target": target_id, "path": str(path)}


def neoskills_enhance(skill_id: str, operation: str = "audit") -> dict:
    """Enhance a skill using Claude.

    Args:
        skill_id: Skill to enhance (bare or namespace-qualified).
        operation: Enhancement operation (normalize, audit, add-docs, add-tests, generate-variant).

    Returns:
        Dictionary with enhancement result or error.
    """
    from neoskills.meta.enhancer import Enhancer

    bare_id = _ns.strip(skill_id)

    ws = Workspace()
    store = SkillStore(ws)

    skill = store.get(bare_id)
    if not skill:
        return {"error": f"Skill '{bare_id}' not found in bank"}

    enhancer = Enhancer()
    if not enhancer.available:
        return {"error": "No LLM backend available"}

    try:
        result = enhancer.enhance(skill.content, operation)
        return {"status": "success", "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}


def neoskills_capabilities() -> dict:
    """List available capability groups in the current execution mode.

    Returns:
        Dictionary with mode and available capabilities.
    """
    mode = detect_mode()
    caps = ["discover", "lifecycle", "evolution", "registry", "governance"]

    return {
        "mode": mode.value,
        "capabilities": [_ns.qualify(c) for c in caps],
    }
