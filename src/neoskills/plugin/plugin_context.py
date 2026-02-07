"""Plugin execution context — runtime state when embedded in a host agent."""

from dataclasses import dataclass, field

from neoskills.core.mode import ExecutionMode
from neoskills.core.namespace import NamespaceManager


@dataclass
class PluginContext:
    """Execution context when running as an embedded plugin.

    Provides namespace isolation, capability restrictions, and scoped
    registry access for safe operation inside a host agent.
    """

    host_agent: str  # e.g. "claude-code", "opencode"
    namespace: NamespaceManager = field(init=False)
    capabilities: list[str] = field(
        default_factory=lambda: ["discover", "lifecycle", "evolution", "registry", "governance"]
    )
    registry_scope: str = "plugin"

    def __post_init__(self) -> None:
        self.namespace = NamespaceManager(mode=ExecutionMode.PLUGIN)

    def has_capability(self, cap: str) -> bool:
        """Check if this plugin context grants a specific capability."""
        return cap in self.capabilities

    def qualify(self, skill_name: str) -> str:
        """Namespace-qualify a skill name."""
        return self.namespace.qualify(skill_name)
