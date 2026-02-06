---
name: bank-status
description: Use when user asks about skill bank status, inventory, or what skills are available in neoskills
---

# Bank Status

Display the current status of the neoskills skill bank.

## Instructions

1. Read `~/.neoskills/registry.yaml` to get the skill catalog
2. Count total skills, their tags, and when they were last updated
3. Check `~/.neoskills/state.yaml` for any currently embedded skills
4. Read target definitions from `~/.neoskills/LTM/mappings/targets/` to show configured targets

## Output Format

Present a summary:
- **Bank**: Total skills, last updated timestamp
- **Targets**: List configured targets with skill counts
- **Embedded**: Any currently embedded skills (symlinked)
- **Recent**: Last 5 imported skills with provenance

## Quick Commands

If the user wants to take action, suggest:
- `neoskills scan <target>` to discover new skills
- `neoskills import from-target <target> --all` to import everything
- `neoskills embed --target <target>` to embed bank into agent
