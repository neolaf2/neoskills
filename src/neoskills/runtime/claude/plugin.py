"""Claude Code MCP tools for neoskills embedded plugin mode.

These tools are exposed via the MCP protocol so Claude Code can invoke
neoskills operations directly as tool calls. In plugin mode, results
are namespace-qualified to avoid collisions with host agent skills.
"""

from neoskills.core.cellar import Cellar
from neoskills.core.linker import Linker
from neoskills.core.mode import detect_mode
from neoskills.core.namespace import NamespaceManager
from neoskills.core.tap import TapManager

_ns = NamespaceManager(mode=detect_mode())


def neoskills_list(query: str = "") -> dict:
    """List skills in taps, optionally filtered by query.

    Args:
        query: Optional search query to filter skills by name/description/tags.

    Returns:
        Dictionary with skill list and count.
    """
    cellar = Cellar()
    mgr = TapManager(cellar)

    if query:
        results = mgr.search(query)
        return {
            "mode": detect_mode().value,
            "count": len(results),
            "skills": [
                {
                    "id": _ns.qualify(s.skill_id),
                    "name": s.name,
                    "description": s.description,
                }
                for s in results
            ],
        }

    default_tap = cellar.default_tap
    skills = mgr.list_skills(default_tap)
    return {
        "mode": detect_mode().value,
        "count": len(skills),
        "skills": [
            {
                "id": _ns.qualify(s["skill_id"]),
                "name": s.get("name", s["skill_id"]),
                "description": s.get("description", ""),
            }
            for s in skills
        ],
    }


def neoskills_scan(target: str | None = None) -> dict:
    """Scan a target for linked skills.

    Args:
        target: Target to scan (default: from config).

    Returns:
        Dictionary with discovered skills.
    """
    cellar = Cellar()
    linker = Linker(cellar)
    links = linker.list_links(target)

    return {
        "target": target or cellar.load_config().get("default_target", "claude-code"),
        "count": len(links),
        "skills": [
            {"id": l["skill_id"], "is_symlink": l["is_symlink"], "source": l.get("source", "")}
            for l in links
        ],
    }


def neoskills_deploy(skill_id: str, target: str | None = None) -> dict:
    """Link a skill from the default tap to a target.

    Args:
        skill_id: Skill to link (bare or namespace-qualified).
        target: Target to link to.

    Returns:
        Dictionary with link result.
    """
    bare_id = _ns.strip(skill_id)

    cellar = Cellar()
    mgr = TapManager(cellar)
    linker = Linker(cellar)

    source = mgr.get_skill_path(bare_id)
    if not source:
        return {"error": f"Skill '{bare_id}' not found in any tap"}

    action = linker.link(bare_id, source, target)
    return {
        "status": action.action,
        "skill_id": _ns.qualify(bare_id),
        "path": str(action.link_path),
    }


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

    cellar = Cellar()
    mgr = TapManager(cellar)
    skill_path = mgr.get_skill_path(bare_id)

    if not skill_path:
        return {"error": f"Skill '{bare_id}' not found in any tap"}

    skill_md = skill_path / "SKILL.md"
    if not skill_md.exists():
        return {"error": f"No SKILL.md found for '{bare_id}'"}

    enhancer = Enhancer()
    if not enhancer.available:
        return {"error": "No LLM backend available"}

    try:
        result = enhancer.enhance(skill_md.read_text(), operation)
        return {"status": "success", "operation": operation, "result": result}
    except Exception as e:
        return {"error": str(e)}


def neoskills_capabilities() -> dict:
    """List available capability groups in the current execution mode.

    Returns:
        Dictionary with mode and available capabilities.
    """
    mode = detect_mode()
    caps = ["list", "scan", "deploy", "enhance", "doctor"]

    return {
        "mode": mode.value,
        "capabilities": [_ns.qualify(c) for c in caps],
    }
