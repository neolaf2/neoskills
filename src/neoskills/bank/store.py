"""SkillStore - manages skills in the canonical bank."""

import shutil
from pathlib import Path
from typing import Any

import yaml

from neoskills.core.checksum import checksum_string
from neoskills.core.frontmatter import parse_frontmatter
from neoskills.core.models import Skill, SkillFormat, SkillMetadata
from neoskills.core.workspace import Workspace


class SkillStore:
    """Add, get, list, and remove skills in the bank."""

    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self.skills_dir = workspace.bank_skills

    def skill_dir(self, skill_id: str) -> Path:
        return self.skills_dir / skill_id

    def canonical_dir(self, skill_id: str) -> Path:
        return self.skill_dir(skill_id) / "canonical"

    def variants_dir(self, skill_id: str) -> Path:
        return self.skill_dir(skill_id) / "variants"

    def variant_dir(self, skill_id: str, agent_type: str) -> Path:
        return self.variants_dir(skill_id) / agent_type

    def metadata_file(self, skill_id: str) -> Path:
        return self.skill_dir(skill_id) / "metadata.yaml"

    def provenance_file(self, skill_id: str) -> Path:
        return self.skill_dir(skill_id) / "provenance.yaml"

    def add(
        self,
        skill_id: str,
        content: str,
        source_format: SkillFormat = SkillFormat.CANONICAL,
        metadata_overrides: dict[str, Any] | None = None,
    ) -> Skill:
        """Add a skill to the bank. Stores canonical copy and optional variant."""
        # Create directory structure
        canonical = self.canonical_dir(skill_id)
        canonical.mkdir(parents=True, exist_ok=True)

        # Write canonical SKILL.md
        skill_file = canonical / "SKILL.md"
        skill_file.write_text(content)

        # If source is from a specific agent, also store as variant
        if source_format != SkillFormat.CANONICAL:
            variant = self.variant_dir(skill_id, source_format.value)
            variant.mkdir(parents=True, exist_ok=True)
            (variant / "SKILL.md").write_text(content)

        # Parse metadata
        fm, body = parse_frontmatter(content)
        meta = SkillMetadata(
            name=fm.get("name", skill_id),
            description=fm.get("description", ""),
            version=fm.get("version", "0.1.0"),
            author=fm.get("author", ""),
            tags=fm.get("tags", []),
            model=fm.get("model", ""),
            tools=fm.get("tools", []),
            extra={k: v for k, v in fm.items() if k not in {
                "name", "description", "version", "author", "tags", "model", "tools"
            }},
        )
        if metadata_overrides:
            for k, v in metadata_overrides.items():
                if hasattr(meta, k):
                    setattr(meta, k, v)

        # Write metadata.yaml
        meta_dict = {
            "name": meta.name,
            "description": meta.description,
            "version": meta.version,
            "author": meta.author,
            "tags": meta.tags,
            "format": source_format.value,
            "checksum": checksum_string(content),
        }
        self.metadata_file(skill_id).write_text(
            yaml.dump(meta_dict, default_flow_style=False)
        )

        return Skill(
            skill_id=skill_id,
            metadata=meta,
            content=content,
            format=source_format,
            checksum=checksum_string(content),
        )

    def get(self, skill_id: str) -> Skill | None:
        """Get a skill by ID."""
        skill_file = self.canonical_dir(skill_id) / "SKILL.md"
        if not skill_file.exists():
            return None

        content = skill_file.read_text()
        fm, _ = parse_frontmatter(content)
        meta = SkillMetadata(
            name=fm.get("name", skill_id),
            description=fm.get("description", ""),
            version=fm.get("version", "0.1.0"),
            author=fm.get("author", ""),
            tags=fm.get("tags", []),
            model=fm.get("model", ""),
            tools=fm.get("tools", []),
        )

        return Skill(
            skill_id=skill_id,
            metadata=meta,
            content=content,
            checksum=checksum_string(content),
        )

    def list_skills(self) -> list[str]:
        """List all skill IDs in the bank."""
        if not self.skills_dir.exists():
            return []
        return sorted(
            d.name
            for d in self.skills_dir.iterdir()
            if d.is_dir() and (d / "canonical" / "SKILL.md").exists()
        )

    def list_variants(self, skill_id: str) -> list[str]:
        """List variant agent types for a skill."""
        variants = self.variants_dir(skill_id)
        if not variants.exists():
            return []
        return sorted(d.name for d in variants.iterdir() if d.is_dir())

    def remove(self, skill_id: str) -> bool:
        """Remove a skill from the bank."""
        skill_dir = self.skill_dir(skill_id)
        if skill_dir.exists():
            shutil.rmtree(skill_dir)
            return True
        return False

    def get_variant_content(self, skill_id: str, agent_type: str) -> str | None:
        """Get variant content for a specific agent type."""
        variant_file = self.variant_dir(skill_id, agent_type) / "SKILL.md"
        if variant_file.exists():
            return variant_file.read_text()
        return None

    def add_variant(self, skill_id: str, agent_type: str, content: str) -> Path:
        """Add or update a variant for a skill."""
        variant = self.variant_dir(skill_id, agent_type)
        variant.mkdir(parents=True, exist_ok=True)
        skill_file = variant / "SKILL.md"
        skill_file.write_text(content)
        return skill_file
