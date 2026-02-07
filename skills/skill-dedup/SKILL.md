---
name: skill-dedup
description: Identify and resolve duplicate skills across the neoskills bank and agent targets (Claude Code, OpenCode, plugins). Use when the user mentions duplicate skills, wants to deduplicate their skill bank, asks about redundant or overlapping skills, wants to clean up skills, or needs to audit skill inventory for duplicates. Also use when importing skills that may already exist in the bank.
---

# Skill Dedup

Scan for duplicate and near-duplicate skills across the neoskills bank, agent targets, and plugins, then resolve them with merge/remove/keep strategies.

## Quick Start

```bash
python scripts/dedup_scan.py
```

For machine-readable output:

```bash
python scripts/dedup_scan.py --json
```

Auto-resolve exact duplicates (replace target copies with symlinks to bank):

```bash
python scripts/dedup_scan.py --resolve exact --dry-run   # preview
python scripts/dedup_scan.py --resolve exact              # execute
```

## Three Duplicate Categories

The scan classifies duplicates into three categories:

**1. Exact Duplicates** — identical content (same SHA256) across locations. Safe to consolidate. The bank copy is canonical; target copies can be replaced with symlinks.

**2. Diverged Copies** — same skill ID exists in multiple locations but content differs. The script identifies the "richer" copy (more files) and recommends importing it to the bank.

**3. Name-Similar Groups** — different skill IDs with similar names and descriptions. These need manual review to determine if they're truly related or just coincidentally named.

## Resolution

### Auto-Resolve

```bash
# Replace exact-duplicate target copies with symlinks to bank
python scripts/dedup_scan.py --resolve exact

# Import richer diverged copies to bank, then symlink targets
python scripts/dedup_scan.py --resolve diverged

# Both at once
python scripts/dedup_scan.py --resolve all

# Preview without making changes
python scripts/dedup_scan.py --resolve all --dry-run
```

Backups are saved as `.<skill-name>.dedup-backup` in the parent directory.

### Manual Resolution

For name-similar groups or cases needing judgment:

```bash
# Remove target copy, replace with symlink
rm -rf ~/.claude/skills/<skill-name>
neoskills embed --target claude-code-user

# Import a better target version into the bank
neoskills import from-target claude-code-user --skill <skill-name>
```

## Script Options

```
python scripts/dedup_scan.py [OPTIONS]

--bank PATH          Path to neoskills workspace (default: ~/.neoskills)
--targets LIST       Targets to scan (default: claude opencode)
--repos LIST         GitHub repos to scan (e.g. neolaf2/mySkills)
--threshold FLOAT    Combined similarity threshold 0.0-1.0 (default: 0.80)
--json               Output as JSON for programmatic use
--no-plugins         Skip scanning ~/.claude/plugins/
--resolve MODE       Auto-resolve: exact, diverged, or all
--dry-run            Preview resolution without making changes
```

## Scan Locations

- **Bank**: `~/.neoskills/LTM/bank/skills/` (canonical copies)
- **Claude Code**: `~/.claude/skills/` (user-installed)
- **OpenCode**: `~/.config/opencode/skills/` (user-installed)
- **Plugins**: `~/.claude/plugins/*/skills/` and cache (disable with `--no-plugins`)
- **GitHub repos**: cloned on demand with `--repos`
