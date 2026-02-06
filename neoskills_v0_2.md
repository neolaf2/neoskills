# **neoskills**

**Cross-Agent Skill Bank, Transfer System, and Embedded Skill Substrate**

**Version:** v0.2 (PyPI Distribution, Validation, Install, Agents)

**Author:** Richard Tong

**License:** MIT

**PyPI:** https://pypi.org/project/neoskills/

**Repository:** https://github.com/neolaf2/neoskills

---

## **1. Mission**

**neoskills** is a **Python package + CLI** (PyPI-installable) that:

1. Manages **skills as the common denominator** across:
   - Multiple agent ecosystems (Claude Code, OpenCode, OpenClaw)
   - Multiple instances and versions of those agents
   - Multiple machines

2. Maintains a **canonical, portable master skill bank** (LTM) that you can:
   - View in one place
   - Sync to GitHub
   - Deploy selectively to different agents/instances/workflows
   - **Validate** for structural completeness and consistency

3. Supports **bidirectional transfer**:
   - Agent → bank (import / capture) with **full-directory preservation** (scripts/, references/, assets/)
   - Bank → agent (deploy / install / embed)
   - **Pre-import duplicate detection** with intrinsic-only checksums

4. Supports **web acquisition** of skills (GitHub repos, zip URLs, file URLs).

5. Reuses **existing meta-skills** (skill-manager skills) instead of re-implementing them.

6. Runs in **three modes**:
   - External orchestrator (CLI)
   - Agent-invoked tool
   - **Embedded plugin mode** (inside Claude Code / OpenCode, zero-copy, symlink-based)

7. Provides **autonomous agents** for skill management tasks (scanning, importing, deploying, deduplication).

8. Supports **dual authentication**:
   - `.env` with API key
   - Reuse of existing Claude subscription/client token (Claude Code / Desktop)

neoskills is **not** a new agent framework, a new skill schema, or a replacement for Claude/OpenCode/OpenClaw. It is a **skill bank + mapping + deployment substrate**.

---

## **2. Core Design Principles**

1. **Skills are the interoperability unit** — everything else (plugins, MCPs, commands, hooks, teams, subagents) exists around skills.

2. **Convention adoption, not reinvention** — Claude Code / OpenCode / OpenClaw conventions are treated as authoritative. neoskills does not invent replacement schemas.

3. **Canonical bank + adapters** — one canonical master inventory; per-agent/per-instance adapters translate and deploy.

4. **LTM / STM memory separation** — long-term portable knowledge vs short-term runtime artifacts.

5. **Full-directory preservation** — skills are not just SKILL.md; they include scripts/, references/, assets/. All import paths preserve the complete skill package.

6. **Intrinsic-only checksums** — duplicate detection and comparison ignore neoskills-generated metadata (metadata.yaml, provenance.yaml, .gitkeep) so structural differences don't trigger false positives.

7. **External + embedded modes** — neoskills can run outside agents or become the embedded skill system inside them.

---

## **3. License**

- **License:** MIT
- **Copyright:** Copyright (c) 2026 Richard Tong
- Repository includes: `LICENSE` (MIT text), `pyproject.toml` with `license = "MIT"`

---

## **4. Authentication Model**

neoskills supports two authentication modes, resolved automatically:

### **Mode A — API key (.env)**

Load `.env` from:
1. Current directory
2. `.neoskills/`
3. `~/.neoskills/.env`

Supported variables:
```
ANTHROPIC_API_KEY=...
CLAUDE_MODEL=sonnet
```

Used in CI, servers, headless environments.

### **Mode B — Subscription reuse (default)**

When no API key is present:
- Reuse existing Claude subscription/client token
- Works inside Claude Code, Claude Desktop
- No API key required

### **Resolution order**

1. `.env` API key
2. Subscription reuse via Claude Agent SDK
3. Disable LLM-assisted features (non-LLM features still work: scan, import, deploy, embed, validate, install)

---

## **5. Three Operating Modes**

### **Mode 1 — External Orchestrator (default)**

- neoskills CLI runs independently
- Scans/imports/deploys across agents and machines
- Validates skill bank, runs agents

### **Mode 2 — Agent-invoked Tool**

