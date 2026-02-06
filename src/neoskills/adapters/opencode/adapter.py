"""OpenCode adapter - discovers and manages skills in ~/.config/opencode/skills/."""

from pathlib import Path

from neoskills.adapters.base import BaseAdapter, DiscoveredSkill
from neoskills.core.frontmatter import parse_frontmatter
from neoskills.core.models import Skill, SkillFormat, Target


class OpenCodeAdapter(BaseAdapter):
    """Adapter for OpenCode skill ecosystem."""

    @property
    def agent_type(self) -> str:
        return "opencode"

    def discover(self, target: Target) -> list[DiscoveredSkill]:
        """Scan OpenCode skill directories."""
        discovered = []
        for path_str in target.discovery_paths:
            base = Path(path_str).expanduser()
            if not base.exists():
                continue

            for item in sorted(base.iterdir()):
                if item.name.startswith("."):
                    continue

                if item.is_dir():
                    skill_file = item / "SKILL.md"
                    if skill_file.exists():
                        content = skill_file.read_text()
                        fm, _ = parse_frontmatter(content)
                        discovered.append(DiscoveredSkill(
                            skill_id=item.name,
                            name=fm.get("name", item.name),
                            description=fm.get("description", ""),
                            path=item,
                            is_directory=True,
                            has_frontmatter=bool(fm),
                            format=SkillFormat.OPENCODE,
                        ))
                elif item.is_file() and item.suffix == ".md":
                    content = item.read_text()
                    fm, _ = parse_frontmatter(content)
                    discovered.append(DiscoveredSkill(
                        skill_id=item.stem,
                        name=fm.get("name", item.stem),
                        description=fm.get("description", ""),
                        path=item,
                        is_directory=False,
                        has_frontmatter=bool(fm),
                        format=SkillFormat.OPENCODE,
                    ))

        return discovered

    def export(self, target: Target, skill_ids: list[str]) -> list[tuple[str, str]]:
        results = []
        for skill_id in skill_ids:
            for path_str in target.discovery_paths:
                base = Path(path_str).expanduser()
                skill_file = base / skill_id / "SKILL.md"
                if skill_file.exists():
                    results.append((skill_id, skill_file.read_text()))
                    break
                alt = base / f"{skill_id}.md"
                if alt.exists():
                    results.append((skill_id, alt.read_text()))
                    break
        return results

    def install(self, target: Target, skill_id: str, content: str) -> Path:
        if not target.install_paths:
            raise ValueError(f"No install paths for target {target.target_id}")
        install_base = Path(target.install_paths[0]).expanduser()
        skill_dir = install_base / skill_id
        skill_dir.mkdir(parents=True, exist_ok=True)
        skill_file = skill_dir / "SKILL.md"
        skill_file.write_text(content)
        return skill_file

    def translate(self, skill: Skill, target: Target) -> str:
        return skill.content
