"""Registry capability — local/remote registry operations and sync."""

from __future__ import annotations

from neoskills.core.workspace import Workspace


def local_registry(root: str | None = None) -> dict:
    """List all skills in the local registry.

    Returns dict with 'count' and 'skills'.
    """
    from neoskills.bank.registry import Registry

    ws = Workspace() if root is None else Workspace(root)
    registry = Registry(ws)
    skills = registry.list_all()
    return {
        "count": len(skills),
        "skills": list(skills.keys()),
    }


def sync_registry(message: str = "Update skill bank", root: str | None = None) -> dict:
    """Commit the current workspace state to git.

    Returns dict with 'status' and 'message'.
    """
    import git

    ws = Workspace() if root is None else Workspace(root)

    try:
        repo = git.Repo(ws.root)
    except git.InvalidGitRepositoryError:
        repo = git.Repo.init(ws.root)

    from neoskills.cli.sync_cmd import _SAFE_PATHS

    for path_spec in _SAFE_PATHS:
        full = ws.root / path_spec
        if full.exists():
            repo.git.add(path_spec)

    try:
        has_staged = bool(repo.index.diff("HEAD"))
    except git.BadName:
        has_staged = bool(repo.index.entries)

    if not has_staged:
        return {"status": "clean", "message": "Nothing to commit"}

    repo.index.commit(message)
    return {"status": "committed", "message": message}
