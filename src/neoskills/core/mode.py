"""Execution mode detection — agent (standalone) vs plugin (embedded)."""

import os
from enum import Enum


class ExecutionMode(Enum):
    AGENT = "agent"    # Mode A: neoskills as top-level agent
    PLUGIN = "plugin"  # Mode B: neoskills embedded in a host agent


def detect_mode() -> ExecutionMode:
    """Detect the current execution mode.

    Priority:
      1. NEOSKILLS_MODE env var ('agent' or 'plugin')
      2. Presence of host agent markers (e.g. CLAUDE_CODE_ENTRY)
      3. Default: AGENT
    """
    env_mode = os.environ.get("NEOSKILLS_MODE", "").lower()
    if env_mode == "plugin":
        return ExecutionMode.PLUGIN
    if env_mode == "agent":
        return ExecutionMode.AGENT

    # Auto-detect: if running inside Claude Code plugin context
    if os.environ.get("CLAUDE_CODE_ENTRY"):
        return ExecutionMode.PLUGIN

    return ExecutionMode.AGENT
