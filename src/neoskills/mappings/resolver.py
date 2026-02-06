"""SymlinkResolver - creates/removes symlinks for embed/unembed."""

import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml

from neoskills.core.workspace import Workspace


@dataclass
class SymlinkAction:
    """Record of a symlink operation."""

    skill_id: str
    source: Path  # Bank variant path
    target: Path  # Agent skill path
    backup: Path | None  # Backup location if original existed


class SymlinkResolver:
    """Manages symlink creation and removal for embed/unembed."""

    def __init__(self, workspace: Workspace):
        self.workspace = workspace

    def create_symlink(
        self, skill_id: str, bank_path: Path, agent_path: Path
    ) -> SymlinkAction:
        """Create a symlink from agent skill path to bank path.

        If the agent path already exists, backs it up to STM/scratch/.
        """
        backup = None

        if agent_path.exists() or agent_path.is_symlink():
            # Back up existing
            backup = self.workspace.scratch / f"backup_{skill_id}"
            backup.mkdir(parents=True, exist_ok=True)

            if agent_path.is_symlink():
                agent_path.unlink()
            elif agent_path.is_dir():
                if backup.exists():
                    shutil.rmtree(backup)
                shutil.copytree(agent_path, backup)
                shutil.rmtree(agent_path)
            elif agent_path.is_file():
                shutil.copy2(agent_path, backup / agent_path.name)
                agent_path.unlink()

        # Create symlink
        agent_path.parent.mkdir(parents=True, exist_ok=True)
        agent_path.symlink_to(bank_path)

        return SymlinkAction(
            skill_id=skill_id,
            source=bank_path,
            target=agent_path,
            backup=backup,
        )

    def remove_symlink(self, skill_id: str, agent_path: Path) -> bool:
        """Remove a symlink and restore backup if available."""
        if not agent_path.is_symlink():
            return False

        agent_path.unlink()

        # Check for backup
        backup = self.workspace.scratch / f"backup_{skill_id}"
        if backup.exists() and any(backup.iterdir()):
            # Determine if backup is a directory backup or a file backup
            children = list(backup.iterdir())
            if len(children) == 1 and children[0].is_file():
                # Single file backup - restore as file
                shutil.copy2(children[0], agent_path)
            else:
                # Directory backup - the backup IS the directory contents
                shutil.copytree(backup, agent_path)
            shutil.rmtree(backup)

        return True

    def save_state(self, actions: list[SymlinkAction]) -> None:
        """Record embed state to state.yaml."""
        state_file = self.workspace.state_file
        state = yaml.safe_load(state_file.read_text()) if state_file.exists() else {}
        embedded = state.setdefault("embedded", {})

        for action in actions:
            embedded[action.skill_id] = {
                "source": str(action.source),
                "target": str(action.target),
                "backup": str(action.backup) if action.backup else None,
            }

        state_file.write_text(yaml.dump(state, default_flow_style=False))

    def load_state(self) -> dict:
        """Load current embed state."""
        state_file = self.workspace.state_file
        if not state_file.exists():
            return {}
        state = yaml.safe_load(state_file.read_text()) or {}
        return state.get("embedded", {})

    def clear_state(self, skill_ids: list[str] | None = None) -> None:
        """Clear embed state for specified skills (or all)."""
        state_file = self.workspace.state_file
        if not state_file.exists():
            return
        state = yaml.safe_load(state_file.read_text()) or {}
        embedded = state.get("embedded", {})

        if skill_ids is None:
            state["embedded"] = {}
        else:
            for sid in skill_ids:
                embedded.pop(sid, None)

        state_file.write_text(yaml.dump(state, default_flow_style=False))