- Claude Code / OpenCode calls neoskills as a tool
- Used for generate / enhance / deploy workflows

### **Mode 3 — Embedded Plugin Mode**

- neoskills installs itself as a **plugin inside Claude Code / OpenCode**
- Host agent delegates all skill/command/tool management to neoskills
- Implemented via **symlink-based projection** (zero-copy, reversible, native-looking)
- Plugin structure: `agents/`, `commands/`, `skills/` directories

---

## **6. Canonical Workspace & Memory Model**

All neoskills state lives under `~/.neoskills/` (configurable via `--root`).

### **6.1 Directory Structure**

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
│   │
│   ├── bank/
│   │   ├── skills/             # Canonical skill bank
│   │   │   └── <skill_id>/
│   │   │       ├── canonical/  # Master copy (full directory)
│   │   │       │   ├── SKILL.md
│   │   │       │   ├── scripts/
│   │   │       │   ├── references/
│   │   │       │   └── assets/
│   │   │       ├── variants/   # Agent-specific variants
│   │   │       │   ├── claude-code/
│   │   │       │   ├── opencode/
│   │   │       │   └── openclaw/
│   │   │       ├── metadata.yaml
│   │   │       └── provenance.yaml
│   │   ├── plugins/
│   │   └── bundles/
│   │
│   ├── mappings/
│   │   ├── targets/            # Deployment target definitions
│   │   └── translators/
│   │
│   └── sources/
│       ├── markets/
│       └── web/
│
├── STM/                        # Short-term runtime artifacts
│   ├── sessions/
│   ├── runs/
│   ├── logs/
│   └── scratch/                # Embed backups
│
├── targets/
├── registry.yaml               # Master skill catalog
├── config.yaml                 # Configuration
└── state.yaml                  # Embed state
```

---

## **7. myMemory (User-Editable Long-Term Memory)**

Location: `~/.neoskills/LTM/myMemory/`

Files (never auto-overwritten by `neoskills init`):

- **AGENTS.md** — operating instructions + accumulated memory
- **SOUL.md** — persona, boundaries, tone
- **TOOLS.md** — user tool notes and conventions
- **BOOTSTRAP.md** — one-time first-run ritual
- **IDENTITY.md** — agent name, vibe, emoji
- **USER.md** — user profile and preferences

---

## **8. What neoskills Manages (First-Class Constructs)**

- Skills (primary)
- Plugins (bundles of skills + MCPs)
- MCPs / tools
- Commands
- Hooks
- Teams
- Subagents

**Plugin rule:** A plugin is a bundle that must include skills and MCPs, and may also include commands, hooks, teams, and subagents.

---

## **9. Canonical Skill Bank Model**

Each skill in the bank stores the **complete skill directory** (not just SKILL.md):

```
bank/skills/<skill_id>/
  canonical/              # Full directory copy
    SKILL.md              # Skill definition with YAML frontmatter
    scripts/              # Executable code (preserved from source)
    references/           # Documentation files
    assets/               # Templates, images, fonts
  variants/
    claude-code/          # Agent-specific variants
    opencode/
    openclaw/
  metadata.yaml           # Parsed frontmatter + checksum
  provenance.yaml         # Import source tracking
