"""Namespace manager — isolates plugin skills from host agent skills."""

from neoskills.core.mode import ExecutionMode


class NamespaceManager:
    """Manages skill name qualification based on execution mode.

    In plugin mode, all skill names are prefixed with 'plugin/<name>/'
    to avoid collisions with the host agent's own skills.
    In agent mode, names pass through unchanged.
    """

    def __init__(self, mode: ExecutionMode, plugin_name: str = "neoskills"):
        self.mode = mode
        self.plugin_name = plugin_name
        self._prefix = f"plugin/{plugin_name}/"

    def qualify(self, skill_name: str) -> str:
        """Add namespace prefix in plugin mode; pass through in agent mode.

        'find_skills' -> 'plugin/neoskills/find_skills' (plugin mode)
        'find_skills' -> 'find_skills' (agent mode)
        """
        if self.mode == ExecutionMode.AGENT:
            return skill_name
        if skill_name.startswith(self._prefix):
            return skill_name  # Already qualified
        return f"{self._prefix}{skill_name}"

    def is_own(self, qualified_name: str) -> bool:
        """Check if a qualified name belongs to this plugin's namespace."""
        return qualified_name.startswith(self._prefix)

    def strip(self, qualified_name: str) -> str:
        """Remove namespace prefix to get the bare skill name."""
        if qualified_name.startswith(self._prefix):
            return qualified_name[len(self._prefix):]
        return qualified_name
