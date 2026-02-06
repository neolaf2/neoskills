"""Claude Code adapter - discovers and manages skills in ~/.claude/skills/."""

from pathlib import Path

from neoskills.adapters.base import BaseAdapter, DiscoveredSkill
from neoskills.core.frontmatter import parse_frontmatter
from neoskills.core.models import Skill, SkillFormat, Target


class ClaudeCodeAdapter(BaseAdapter):
    """Adapter for Claude Code skill ecosystem."""

    @property
    def agent_type(self) -> str:
        return "claude-code"

    def discover(self, target: Target) -> list[DiscoveredSkill]:
        """Scan Claude Code skill directories."""
        discovered = []

        for path_str in target.discovery_paths:
            base = Path(path_str).expanduser()
            if not base.exists():
                continue

            for item in sorted(base.iterdir()):
                skill = self._inspect_item(item)
                if skill:
                    discovered.append(skill)

        return discovered

    def _inspect_item(self, item: Path) -> DiscoveredSkill | None:
        """Inspect a file or directory to see if it's a skill."""
        if item.name.startswith("."):
            return None

        # Directory with SKILL.md
        if item.is_dir():
            skill_file = item / "SKILL.md"
            if skill_file.exists():
                content = skill_file.read_text()
                fm, body = parse_frontmatter(content)
                return DiscoveredSkill(
                    skill_id=item.name,
                    name=fm.get("name", item.name),
                    description=fm.get("description", ""),
                    path=item,
                    is_directory=True,
                    has_frontmatter=bool(fm),
                    format=SkillFormat.CLAUDE_CODE,
                )
            return None

        # Standalone .md file (skill)
        if item.is_file() and item.suffix == ".md":
            content = item.read_text()
            fm, body = parse_frontmatter(content)
            skill_id = item.stem
            return DiscoveredSkill(
                skill_id=skill_id,
                name=fm.get("name", skill_id),
                description=fm.get("description", ""),
                path=item,
                is_directory=False,
                has_frontmatter=bool(fm),
                format=SkillFormat.CLAUDE_CODE,
            )

        return None

    def export(self, target: Target, skill_ids: list[str]) -> list[tuple[str, str]]:
        """Export skills from Claude Code target."""
        results = []
        for skill_id in skill_ids:
            content = self._read_skill_content(target, skill_id)
            if content is not None:
                results.append((skill_id, content))
        return results

    def _read_skill_content(self, target: Target, skill_id: str) -> str | None:
        """Read skill content from target paths."""
        for path_str in target.discovery_paths:
            base = Path(path_str).expanduser()

            # Try directory with SKILL.md
            skill_dir = base / skill_id
            if skill_dir.is_dir():
                skill_file = skill_dir / "SKILL.md"
                if skill_file.exists():
                    return skill_file.read_text()

            # Try standalone .md file
            skill_file = base / f"{skill_id}.md"
            if skill_file.is_file():
                return skill_file.read_text()

        return None

    def install(self, target: Target, skill_id: str, content: str) -> Path:
        """Install a skill to Claude Code target."""
        if not target.install_paths:
            raise ValueError(f"No install paths configured for target {target.target_id}")

        install_base = Path(target.install_paths[0]).expanduser()
        install_base.mkdir(parents=True, exist_ok=True)

        skill_dir = install_base / skill_id
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content)
        return skill_file

    def translate(self, skill: Skill, target: Target) -> str:
        """Claude Code uses native markdown+frontmatter - minimal translation needed."""
        return skill.content
