"""Meta-skill enhancer - uses Claude to improve skills."""

from typing import Any

from neoskills.core.auth import AuthResolver

ENHANCE_OPERATIONS = {
    "normalize": "Normalize this skill to follow best practices: add proper YAML frontmatter "
    "(name, description, tags), organize sections, fix formatting.",
    "generate-variant": "Generate a variant of this skill adapted for {target_agent}. "
    "Preserve core functionality but adjust for the target agent's conventions.",
    "add-tests": "Generate test cases for this skill. Include edge cases, "
    "expected inputs/outputs, and validation criteria.",
    "add-docs": "Add comprehensive documentation: usage examples, prerequisites, "
    "limitations, and related skills.",
    "audit": "Audit this skill for quality: check for completeness, clarity, "
    "consistency, and potential improvements. Output a structured report.",
}


class Enhancer:
    """Uses Claude (via API key or SDK) to enhance skills."""

    def __init__(self) -> None:
        self.auth = AuthResolver().resolve()

    @property
    def available(self) -> bool:
        return self.auth.mode != "disabled"

    def enhance(
        self,
        content: str,
        operation: str,
        extra_context: dict[str, Any] | None = None,
    ) -> str:
        """Run an enhance operation on skill content. Returns enhanced output."""
        if not self.available:
            raise RuntimeError(
                "No API key or SDK available. "
                "Set ANTHROPIC_API_KEY in .env or install claude-agent-sdk."
            )

        instruction = ENHANCE_OPERATIONS.get(operation)
        if not instruction:
            raise ValueError(
                f"Unknown operation: {operation}. Available: {', '.join(ENHANCE_OPERATIONS.keys())}"
            )

        if extra_context:
            instruction = instruction.format(**extra_context)

        prompt = (
            f"You are a skill enhancement assistant. "
            f"Perform the following operation on the skill below.\n\n"
            f"## Operation\n{instruction}\n\n"
            f"## Skill Content\n```\n{content}\n```\n\n"
            f"Output the enhanced result directly (no extra explanation)."
        )

        return self._call_llm(prompt)

    def _call_llm(self, prompt: str) -> str:
        """Call Claude via API key or SDK."""
        if self.auth.mode == "api_key":
            return self._call_via_api(prompt)
        elif self.auth.mode == "sdk":
            return self._call_via_sdk(prompt)
        raise RuntimeError("No LLM backend available")

    def _call_via_api(self, prompt: str) -> str:
        """Call Claude via Anthropic API."""
        import anthropic

        client = anthropic.Anthropic(api_key=self.auth.api_key)
        response = client.messages.create(
            model=self._resolve_model(),
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def _call_via_sdk(self, prompt: str) -> str:
        """Call Claude via Agent SDK (subscription reuse)."""
        try:
            import claude_agent_sdk

            result = claude_agent_sdk.query(prompt)
            return result
        except Exception as e:
            raise RuntimeError(f"SDK call failed: {e}") from e

    def _resolve_model(self) -> str:
        """Resolve model name to API model ID."""
        model_map = {
            "sonnet": "claude-sonnet-4-5-20250929",
            "opus": "claude-opus-4-6",
            "haiku": "claude-haiku-4-5-20251001",
        }
        return model_map.get(self.auth.model, self.auth.model)
