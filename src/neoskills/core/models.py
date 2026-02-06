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
