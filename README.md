# neoskills

**Cross-Agent Skill Bank, Transfer System, and Embedded Skill Substrate**

neoskills manages **skills as the common denominator** across multiple agent ecosystems (Claude Code, OpenCode, OpenClaw). It maintains a canonical, portable master skill bank that you can view in one place, sync to GitHub, and deploy selectively to different agents, instances, and workflows.

## Features

- **Canonical Skill Bank** with LTM/STM memory model and variant support per agent
- **Multi-ecosystem discovery** - scan Claude Code, OpenCode, and OpenClaw for installed skills
- **Bidirectional transfer** - import skills into the bank, deploy them to any target
- **Symlink-based embedding** - zero-copy, reversible projection into agent skill directories
- **Web acquisition** - import from git repos, zip URLs, or raw file URLs
- **Git sync** - version control your skill bank and push/pull to GitHub
- **Claude-powered enhancement** - normalize, audit, generate variants, add docs/tests
- **Bundle management** - group skills into deployable sets for workflows, teams, or machines
- **Plugin mode** - runs inside Claude Code as an embedded plugin with agents and commands

## Installation

```bash
pip install neoskills
```

Or with [uv](https://github.com/astral-sh/uv):

```bash
uv add neoskills
```

## Quick Start

```bash
# Install from PyPI
pip install neoskills
# or with uv
uv add neoskills

# Initialize workspace
neoskills init

# Discover skills across your agent ecosystems
neoskills scan claude-code-user
neoskills scan opencode-local

# Import skills into the bank
neoskills import from-target claude-code-user --skill skill-discovery
neoskills import from-git https://github.com/your-org/skills-repo

# Deploy to a different agent
neoskills deploy skill skill-discovery --to opencode-local

# Embed bank into an agent via symlinks
neoskills embed --target claude-code-user
neoskills unembed --target claude-code-user

# Sync with GitHub
neoskills sync commit -m "Add new skills"
neoskills sync push

# Enhance with Claude
neoskills enhance audit --skill skill-discovery
neoskills enhance normalize --skill skill-discovery --apply
```

## Architecture

```
~/.neoskills/
├── LTM/                        # Long-term portable knowledge
│   ├── myMemory/               # User-editable agent memory
│   │   ├── AGENTS.md           # Operating instructions
│   │   ├── SOUL.md             # Persona, boundaries, tone
│   │   ├── TOOLS.md            # Tool notes and conventions
│   │   ├── BOOTSTRAP.md        # First-run ritual
│   │   ├── IDENTITY.md         # Agent name, vibe, emoji
│   │   └── USER.md             # User profile and preferences
│   ├── bank/
│   │   ├── skills/             # Canonical skill bank
│   │   │   └── <skill_id>/
│   │   │       ├── canonical/  # Master copy
│   │   │       ├── variants/   # Agent-specific variants
│   │   │       ├── metadata.yaml
│   │   │       └── provenance.yaml
│   │   ├── plugins/
│   │   └── bundles/
│   ├── mappings/
│   │   ├── targets/            # Deployment target definitions
│   │   └── translators/
│   └── sources/
├── STM/                        # Short-term runtime artifacts
│   ├── sessions/
│   ├── runs/
│   ├── logs/
│   └── scratch/                # Embed backups
├── targets/
├── registry.yaml               # Master skill catalog
├── config.yaml                 # Configuration
└── state.yaml                  # Embed state
```

## Targets

neoskills ships with four built-in targets:

| Target | Agent | Discovery Path |
|--------|-------|---------------|
| `claude-code-user` | Claude Code | `~/.claude/skills` |
| `claude-code-plugins` | Claude Code | `~/.claude/plugins/*/skills` |
| `opencode-local` | OpenCode | `~/.config/opencode/skills` |
| `openclaw-custom` | OpenClaw | (user-defined) |

Add custom targets:
```bash
neoskills target add my-server \
  --agent-type claude-code \
  --discovery ~/.claude/skills \
  --install ~/.claude/skills
```

## CLI Reference

| Command | Description |
|---------|-------------|
| `neoskills init` | Create `~/.neoskills/` workspace |
| `neoskills target list\|add` | Manage deployment targets |
| `neoskills scan <target>` | Discover skills in a target |
| `neoskills import from-target\|from-git\|from-web` | Import skills to bank |
| `neoskills deploy skill\|bundle --to <target>` | Deploy to a target |
| `neoskills deploy create-bundle` | Create a skill bundle |
| `neoskills embed\|unembed` | Symlink projection into agents |
| `neoskills sync status\|commit\|push\|pull` | Git operations on bank |
| `neoskills enhance <op> --skill <id>` | Claude-powered enhancement |
| `neoskills validate [--skill <id>]` | Validate skills (structure, references) |
| `neoskills install <skill_id>...` | One-step bank verify + embed |
| `neoskills agent list\|run` | List or run autonomous agents |
| `neoskills config set\|get\|show` | Configuration management |

## Three Operating Modes

1. **External Orchestrator** (default) - CLI runs independently, scans/imports/deploys across agents
2. **Agent-invoked Tool** - Claude Code or OpenCode calls neoskills as a tool
3. **Embedded Plugin Mode** - neoskills installs itself as a Claude Code plugin, exposing agents, skills, and the `/ns` command

## Authentication

neoskills resolves authentication automatically:

1. **.env API key** - loads from `./`, `.neoskills/`, or `~/.neoskills/.env`
2. **SDK subscription reuse** - works inside Claude Code/Desktop with no API key
3. **Disabled** - non-LLM features still work (scan, import, deploy, embed)

## Development

```bash
# Clone and install
git clone https://github.com/neolaf2/neoskills
cd neoskills
uv sync --dev

# Run tests
uv run pytest -v

# Lint
uv run ruff check src/

# Run locally
uv run neoskills --help
```

## Docker

```bash
docker build -t neoskills .
docker run -e ANTHROPIC_API_KEY=... neoskills scan claude-code-user
```

## License

MIT - see [LICENSE](LICENSE)

## Author

Richard Tong
