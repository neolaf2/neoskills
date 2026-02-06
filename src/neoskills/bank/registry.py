"""Registry - master catalog of skills in registry.yaml."""

from datetime import datetime
from typing import Any

import yaml

from neoskills.core.models import Skill
from neoskills.core.workspace import Workspace


class Registry:
    """Master catalog stored in registry.yaml."""

    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self.path = workspace.registry_file
        self._data: dict[str, Any] = self._load()

    def _load(self) -> dict[str, Any]:
        if self.path.exists():
            return yaml.safe_load(self.path.read_text()) or {}
        return {"version": "0.1.0", "skills": {}, "updated_at": ""}

    def save(self) -> None:
        self._data["updated_at"] = datetime.now().isoformat()
        self.path.write_text(yaml.dump(self._data, default_flow_style=False))

    def register(self, skill: Skill) -> None:
        """Register a skill in the catalog."""
        self._data.setdefault("skills", {})[skill.skill_id] = {
            "name": skill.metadata.name,
            "description": skill.metadata.description,
            "version": skill.metadata.version,
            "tags": skill.metadata.tags,
            "checksum": skill.checksum,
            "registered_at": datetime.now().isoformat(),
        }
        self.save()

    def unregister(self, skill_id: str) -> bool:
        """Remove a skill from the catalog."""
        skills = self._data.get("skills", {})
        if skill_id in skills:
            del skills[skill_id]
            self.save()
            return True
        return False

    def get(self, skill_id: str) -> dict[str, Any] | None:
        """Get registry entry for a skill."""
        return self._data.get("skills", {}).get(skill_id)

    def list_all(self) -> dict[str, dict[str, Any]]:
        """List all registered skills."""
        return self._data.get("skills", {})

    def search(self, query: str) -> dict[str, dict[str, Any]]:
        """Search skills by name, description, or tags."""
        query_lower = query.lower()
        results = {}
        for skill_id, info in self._data.get("skills", {}).items():
            if (
                query_lower in skill_id.lower()
                or query_lower in info.get("name", "").lower()
                or query_lower in info.get("description", "").lower()
                or any(query_lower in t.lower() for t in info.get("tags", []))
            ):
                results[skill_id] = info
        return results
