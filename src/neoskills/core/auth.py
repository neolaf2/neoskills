"""Authentication resolver - .env -> SDK -> disable chain."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass
class AuthResult:
    """Result of auth resolution."""

    mode: str  # "api_key", "sdk", "disabled"
    api_key: str | None = None
    model: str = "sonnet"
    message: str = ""


class AuthResolver:
    """Resolves authentication following the priority chain:
    1. .env API key (from cwd, .neoskills/, ~/.neoskills/)
    2. Claude Agent SDK subscription reuse
    3. Disabled (non-LLM features still work)
    """

    ENV_SEARCH_PATHS = [
        Path.cwd() / ".env",
        Path.cwd() / ".neoskills" / ".env",
        Path.home() / ".neoskills" / ".env",
    ]

    def resolve(self) -> AuthResult:
        """Resolve authentication mode."""
        # 1. Try .env files
        for env_path in self.ENV_SEARCH_PATHS:
            if env_path.exists():
                load_dotenv(env_path, override=True)
                break

        api_key = os.environ.get("CLAUDE_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
        model = os.environ.get("CLAUDE_MODEL", "sonnet")

        if api_key:
            return AuthResult(
                mode="api_key",
                api_key=api_key,
                model=model,
                message=f"Using API key (model: {model})",
            )

        # 2. Try SDK subscription reuse
        if self._sdk_available():
            return AuthResult(
                mode="sdk",
                model=model,
                message="Using Claude subscription via SDK",
            )

        # 3. Disable LLM features
        return AuthResult(
            mode="disabled",
            message="No API key or SDK found. LLM features disabled.",
        )

    @staticmethod
    def _sdk_available() -> bool:
        """Check if claude-agent-sdk is importable."""
        try:
            import claude_agent_sdk  # noqa: F401

            return True
        except ImportError:
            return False
