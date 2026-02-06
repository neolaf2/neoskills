"""Adapter factory - resolves agent type to adapter instance."""

from neoskills.adapters.base import BaseAdapter
from neoskills.adapters.claude.adapter import ClaudeCodeAdapter
from neoskills.adapters.opencode.adapter import OpenCodeAdapter
from neoskills.adapters.openclaw.adapter import OpenClawAdapter

_ADAPTERS: dict[str, type[BaseAdapter]] = {
    "claude-code": ClaudeCodeAdapter,
    "opencode": OpenCodeAdapter,
    "openclaw": OpenClawAdapter,
}


def get_adapter(agent_type: str) -> BaseAdapter:
    """Get adapter instance for an agent type."""
    cls = _ADAPTERS.get(agent_type)
    if cls is None:
        raise ValueError(
            f"No adapter for agent type '{agent_type}'. Available: {', '.join(_ADAPTERS.keys())}"
        )
    return cls()


def list_adapter_types() -> list[str]:
    """List available agent types."""
    return list(_ADAPTERS.keys())
