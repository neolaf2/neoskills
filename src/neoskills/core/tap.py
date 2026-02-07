"""TapManager - clone, pull, search, and list skills across taps."""

import shutil
from pathlib import Path
from typing import Any

from neoskills.core.cellar import Cellar
from neoskills.core.frontmatter import parse_frontmatter


class TapManager:
    """Manages tap repositories (git clones under ~/.neoskills/taps/)."""

    def __init__(self, cellar: Cellar):
        self.cellar = cellar

    # --- Tap CRUD ---

    def add(self, name: str, url: str, branch: str = "main") -> Path:
        """Clone a tap repo. Returns the tap directory."""
        import git

        tap_dir = self.cellar.tap_dir(name)
        if tap_dir.exists():
            raise FileExistsError(f"Tap '{name}' already exists at {tap_dir}")

        git.Repo.clone_from(url, tap_dir, branch=branch, depth=1)

        # Register in config
        config = self.cellar.load_config()
        taps = config.setdefault("taps", {})
        taps[name] = {"url": url, "branch": branch}
        if not any(t.get("default") for t in taps.values()):
            taps[name]["default"] = True
        self.cellar.save_config(config)

        return tap_dir

    def remove(self, name: str) -> bool:
        """Remove a tap repo and unregister it."""
        tap_dir = self.cellar.tap_dir(name)
        if not tap_dir.exists():
            return False

        shutil.rmtree(tap_dir)

        config = self.cellar.load_config()
        config.get("taps", {}).pop(name, None)
        self.cellar.save_config(config)
        return True

    def update(self, name: str | None = None) -> list[str]:
        """Git pull one or all taps. Returns list of updated tap names."""
        import git

        updated = []
        taps = self.list_taps() if name is None else [name]

        for tap_name in taps:
            tap_dir = self.cellar.tap_dir(tap_name)
            if not tap_dir.exists():
                continue
            try:
                repo = git.Repo(tap_dir)
                origin = repo.remotes.origin
                info = origin.pull()
                if info and info[0].flags != info[0].HEAD_UPTODATE:
                    updated.append(tap_name)
                else:
                    updated.append(tap_name)  # still counts as "checked"
            except Exception:
                pass  # skip taps with git issues

        return updated

    # --- Query ---

    def list_taps(self) -> list[str]:
        """List registered tap names."""
        if not self.cellar.taps_dir.exists():
            return []
        return sorted(
            d.name
            for d in self.cellar.taps_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        )

    def list_skills(self, tap_name: str | None = None) -> list[dict[str, Any]]:
        """List all skills in a tap (or default tap). Returns list of SkillSpec-like dicts."""
        tap_name = tap_name or self.cellar.default_tap
        skills_dir = self.cellar.tap_skills_dir(tap_name)
        if not skills_dir.exists():
            return []

        results = []
        for skill_dir in sorted(skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            fm, _ = parse_frontmatter(skill_md.read_text())
            results.append({
                "skill_id": skill_dir.name,
                "name": fm.get("name", skill_dir.name),
                "description": fm.get("description", ""),
                "version": fm.get("version", ""),
                "author": fm.get("author", ""),
                "tags": fm.get("tags", []),
                "targets": fm.get("targets", []),
                "source": fm.get("source", tap_name),
                "tap": tap_name,
                "path": skill_dir,
            })
        return results

    def get_skill_path(self, skill_id: str, tap_name: str | None = None) -> Path | None:
        """Find a skill's directory in a tap (or search all taps)."""
        if tap_name:
            path = self.cellar.tap_skills_dir(tap_name) / skill_id
            return path if path.exists() and (path / "SKILL.md").exists() else None

        # Search all taps, default first
        default = self.cellar.default_tap
        taps = [default] + [t for t in self.list_taps() if t != default]
        for tn in taps:
            path = self.cellar.tap_skills_dir(tn) / skill_id
            if path.exists() and (path / "SKILL.md").exists():
                return path
        return None

    def search(self, query: str) -> list[dict[str, Any]]:
        """Search skills across all taps by name/description/tags."""
        query_lower = query.lower()
        results = []
        for tap_name in self.list_taps():
            for skill in self.list_skills(tap_name):
                text = f"{skill['skill_id']} {skill['name']} {skill['description']} {' '.join(skill['tags'])}".lower()
                if query_lower in text:
                    results.append(skill)
        return results
