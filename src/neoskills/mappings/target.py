"""TargetManager - CRUD for target definitions, built-in targets created at init."""

from pathlib import Path
from typing import Any

import yaml

from neoskills.core.models import Target, TransportType
from neoskills.core.workspace import Workspace


# Built-in target definitions
BUILTIN_TARGETS: list[dict[str, Any]] = [
    {
        "target_id": "claude-code-user",
        "agent_type": "claude-code",
        "display_name": "Claude Code (User Skills)",
        "discovery_paths": ["~/.claude/skills"],
        "install_paths": ["~/.claude/skills"],
        "writable": True,
        "transport": "local-fs",
    },
    {
        "target_id": "claude-code-plugins",
        "agent_type": "claude-code",
        "display_name": "Claude Code (Plugin Skills)",
        "discovery_paths": ["~/.claude/plugins/*/skills"],
        "install_paths": [],
        "writable": False,
        "transport": "local-fs",
    },
    {
        "target_id": "opencode-local",
        "agent_type": "opencode",
        "display_name": "OpenCode (Local)",
        "discovery_paths": ["~/.config/opencode/skills"],
        "install_paths": ["~/.config/opencode/skills"],
        "writable": True,
        "transport": "local-fs",
    },
    {
        "target_id": "openclaw-custom",
        "agent_type": "openclaw",
        "display_name": "OpenClaw (Custom Skills)",
        "discovery_paths": [],
        "install_paths": [],
        "writable": True,
        "transport": "local-fs",
    },
]


class TargetManager:
    """Manages target definitions in LTM/mappings/targets/."""

    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self.targets_dir = workspace.mappings_targets

    def _target_file(self, target_id: str) -> Path:
        return self.targets_dir / f"{target_id}.yaml"

    def ensure_builtins(self) -> list[str]:
        """Create built-in target definitions if they don't exist. Returns created IDs."""
        created = []
        for defn in BUILTIN_TARGETS:
            path = self._target_file(defn["target_id"])
            if not path.exists():
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(yaml.dump(defn, default_flow_style=False))
                created.append(defn["target_id"])
        return created

    def add(self, target: Target) -> Path:
        """Add a new target definition."""
        data = {
            "target_id": target.target_id,
            "agent_type": target.agent_type,
            "display_name": target.display_name,
            "discovery_paths": target.discovery_paths,
            "install_paths": target.install_paths,
            "writable": target.writable,
            "transport": target.transport.value,
        }
        if target.extra:
            data["extra"] = target.extra
        path = self._target_file(target.target_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.dump(data, default_flow_style=False))
        return path

    def get(self, target_id: str) -> Target | None:
        """Get a target by ID."""
        path = self._target_file(target_id)
        if not path.exists():
            return None
        data = yaml.safe_load(path.read_text())
        return Target(
            target_id=data["target_id"],
            agent_type=data["agent_type"],
            display_name=data.get("display_name", ""),
            discovery_paths=data.get("discovery_paths", []),
            install_paths=data.get("install_paths", []),
            writable=data.get("writable", True),
            transport=TransportType(data.get("transport", "local-fs")),
            extra=data.get("extra", {}),
        )

    def list_targets(self) -> list[Target]:
        """List all configured targets."""
        targets = []
        if not self.targets_dir.exists():
            return targets
        for f in sorted(self.targets_dir.glob("*.yaml")):
            data = yaml.safe_load(f.read_text())
            targets.append(
                Target(
                    target_id=data["target_id"],
                    agent_type=data["agent_type"],
                    display_name=data.get("display_name", ""),
                    discovery_paths=data.get("discovery_paths", []),
                    install_paths=data.get("install_paths", []),
                    writable=data.get("writable", True),
                    transport=TransportType(data.get("transport", "local-fs")),
                    extra=data.get("extra", {}),
                )
            )
        return targets

    def remove(self, target_id: str) -> bool:
        """Remove a target definition."""
        path = self._target_file(target_id)
        if path.exists():
            path.unlink()
            return True
        return False