```

### **9.1 Skill Store Operations**

- `add(skill_id, content)` — store single SKILL.md content
- `add_from_dir(skill_id, source_dir)` — copy entire skill directory (scripts, references, assets)
- `exists(skill_id)` — check if skill is in bank
- `dir_checksum(skill_id)` — intrinsic-only checksum of canonical directory
- `get(skill_id)` — retrieve skill content and metadata
- `list_skills()` — list all skill IDs
- `list_variants(skill_id)` — list agent-specific variants
- `remove(skill_id)` — remove skill from bank

### **9.2 Checksum Algorithm**

Checksums use SHA256 over sorted file paths + contents, excluding:
- `metadata.yaml`, `provenance.yaml` (neoskills-generated)
- `.gitkeep`, `.DS_Store` (filesystem artifacts)
- `__pycache__/`, `.pyc`, `.pyo` (Python build artifacts)
- `.git/` directories

This ensures structural differences between bank and target don't produce false duplicate positives.

---

## **10. Targets & Instances**

A **target** represents a concrete deployment destination (machine + agent + instance).

### **10.1 Built-in Targets**

| Target ID | Agent Type | Discovery Path | Install Path |
|-----------|-----------|---------------|-------------|
| `claude-code-user` | claude-code | `~/.claude/skills` | `~/.claude/skills` |
| `claude-code-plugins` | claude-code | `~/.claude/plugins/*/skills` | — |
| `opencode-local` | opencode | `~/.config/opencode/skills` | `~/.config/opencode/skills` |
| `openclaw-custom` | openclaw | (user-defined) | (user-defined) |

### **10.2 Target Definition**

Each target defines:
- Agent type (claude-code, opencode, openclaw)
- Discovery paths (where to scan for existing skills)
- Install paths (where to deploy skills)
- Writable/read-only rules

Target definitions live in `LTM/mappings/targets/`.

---

## **11. Adapters (Per Agent / Instance)**

Adapters implement the interface between neoskills and each agent ecosystem:

```python
class BaseAdapter:
    def discover(target) -> list[DiscoveredSkill]
    def export(target, selection) -> list[Skill]
    def install(target, selection, mapping)
    def translate(skill, target) -> str
```

Implemented adapters:
- `adapters/claude/` — Claude Code
- `adapters/opencode/` — OpenCode
- `adapters/openclaw/` — OpenClaw

Adapters map native layouts; they do not invent schemas.

---

## **12. Import System**

### **12.1 Import Sources**

Three import subcommands:

| Command | Source |
|---------|--------|
| `neoskills import from-target <id>` | Scan an agent target and import selected skills |
| `neoskills import from-git <url>` | Clone a git repo and import SKILL.md directories |
| `neoskills import from-web <url>` | Fetch a raw file URL or zip archive |

### **12.2 Import Behavior**

All import paths:
1. **Preserve full directories** — scripts/, references/, assets/ are copied alongside SKILL.md via `store.add_from_dir()`
2. **Pre-import duplicate check** — compares intrinsic-only directory checksums between source and bank
3. **Skip identical** — if checksums match, skill is skipped with `=` indicator
4. **Warn on difference** — if checksums differ, warns user to use `--force`
5. **Track provenance** — records source type, location, timestamp, and original checksum
6. **Auto-embed** — after import, automatically symlinks new skills to default target (unless `--no-embed`)

### **12.3 Import Flags**

| Flag | Behavior |
|------|----------|
| `--skill <id>` | Import specific skill(s) only |
| `--all` | Import all discovered skills (from-target) |
| `--force` | Overwrite existing bank skills |
| `--no-embed` | Import to bank only, skip auto-embed |
| `--branch` | Git branch to clone (from-git) |

---

## **13. Validation System (v0.2)**

`neoskills validate` checks every skill in the bank for structural completeness.

### **13.1 Validation Checks**

| Check | Severity | Description |
|-------|----------|-------------|
| SKILL.md exists | error | Canonical directory must contain SKILL.md |
| Name present | error | YAML frontmatter must include `name` field |
| Description present | error | YAML frontmatter must include `description` field |
| Referenced paths exist | error | Paths mentioned in SKILL.md body must exist on disk |
| Orphan files | warning | Files in scripts/references/assets/ not referenced in SKILL.md |

### **13.2 Reference Detection**

Regex pattern `[\w./_-]*\w` captures file references in SKILL.md, filtering to paths within known subdirectories (scripts/, references/, assets/). Trailing punctuation is excluded.

### **13.3 Auto-fix**

`neoskills validate --fix` creates stub files for missing referenced paths.

---

## **14. Install Workflow (v0.2)**

`neoskills install <skill_id>...` provides a one-step bank verify + embed workflow:

1. Verify skill exists in bank
2. Resolve target (from `--target` flag or config `default_target`)
3. Determine bank path (variant preferred, canonical fallback)
4. Create symlink from bank to target install path
5. Report state with three indicators:
   - `+` — new symlink created
   - `=` — already linked (identical), skipped
   - `~` — updating existing symlink or replacing directory

### **14.1 Install Flags**

| Flag | Behavior |
|------|----------|
| `--target <id>` | Override default target |
| `--no-embed` | Verify in bank only, skip symlink |
| `--root <path>` | Workspace root override |

---

## **15. Autonomous Agents (v0.2)**

neoskills ships with 4 autonomous agents discovered from the `agents/` directory:

| Agent | Color | Purpose |
|-------|-------|---------|
| `skill-scanner` | cyan | Scan targets and discover skills |
| `skill-importer` | green | Import skills from various sources |
| `skill-deployer` | blue | Deploy skills to targets |
| `skill-dedup` | yellow | Identify and resolve duplicate skills |

### **15.1 Agent Commands**

- `neoskills agent list` — list available agents with descriptions
- `neoskills agent run <name> --task '...'` — run an agent autonomously

### **15.2 Agent File Format**

Agents are Markdown files with YAML frontmatter:

```yaml
---
name: agent-identifier
description: |
  Use this agent when [conditions]. Examples:
  <example>...</example>
model: inherit
color: yellow
tools: ["Read", "Bash", "Grep", "Glob"]
---

System prompt body...
```

### **15.3 Bundled Skills**

neoskills ships with bundled skills in the `skills/` directory:

- `skill-dedup/` — SKILL.md + `scripts/dedup_scan.py` for duplicate detection
- `bank-status/` — SKILL.md for bank health reporting

---

## **16. Embedded Plugin Mode**

### **16.1 Concept**

neoskills can install itself as a plugin inside Claude Code / OpenCode, becoming the authoritative skill system.

### **16.2 Mechanism**

Symbolic links project bank skills into agent directories:

```
~/.claude/skills/<skill_id>  →  ~/.neoskills/LTM/bank/skills/<skill_id>/variants/claude-code/
.opencode/skills/<skill_id>  →  ~/.neoskills/LTM/bank/skills/<skill_id>/variants/opencode/
```

- No copying — zero-copy symlink projection
- Fully reversible via `neoskills unembed`
- Backups stored in `STM/scratch/` before replacement

### **16.3 Plugin Structure**

```
neoskills/
├── agents/           # 4 autonomous agents
│   ├── skill-scanner.md
│   ├── skill-importer.md
│   ├── skill-deployer.md
│   └── skill-dedup.md
├── commands/         # Plugin commands
│   └── ns.md         # /ns command router
└── skills/           # Bundled skills
    ├── skill-dedup/
    └── bank-status/
```

### **16.4 Command Routing (/ns)**

The `/ns` command routes to either CLI commands or agents:

| Route | Type | Handler |
|-------|------|---------|
| `/ns scan` | agent | skill-scanner |
| `/ns import` | agent | skill-importer |
| `/ns deploy` | agent | skill-deployer |
| `/ns dedup` | agent | skill-dedup |
| `/ns init` | CLI | `neoskills init` |
| `/ns validate` | CLI | `neoskills validate` |
| `/ns install` | CLI | `neoskills install` |
| `/ns status` | CLI | `neoskills config show` |
| `/ns sync` | CLI | `neoskills sync` |

---

## **17. Bundles (Skill Sets)**

Bundles are named collections of skills/plugins used for machines, workflows, teams, or sub-agents.

Stored in: `LTM/bank/bundles/`

Commands:
- `neoskills deploy create-bundle <name> --skills <id1> <id2> ...`
- `neoskills deploy bundle <name> --to <target>`

---

## **18. Meta-Skill Integration**

neoskills imports and invokes existing meta-skills for:
- Normalizing skills across formats
- Generating agent-specific variants
- Auditing skill quality
- Adding tests/docs

Command: `neoskills enhance <operation> [--skill <id>] [--apply]`

---

## **19. CLI Commands (v0.2)**

### **19.1 Complete Command Reference**

| Command | Description |
|---------|-------------|
| `neoskills init` | Create `~/.neoskills/` workspace |
| `neoskills init --from-repo <url>` | Clone existing skill bank from GitHub |
| `neoskills target list` | List configured targets |
| `neoskills target add <id>` | Add a deployment target |
| `neoskills scan <target>` | Discover skills in a target |
| `neoskills import from-target <id>` | Import from an agent target |
| `neoskills import from-git <url>` | Import from a git repository |
| `neoskills import from-web <url>` | Import from a URL (raw file or zip) |
| `neoskills deploy skill <id> --to <target>` | Deploy a skill to a target |
| `neoskills deploy bundle <name> --to <target>` | Deploy a bundle |
| `neoskills deploy create-bundle <name>` | Create a new bundle |
| `neoskills install <skill_id>...` | One-step bank verify + embed |
| `neoskills validate` | Validate all skills in bank |
| `neoskills validate --skill <id>` | Validate a single skill |
| `neoskills validate --fix` | Auto-create stubs for missing files |
| `neoskills embed --target <id>` | Symlink bank into agent directory |
| `neoskills unembed --target <id>` | Remove symlinks and restore originals |
| `neoskills sync status\|commit\|push\|pull` | Git operations on bank |
| `neoskills enhance <op> --skill <id>` | Claude-powered skill enhancement |
| `neoskills agent list` | List available agents |
| `neoskills agent run <name> --task '...'` | Run an autonomous agent |
| `neoskills config set\|get\|show` | Configuration management |

### **19.2 New in v0.2**

- `neoskills init --from-repo <url> [--branch] [--force]` — clone existing workspace
- `neoskills validate [--skill] [--fix] [--root]` — structural validation
- `neoskills install <ids>... [--target] [--no-embed] [--root]` — one-step install
- `neoskills agent list|run` — autonomous agent management
- `--force` flag on all import subcommands — overwrite existing bank skills
- `--no-embed` flag on all import subcommands — skip auto-embed after import

---

## **20. Implementation Architecture**

### **20.1 Source Layout**

```
src/neoskills/
  __init__.py               # Version: 0.2.0
  core/
    auth.py                 # Dual authentication (API key + subscription)
    checksum.py             # SHA256 intrinsic-only checksums
    config.py               # YAML config management
    frontmatter.py          # YAML frontmatter parser
    models.py               # Skill, Target, Bundle, Provenance models
    workspace.py            # Workspace initialization and paths
  bank/
    store.py                # SkillStore: add, add_from_dir, get, list, remove
    registry.py             # Registry: master skill catalog
    provenance.py           # ProvenanceTracker: import source tracking
    validator.py            # Validation checks (5 rules, auto-fix)
  bundles/
    manager.py              # Bundle creation and deployment
  mappings/
    target.py               # TargetManager: built-in + custom targets
    resolver.py             # SymlinkResolver: create/remove/state
  adapters/
    base.py                 # BaseAdapter interface
    factory.py              # Adapter factory (get_adapter)
    claude/adapter.py       # Claude Code adapter
    opencode/adapter.py     # OpenCode adapter
    openclaw/adapter.py     # OpenClaw adapter
  translators/              # Skill format translators
  meta/
    enhancer.py             # Claude-powered skill enhancement
  runtime/
    claude/plugin.py        # Claude Code plugin integration
  cli/
    main.py                 # Click CLI entry point (14 commands)
    init_cmd.py             # init + --from-repo
    import_cmd.py           # import from-target|from-git|from-web
    install_cmd.py          # install (one-step bank + embed)
    validate_cmd.py         # validate (5 checks + auto-fix)
    agent_cmd.py            # agent list|run
    scan_cmd.py             # scan
    deploy_cmd.py           # deploy skill|bundle|create-bundle
    embed_cmd.py            # embed + unembed
    sync_cmd.py             # sync status|commit|push|pull
    enhance_cmd.py          # enhance
    target_cmd.py           # target add|list
    config_cmd.py           # config set|get|show
```

### **20.2 Dependencies**

```toml
[project]
requires-python = ">=3.13"
dependencies = [
    "pyyaml>=6.0",
    "jinja2>=3.1",
    "rich>=13.0",
    "click>=8.1",
    "gitpython>=3.1",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
sdk = ["claude-agent-sdk>=0.1.0", "anthropic>=0.40.0"]
dev = ["pytest>=8.0", "ruff>=0.4"]
```

### **20.3 Build System**

- Build backend: `hatchling`
- Package manager: `uv`
- Entry point: `neoskills = "neoskills.cli.main:cli"`

---

## **21. CI/CD Pipeline**

### **21.1 CI Workflow** (`.github/workflows/ci.yml`)

Triggers on push to `main` and pull requests:

```
lint (ruff check + format) → test (pytest) → build (wheel + install + smoke test)
```

Build job uploads wheel as artifact (7-day retention).

### **21.2 Release Workflow** (`.github/workflows/release.yml`)

Triggers on `v*` tags:

```
test (lint + test + build verify) → publish (PyPI + GitHub Release)
```

- PyPI publishing via **Trusted Publisher** (OIDC, no API token)
- GitHub Release with wheel + sdist + publish attestations
- Auto-generated release notes

### **21.3 Release Process**

```bash
# 1. Bump version in pyproject.toml and src/neoskills/__init__.py
# 2. Commit and push
# 3. Tag and push — CI handles the rest
git tag -a v0.X.Y -m "neoskills v0.X.Y - description"
git push origin v0.X.Y
```

---

## **22. GitHub Template Repos**

Two template repositories for bootstrapping:

| Template | Purpose | Contents |
|----------|---------|----------|
| `neolaf2/neoskills-my-skills-template` | Skill bank starter | 3 example skills, CI workflow |
| `neolaf2/neoskills-plugin-template` | Plugin starter | plugin.json, example agent/command/skill |

Usage:
```bash
neoskills init --from-repo https://github.com/neolaf2/neoskills-my-skills-template
```

---

## **23. Test Suite**

- **50 tests** covering core, bank, workspace, validation, models
- Test layout: `tests/unit/test_core.py`, `tests/unit/test_validator.py`
- Framework: pytest
- Run: `uv run pytest -v`

---

## **24. Acceptance Criteria (v0.2)**

neoskills v0.2 is complete when it can:

1. ~~Create the full `.neoskills` structure with myMemory.~~ **Done**
2. ~~Discover skills from two different agent ecosystems.~~ **Done** (Claude Code, OpenCode)
3. ~~Import skills into the canonical bank with provenance.~~ **Done** (3 import sources)
4. ~~Deploy a bundle to a different agent/instance.~~ **Done**
5. ~~Sync bank with a GitHub repo.~~ **Done**
6. ~~Run inside Claude Code without API key.~~ **Done**
7. ~~Run outside Claude Code with `.env` API key.~~ **Done**
8. ~~Embed into Claude Code and expose skills natively via symlinks.~~ **Done**
9. ~~Invoke at least one existing meta-skill and apply its output.~~ **Done**
10. ~~**Validate skills for structural completeness.**~~ **Done** (5 checks, auto-fix)
11. ~~**One-step install workflow** (bank verify + embed)~~ **Done**
12. ~~**Autonomous agents** for skill management~~ **Done** (4 agents)
13. ~~**Full-directory import** preserving scripts/references/assets~~ **Done**
14. ~~**Pre-import duplicate detection** with intrinsic-only checksums~~ **Done**
15. ~~**Publish to PyPI** with CI/CD automation~~ **Done** (v0.2.0 on PyPI)
16. ~~**GitHub template repos** for bootstrapping~~ **Done** (2 templates)

All 16 acceptance criteria met. **v0.2.0 published to PyPI on 2026-02-06.**

---

## **25. What Changed from v0.1 → v0.2**

| Area | v0.1 | v0.2 |
|------|------|------|
| Distribution | Local build only | **PyPI-published** (`pip install neoskills`) |
| Import | SKILL.md content only | **Full-directory** (scripts/, references/, assets/) |
| Dedup | None | **Intrinsic-only checksums**, pre-import check, `--force` |
| Validation | None | **5 structural checks** + auto-fix + per-skill mode |
| Install | Manual embed | **One-step** bank verify + embed with 3-state reporting |
| Agents | None | **4 autonomous agents** (scanner, importer, deployer, dedup) |
| Plugin | Agents only | Agents + **commands** (/ns) + **bundled skills** |
| CI/CD | None | **GitHub Actions** (lint → test → build → release → PyPI) |
| Templates | None | **2 GitHub template repos** |
| Init | Basic | `--from-repo`, `--branch`, `--force` flags |
| Branch | master | **main** |

---

## **26. Future (v0.3 Candidates)**

- Skill search / discovery across public repositories
- Skill versioning and changelog tracking
- Team-based skill sharing and access control
- OpenClaw adapter completion
- Docker starter-kit (Dockerfile + compose)
- Marketplace integration
- Skill dependency graph
- Cross-machine sync via SSH/rsync
