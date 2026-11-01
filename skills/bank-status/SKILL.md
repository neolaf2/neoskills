---
name: bank-status
description: Use when user asks about skill bank status, inventory, or what skills are available in neoskills
---

# Bank Status

Display the current status of the neoskills skill bank.

## Instructions

1. Read `~/.neoskills/config.yaml` to get the configured taps and targets
2. Walk each tap's `skills/` directory (e.g. `~/.neoskills/taps/mySkills/skills/`) to build the catalog
3. Count total skills and their tags; take "last updated" from the newest file mtime or `git -C <tap> log -1`
4. Derive embedded skills from the filesystem: look in each target's skill path for symlinks that resolve
   into `~/.neoskills/taps/`. There is no `state.yaml` to read — state is always re-derived (v0.3+)

## Output Format

Present a summary:
- **Bank**: Total skills, last updated timestamp
- **Targets**: List configured targets with skill counts
- **Embedded**: Any currently linked skills (symlinks)
- **Recent**: Last 5 imported skills with provenance

## Quick Commands

These commands exist in the current (v0.3+) CLI. The v0.2 commands `scan`, `import` and `embed`
were removed together with the `LTM/` and `bank/` directories:

- `neoskills list` — list every skill discovered in your taps
- `neoskills list --linked` — show only what is linked into an agent
- `neoskills tap <git-url>` — add a skill source repository
- `neoskills install <skill_id>` — copy to the default tap and link it to the target
- `neoskills doctor` — health check for config, taps and symlinks
