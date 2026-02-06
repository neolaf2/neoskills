"""Base adapter ABC for agent ecosystem adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from neoskills.core.models import Skill, SkillFormat, Target


@dataclass
class DiscoveredSkill:
    """A skill found by an adapter during discovery."""

    skill_id: str
    name: str
    description: str
    path: Path
    is_directory: bool
    has_frontmatter: bool
    format: SkillFormat
    extra: dict[str, Any] | None = None


class BaseAdapter(ABC):
    """Abstract base class for agent ecosystem adapters."""

    @property
    @abstractmethod
    def agent_type(self) -> str:
        """Agent type identifier (e.g. 'claude-code')."""

    @abstractmethod
    def discover(self, target: Target) -> list[DiscoveredSkill]:
        """Scan target paths and discover skills."""

    @abstractmethod
    def export(self, target: Target, skill_ids: list[str]) -> list[tuple[str, str]]:
        """Export skills from target. Returns list of (skill_id, content)."""

    @abstractmethod
    def install(self, target: Target, skill_id: str, content: str) -> Path:
        """Install a skill to target. Returns installed path."""

    @abstractmethod
    def translate(self, skill: Skill, target: Target) -> str:
        """Translate skill content for target agent format."""
