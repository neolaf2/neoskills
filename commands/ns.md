---
name: ns
description: Invoke neoskills commands from within Claude Code
user_invocable: true
---

# /ns - neoskills Command

Wraps the neoskills CLI for in-session use. Some commands route to agents for richer workflows.

## Usage

`/ns <subcommand> [args]`

## Agent-Routed Commands

These trigger specialized agents via the Task tool for autonomous multi-step workflows:

- `/ns scan <target>` - Use the **skill-scanner** agent to discover skills across targets
- `/ns import from-target <target> --all` - Use the **skill-importer** agent for bulk import with analysis
- `/ns deploy skill <id> --to <target>` - Use the **skill-deployer** agent for deployment with validation
- `/ns dedup [--repos <slug>]` - Use the **skill-dedup** agent to find and resolve duplicate skills

## CLI-Routed Commands

These run directly via Bash:

- `/ns validate [--skill <id>] [--fix]` - Validate skills for completeness
- `/ns install <skill-id> [--target <t>]` - Install skill (bank + embed)
- `/ns embed --target <target>` - Embed bank via symlinks
- `/ns unembed --target <target>` - Remove embedded symlinks
- `/ns enhance <op> --skill <id>` - Enhance a skill using Claude
- `/ns sync status` - Check git status
- `/ns target list` - List targets
- `/ns config show` - Show configuration
- `/ns agent list` - List available agents
- `/ns agent run <name> --task '...'` - Run an agent via CLI

## Instructions

**For agent-routed commands** (`scan`, `import`, `deploy`, `dedup`):
Use the Task tool to launch the corresponding agent. Pass the user's arguments as the task prompt.

**For CLI-routed commands** (everything else):
Run the corresponding neoskills CLI command using Bash:

```bash
uv run neoskills <subcommand> [args]
```

If the user provides no subcommand, show the help:
```bash
uv run neoskills --help
```
