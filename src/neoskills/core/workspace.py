"""Workspace manager - creates and manages the ~/.neoskills/ directory tree."""

from pathlib import Path

# Default myMemory templates
MY_MEMORY_TEMPLATES: dict[str, str] = {
    "AGENTS.md": (
        "# Agent Operating Instructions\n\n"
        "Accumulated memory and instructions for your agents.\n"
        "Edit freely — neoskills will never overwrite this file.\n"
    ),
    "SOUL.md": ("# Soul\n\nDefine your agent's persona, boundaries, and tone.\n"),
    "TOOLS.md": ("# Tools\n\nNotes on tools, conventions, and integrations you use.\n"),
    "BOOTSTRAP.md": (
        "# Bootstrap\n\n"
        "First-run ritual. This file is deleted after initial setup.\n"
        "Use it to define one-time onboarding steps.\n"
    ),
    "IDENTITY.md": (
        "# Identity\n\nAgent name, vibe, and emoji.\n\n- Name: \n- Emoji: \n- Vibe: \n"
    ),
    "USER.md": (
        "# User Profile\n\n"
        "Your preferences and context for agents to use.\n"
        "\n- Name: \n- Role: \n- Preferences: \n"
    ),
}


class Workspace:
    """Manages the ~/.neoskills/ directory tree."""

    def __init__(self, root: Path | None = None):
        self.root = root or Path.home() / ".neoskills"

    # --- Top-level paths ---

    @property
    def ltm(self) -> Path:
        return self.root / "LTM"

    @property
    def stm(self) -> Path:
        return self.root / "STM"

    @property
    def targets_dir(self) -> Path:
        return self.root / "targets"

    # --- LTM paths ---

    @property
    def my_memory(self) -> Path:
        return self.ltm / "myMemory"

    @property
    def bank(self) -> Path:
        return self.ltm / "bank"

    @property
    def bank_skills(self) -> Path:
        return self.bank / "skills"

    @property
    def bank_plugins(self) -> Path:
        return self.bank / "plugins"

    @property
    def bank_bundles(self) -> Path:
        return self.bank / "bundles"

    @property
    def mappings(self) -> Path:
        return self.ltm / "mappings"

    @property
    def mappings_targets(self) -> Path:
        return self.mappings / "targets"

    @property
    def mappings_translators(self) -> Path:
        return self.mappings / "translators"

    @property
    def sources(self) -> Path:
        return self.ltm / "sources"

    @property
    def sources_markets(self) -> Path:
        return self.sources / "markets"

    @property
    def sources_web(self) -> Path:
        return self.sources / "web"

    # --- STM paths ---

    @property
    def sessions(self) -> Path:
        return self.stm / "sessions"

    @property
    def runs(self) -> Path:
        return self.stm / "runs"

    @property
    def logs(self) -> Path:
        return self.stm / "logs"

    @property
    def scratch(self) -> Path:
        return self.stm / "scratch"

    # --- Config files ---

    @property
    def registry_file(self) -> Path:
        return self.root / "registry.yaml"

    @property
    def config_file(self) -> Path:
        return self.root / "config.yaml"

    @property
    def state_file(self) -> Path:
        return self.root / "state.yaml"

    # --- Targets ---

    @property
    def targets_machine(self) -> Path:
        return self.targets_dir / "machine"

    @property
    def targets_agents(self) -> Path:
        return self.targets_dir / "agents"

    # --- Operations ---

    def all_directories(self) -> list[Path]:
        """All directories that should exist in the workspace."""
        return [
            self.root,
            self.ltm,
            self.my_memory,
            self.bank,
            self.bank_skills,
            self.bank_plugins,
            self.bank_bundles,
            self.mappings,
            self.mappings_targets,
            self.mappings_translators,
            self.sources,
            self.sources_markets,
            self.sources_web,
            self.stm,
            self.sessions,
            self.runs,
            self.logs,
            self.scratch,
            self.targets_dir,
            self.targets_machine,
            self.targets_agents,
        ]

    def ensure_directories(self) -> list[Path]:
        """Create all workspace directories. Returns list of newly created dirs."""
        created = []
        for d in self.all_directories():
            if not d.exists():
                d.mkdir(parents=True, exist_ok=True)
                created.append(d)
        return created

    def ensure_my_memory(self) -> list[Path]:
        """Create myMemory template files if they don't exist (never overwrites)."""
        created = []
        for filename, content in MY_MEMORY_TEMPLATES.items():
            filepath = self.my_memory / filename
            if not filepath.exists():
                filepath.write_text(content)
                created.append(filepath)
        return created

    def ensure_config_files(self) -> list[Path]:
        """Create config files with defaults if they don't exist."""
        import yaml

        created = []

        if not self.config_file.exists():
            default_config = {
                "version": "0.1.0",
                "default_target": "claude-code-user",
                "auth": {"mode": "auto"},
            }
            self.config_file.write_text(yaml.dump(default_config, default_flow_style=False))
            created.append(self.config_file)

        if not self.registry_file.exists():
            default_registry = {"version": "0.1.0", "skills": {}, "updated_at": ""}
            self.registry_file.write_text(yaml.dump(default_registry, default_flow_style=False))
            created.append(self.registry_file)

        if not self.state_file.exists():
            default_state = {"version": "0.1.0", "embedded": {}, "deployments": []}
            self.state_file.write_text(yaml.dump(default_state, default_flow_style=False))
            created.append(self.state_file)

        return created

    def initialize(self) -> dict[str, list[Path]]:
        """Full workspace initialization. Returns summary of what was created."""
        dirs = self.ensure_directories()
        memory_files = self.ensure_my_memory()
        config_files = self.ensure_config_files()
        return {
            "directories": dirs,
            "memory_files": memory_files,
            "config_files": config_files,
        }

    @property
    def is_initialized(self) -> bool:
        return self.root.exists() and self.config_file.exists()
