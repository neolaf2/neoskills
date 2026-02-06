"""BundleManager - create and manage skill bundles."""

from datetime import datetime
from pathlib import Path

import yaml

from neoskills.core.models import Bundle
from neoskills.core.workspace import Workspace


class BundleManager:
    """Manages bundles in LTM/bank/bundles/."""

    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self.bundles_dir = workspace.bank_bundles

    def _bundle_dir(self, bundle_id: str) -> Path:
        return self.bundles_dir / bundle_id

    def _bundle_file(self, bundle_id: str) -> Path:
        return self._bundle_dir(bundle_id) / "bundle.yaml"

    def create(self, bundle: Bundle) -> Path:
        """Create a new bundle."""
        bdir = self._bundle_dir(bundle.bundle_id)
        bdir.mkdir(parents=True, exist_ok=True)

        data = {
            "bundle_id": bundle.bundle_id,
            "name": bundle.name,
            "description": bundle.description,
            "skill_ids": bundle.skill_ids,
            "created_at": bundle.created_at.isoformat(),
            "tags": bundle.tags,
        }
        path = self._bundle_file(bundle.bundle_id)
        path.write_text(yaml.dump(data, default_flow_style=False))
        return path

    def get(self, bundle_id: str) -> Bundle | None:
        """Get a bundle by ID."""
        path = self._bundle_file(bundle_id)
        if not path.exists():
            return None
        data = yaml.safe_load(path.read_text())
        return Bundle(
            bundle_id=data["bundle_id"],
            name=data["name"],
            description=data.get("description", ""),
            skill_ids=data.get("skill_ids", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            tags=data.get("tags", []),
        )

    def list_bundles(self) -> list[Bundle]:
        """List all bundles."""
        bundles = []
        if not self.bundles_dir.exists():
            return bundles
        for bdir in sorted(self.bundles_dir.iterdir()):
            if bdir.is_dir():
                b = self.get(bdir.name)
                if b:
                    bundles.append(b)
        return bundles

    def remove(self, bundle_id: str) -> bool:
        """Remove a bundle."""
        import shutil

        bdir = self._bundle_dir(bundle_id)
        if bdir.exists():
            shutil.rmtree(bdir)
            return True
        return False
