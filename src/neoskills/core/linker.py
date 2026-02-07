"""Linker - manages flat per-skill symlinks from targets to tap skills."""

import shutil
from dataclasses import dataclass
from pathlib import Path

from neoskills.core.cellar import Cellar


@dataclass
class LinkAction:
    """Record of a link operation."""

    skill_id: str
    source: Path  # Tap skill path
    target: Path  # Agent skill path
    action: str  # "linked", "unlinked", "skipped", "broken"


class Linker:
    """Manages per-skill symlinks from target directories to tap skills.

    No state.yaml — derives all state from filesystem inspection.
    """

    def __init__(self, cellar: Cellar):
        self.cellar = cellar

    def link(
        self,
        skill_id: str,
        source_path: Path,
        target: str | None = None,
    ) -> LinkAction:
        """Create a symlink for one skill in the target directory."""
        target_dir = self.cellar.target_path(target)
        target_dir.mkdir(parents=True, exist_ok=True)
        link_path = target_dir / skill_id

        if link_path.is_symlink():
            # Already linked — check if pointing to same source
            if link_path.resolve() == source_path.resolve():
                return LinkAction(skill_id, source_path, link_path, "skipped")
            link_path.unlink()
        elif link_path.exists():
            # Real directory exists — back up and replace
            backup = self.cellar.cache_dir / f"backup_{skill_id}"
            if backup.exists():
                shutil.rmtree(backup)
            shutil.move(str(link_path), str(backup))

        link_path.symlink_to(source_path)
        return LinkAction(skill_id, source_path, link_path, "linked")

    def unlink(self, skill_id: str, target: str | None = None) -> LinkAction:
        """Remove a symlink for one skill from the target directory."""
        target_dir = self.cellar.target_path(target)
        link_path = target_dir / skill_id

        if not link_path.is_symlink():
            return LinkAction(skill_id, Path(), link_path, "skipped")

        source = link_path.resolve()
        link_path.unlink()
        return LinkAction(skill_id, source, link_path, "unlinked")

    def link_all(
        self,
        skills_dir: Path,
        target: str | None = None,
    ) -> list[LinkAction]:
        """Link all skills from a directory to the target."""
        actions = []
        if not skills_dir.exists():
            return actions
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").exists():
                continue
            actions.append(self.link(skill_dir.name, skill_dir, target))
        return actions

    def unlink_all(self, target: str | None = None) -> list[LinkAction]:
        """Unlink all neoskills-managed symlinks from the target."""
        actions = []
        target_dir = self.cellar.target_path(target)
        if not target_dir.exists():
            return actions
        for item in sorted(target_dir.iterdir()):
            if item.is_symlink():
                # Only unlink symlinks that point into our taps
                resolved = item.resolve()
                if str(self.cellar.taps_dir) in str(resolved):
                    actions.append(self.unlink(item.name, target))
        return actions

    def list_links(self, target: str | None = None) -> list[dict]:
        """List all skills in a target directory with link status."""
        target_dir = self.cellar.target_path(target)
        if not target_dir.exists():
            return []

        results = []
        for item in sorted(target_dir.iterdir()):
            if item.is_symlink():
                resolved = item.resolve()
                managed = str(self.cellar.taps_dir) in str(resolved)
                broken = not resolved.exists()
                results.append({
                    "skill_id": item.name,
                    "linked": True,
                    "managed": managed,
                    "broken": broken,
                    "source": str(resolved),
                })
            elif item.is_dir() and (item / "SKILL.md").exists():
                results.append({
                    "skill_id": item.name,
                    "linked": False,
                    "managed": False,
                    "broken": False,
                    "source": str(item),
                })
        return results

    def check_health(self, target: str | None = None) -> dict:
        """Check symlink health. Returns dict with issues."""
        links = self.list_links(target)
        broken = [l for l in links if l["broken"]]
        unmanaged = [l for l in links if not l["managed"] and l["linked"]]
        healthy = [l for l in links if l["linked"] and not l["broken"] and l["managed"]]
        local = [l for l in links if not l["linked"]]

        return {
            "total": len(links),
            "healthy": len(healthy),
            "broken": broken,
            "unmanaged": unmanaged,
            "local": local,
        }
