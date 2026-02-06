---
name: skill-dedup
description: Identify and resolve duplicate skills across the neoskills bank and agent targets (Claude Code, OpenCode). Use when the user mentions duplicate skills, wants to deduplicate their skill bank, asks about redundant or overlapping skills, wants to clean up skills, or needs to audit skill inventory for duplicates. Also use when importing skills that may already exist in the bank.
---

# Skill Dedup

Scan for duplicate and near-duplicate skills across the neoskills bank and agent targets, then resolve them with merge/remove/keep strategies.

## Quick Start

Run the bundled scan script to get an immediate overview:

```bash
python scripts/dedup_scan.py
```

For machine-readable output:

```bash
python scripts/dedup_scan.py --json
```

## Scan Workflow

### 1. Run the Scan

Execute `scripts/dedup_scan.py` to scan all skill locations:

- **Bank**: `~/.neoskills/LTM/bank/skills/` (canonical copies)
- **Claude Code**: `~/.claude/skills/` (user-installed skills)
- **OpenCode**: `~/.config/opencode/skills/` (user-installed skills)

The script compares skills by:
- **SHA256 checksum** — finds exact content duplicates
- **Name similarity** (SequenceMatcher, threshold 0.75) — finds near-duplicates like `whisper` vs `openai-whisper`

### 2. Interpret Results

The scan produces two groups:

**Exact Duplicates** — identical content across locations. These are safe to consolidate. The bank copy is canonical; remove target copies or replace with symlinks via `neoskills embed`.

**Name-Similar Groups** — skills with similar names but different content. These need manual review. Actions:
- `EXACT_DUPLICATE` — identical, keep one
- `SIMILAR` — minor differences, pick the better version
- `DIVERGED` — significantly different, review and merge

### 3. Resolve Duplicates

For each duplicate group, choose a resolution:

**Keep bank copy, remove target copies** (most common for exact dupes):
```bash
# Remove the target copy
rm -rf ~/.claude/skills/<skill-name>

# Or replace with a symlink to the bank
neoskills embed --target claude-code-user
```

**Merge diverged versions** — read both versions, combine the best parts into the bank canonical copy:
1. Read both: `cat ~/.neoskills/LTM/bank/skills/<id>/canonical/SKILL.md` and `cat ~/.claude/skills/<id>/SKILL.md`
2. Merge content into the bank copy
3. Remove or symlink the target copy

**Keep both** — if skills with similar names serve different purposes (e.g., `notebooklm-my-notebooks` vs `notebooklm-notebook-index`), leave them as-is.

## Script Options

```
python scripts/dedup_scan.py [OPTIONS]

--bank PATH       Path to neoskills workspace (default: ~/.neoskills)
--targets LIST    Targets to scan (default: claude opencode)
--repos LIST      GitHub repos to scan (e.g. neolaf2/mySkills)
--threshold FLOAT Name similarity threshold 0.0-1.0 (default: 0.75)
--json            Output as JSON for programmatic use
```

### Scanning GitHub Repos

Include GitHub repos with nested skill structures (e.g. `custom/<skill>/`, `downloaded/<skill>/`):

```bash
python scripts/dedup_scan.py --repos neolaf2/mySkills
```

The script shallow-clones the repo to a temp directory, recursively finds all `SKILL.md` files, and includes them in the comparison. Skills are labeled with the repo name as their source.

## Integration with neoskills CLI

After identifying duplicates, use neoskills commands to resolve:

```bash
# See what's in the bank
neoskills scan claude-code-user

# Embed bank skills as symlinks (replaces target copies)
neoskills embed --target claude-code-user

# Import a better version into the bank
neoskills import from-target claude-code-user --skill <skill-name>
```
