---
name: ns
description: Invoke neoskills commands from within Claude Code
user_invocable: true
---

# /ns - neoskills Command

Wraps the neoskills CLI for in-session use.

## Usage

`/ns <subcommand> [args]`

## Subcommands

- `/ns scan <target>` - Scan a target for skills
- `/ns import from-target <target> --skill <id>` - Import a skill
- `/ns import from-git <url>` - Import from git repo
- `/ns deploy skill <id> --to <target>` - Deploy a skill
- `/ns embed --target <target>` - Embed bank via symlinks
- `/ns unembed --target <target>` - Remove embedded symlinks
- `/ns enhance <op> --skill <id>` - Enhance a skill
- `/ns sync status` - Check git status
- `/ns target list` - List targets
- `/ns config show` - Show configuration

## Instructions

When the user invokes `/ns`, run the corresponding neoskills CLI command using Bash:

```bash
uv run neoskills <subcommand> [args]
```

The working directory should be the neoskills project root or any directory where the `neoskills` command is available in PATH.

If the user provides no subcommand, show the help:
```bash
uv run neoskills --help
```
