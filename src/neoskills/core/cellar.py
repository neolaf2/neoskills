"""Cellar - manages the ~/.neoskills/ workspace (simplified from Workspace)."""

from pathlib import Path
from typing import Any

import yaml


# Default config for a fresh workspace
_DEFAULT_CONFIG: dict[str, Any] = {
    "version": "0.3.0",
    "default_tap": "mySkills",
    "default_target": "claude-code",
    "targets": {
        "claude-code": {"skill_path": "~/.claude/skills"},
        "opencode": {"skill_path": "~/.config/opencode/skills"},
    },
    "taps": {},
    "auth": {"mode": "auto"},
}


class Cellar:
    """Manages the ~/.neoskills/ directory tree.

    Simplified from Workspace — no LTM/STM/bank/mappings hierarchy.
    Skills live directly in taps (git clones); symlinks point to them.
    """

    def __init__(self, root: Path | None = None):
        self.root = root or Path.home() / ".neoskills"

    # --- Directory paths ---

    @property
    def taps_dir(self) -> Path:
        return self.root / "taps"

    @property
    def cache_dir(self) -> Path:
        return self.root / "cache"

    @property
    def config_file(self) -> Path:
        return self.root / "config.yaml"

    @property
    def gitignore_file(self) -> Path:
        return self.root / ".gitignore"

    # --- Tap helpers ---

    def tap_dir(self, tap_name: str) -> Path:
        return self.taps_dir / tap_name

    def tap_skills_dir(self, tap_name: str) -> Path:
        return self.tap_dir(tap_name) / "skills"

    def tap_plugins_dir(self, tap_name: str) -> Path:
        return self.tap_dir(tap_name) / "plugins"

    @property
    def default_tap(self) -> str:
        config = self.load_config()
        return config.get("default_tap", "mySkills")

    @property
    def default_tap_skills_dir(self) -> Path:
        return self.tap_skills_dir(self.default_tap)

    # --- Config ---

    def load_config(self) -> dict[str, Any]:
        if self.config_file.exists():
            return yaml.safe_load(self.config_file.read_text()) or {}
        return dict(_DEFAULT_CONFIG)

    def save_config(self, config: dict[str, Any]) -> None:
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        self.config_file.write_text(yaml.dump(config, default_flow_style=False))

    def target_path(self, target: str | None = None) -> Path:
        """Resolve the skill_path for a target (defaults to default_target)."""
        config = self.load_config()
        target = target or config.get("default_target", "claude-code")
        targets = config.get("targets", {})
        path_str = targets.get(target, {}).get("skill_path", "~/.claude/skills")
        return Path(path_str).expanduser()

    # --- Initialization ---

    @property
    def is_initialized(self) -> bool:
        return self.root.exists() and self.config_file.exists()

    def initialize(self) -> dict[str, list[Path]]:
        """Create workspace directories and default config."""
        created_dirs = []
        for d in [self.root, self.taps_dir, self.cache_dir]:
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                created_dirs.append(d)

        created_files = []
        if not self.config_file.exists():
            self.save_config(dict(_DEFAULT_CONFIG))
            created_files.append(self.config_file)

        if not self.gitignore_file.exists():
            self.gitignore_file.write_text(
                "# Ephemeral\ncache/\n\n# Secrets\n.env\n"
            )
            created_files.append(self.gitignore_file)

        return {"directories": created_dirs, "files": created_files}
