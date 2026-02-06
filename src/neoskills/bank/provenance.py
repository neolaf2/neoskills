"""ProvenanceTracker - records where skills came from."""

from datetime import datetime
from pathlib import Path

import yaml

from neoskills.core.models import Provenance


class ProvenanceTracker:
    """Write and read provenance.yaml for each skill."""

    def __init__(self, bank_skills_dir: Path):
        self.bank_skills_dir = bank_skills_dir

    def _provenance_path(self, skill_id: str) -> Path:
        return self.bank_skills_dir / skill_id / "provenance.yaml"

    def record(self, provenance: Provenance) -> Path:
        """Record provenance for a skill."""
        path = self._provenance_path(provenance.skill_id)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "skill_id": provenance.skill_id,
            "source_type": provenance.source_type,
            "source_location": provenance.source_location,
            "source_target": provenance.source_target,
            "imported_at": provenance.imported_at.isoformat(),
            "original_checksum": provenance.original_checksum,
            "notes": provenance.notes,
        }
        path.write_text(yaml.dump(data, default_flow_style=False))
        return path

    def get(self, skill_id: str) -> Provenance | None:
        """Read provenance for a skill."""
        path = self._provenance_path(skill_id)
        if not path.exists():
            return None

        data = yaml.safe_load(path.read_text())
        return Provenance(
            skill_id=data["skill_id"],
            source_type=data["source_type"],
            source_location=data["source_location"],
            source_target=data.get("source_target", ""),
            imported_at=datetime.fromisoformat(data["imported_at"]),
            original_checksum=data.get("original_checksum", ""),
            notes=data.get("notes", ""),
        )

    def list_all(self) -> list[Provenance]:
        """List provenance for all skills."""
        results = []
        if not self.bank_skills_dir.exists():
            return results
        for skill_dir in sorted(self.bank_skills_dir.iterdir()):
            if skill_dir.is_dir():
                prov = self.get(skill_dir.name)
                if prov:
                    results.append(prov)
        return results
