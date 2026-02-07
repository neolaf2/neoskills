"""Domain models for neoskills."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any


class SkillFormat(Enum):
    """Skill file format conventions by agent."""

    CLAUDE_CODE = "claude-code"
    OPENCODE = "opencode"
    OPENCLAW = "openclaw"
    CANONICAL = "canonical"


class TransportType(Enum):
    """How skills are transferred to/from a target."""

    LOCAL_FS = "local-fs"
    SSH = "ssh"
    RSYNC = "rsync"
    ZIP = "zip"


@dataclass
class SkillMetadata:
    """Metadata extracted from a skill file."""

    name: str
    description: str = ""
    version: str = "0.1.0"
    author: str = ""
    tags: list[str] = field(default_factory=list)
    model: str = ""
    tools: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Skill:
    """A skill in the bank."""

    skill_id: str
    metadata: SkillMetadata
    content: str  # Raw file content (frontmatter + body)
    source_path: Path | None = None
    format: SkillFormat = SkillFormat.CANONICAL
    checksum: str = ""
    imported_at: datetime = field(default_factory=datetime.now)


@dataclass
class Provenance:
    """Tracks where a skill came from."""

    skill_id: str
    source_type: str  # "target", "git", "web", "manual"
    source_location: str  # path, URL, etc.
    source_target: str = ""  # target ID if from a target
    imported_at: datetime = field(default_factory=datetime.now)
    original_checksum: str = ""
    notes: str = ""


@dataclass
class Target:
    """A deployment target (agent instance)."""

    target_id: str
    agent_type: str  # "claude-code", "opencode", "openclaw"
    display_name: str = ""
    discovery_paths: list[str] = field(default_factory=list)
    install_paths: list[str] = field(default_factory=list)
    writable: bool = True
    transport: TransportType = TransportType.LOCAL_FS
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class Bundle:
    """A named collection of skills."""

    bundle_id: str
    name: str
    description: str = ""
    skill_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    tags: list[str] = field(default_factory=list)


# --- v0.3 Brew-style models ---


@dataclass
class SkillSpec:
    """Unified skill metadata derived entirely from SKILL.md frontmatter.

    Replaces the combination of Skill + SkillMetadata + Provenance.
    """

    skill_id: str
    name: str
    description: str = ""
    version: str = ""
    author: str = ""
    tags: list[str] = field(default_factory=list)
    targets: list[str] = field(default_factory=list)
    source: str = ""
    tools: list[str] = field(default_factory=list)
    model: str = ""
    tap: str = ""
    path: Path | None = None

    @classmethod
    def from_skill_dir(cls, skill_dir: Path, tap_name: str = "") -> "SkillSpec":
        """Parse a SkillSpec from a skill directory containing SKILL.md."""
        from neoskills.core.frontmatter import parse_frontmatter

        skill_md = skill_dir / "SKILL.md"
        if not skill_md.exists():
            raise FileNotFoundError(f"No SKILL.md in {skill_dir}")

        fm, _ = parse_frontmatter(skill_md.read_text())
        return cls(
            skill_id=skill_dir.name,
            name=fm.get("name", skill_dir.name),
            description=fm.get("description", ""),
            version=fm.get("version", ""),
            author=fm.get("author", ""),
            tags=fm.get("tags", []),
            targets=fm.get("targets", []),
            source=fm.get("source", tap_name),
            tools=fm.get("tools", []),
            model=fm.get("model", ""),
            tap=tap_name,
            path=skill_dir,
        )
