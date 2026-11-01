# Troubleshooting

Common failures when installing, running and contributing to neoskills, with the command that
diagnoses each one. Every snippet below was reproduced on macOS + Python 3.13.12 + uv 0.12.5
against `main` at v0.4.2.

---

## 1. `python main.py` prints "Hello from neoskills!" and nothing else

`main.py` in the repository root is a leftover placeholder:

```python
def main():
    print("Hello from neoskills!")
```

The real entry point is the Click group declared in `pyproject.toml`:

```toml
[project.scripts]
neoskills = "neoskills.cli.main:cli"
```

**Use one of these instead:**

```bash
uv run neoskills --help          # from a clone (after `uv sync --dev`)
neoskills --help                 # if installed with `uv tool install neoskills`
```

---

## 2. `uv sync` fails: no compatible Python

The package requires Python 3.13+ (`requires-python = ">=3.13"`), so a system Python 3.11/3.12
can't resolve the lock file.

```bash
uv python install 3.13
uv sync --dev
uv run neoskills --version      # neoskills, version 0.4.2
```

Do not `pip install -e .` into a 3.12 interpreter — the project is `uv`-only by convention
(see `CLAUDE.md`).

---

## 3. `neoskills ontology validate` reports a broken `belongs_to` edge

Minimal reproduction using only documented commands:

```bash
neoskills init
neoskills create demo-skill -d "demo" --type task
neoskills ontology enrich demo-skill
neoskills ontology validate
```

```
Graph has errors:
  ERROR: Broken edge: demo-skill --belongs_to--> general
```

Exit code is `1`, even though nothing is actually wrong: `create` assigns
`domain: [general]`, which the loader turns into a `belongs_to` edge, but domains are stored as a
separate node collection (`taxonomy.py`) rather than as skill nodes. The validator only resolves
edge targets against skill nodes, so every domain edge looks dangling.

This is tracked as "Domain-aware validation" in `TASKS.md`.

**Workarounds until it is fixed:**

- Treat `belongs_to` errors as informational: they carry no information about skill health.
- Machine-readable filtering:

  ```bash
  neoskills ontology validate 2>&1 | grep -v -- '--belongs_to-->'
  ```

- Skip enrichment (`enrich` is what materialises the domain edge) and keep the skill at L0/L1
  without a `domain:` key — `ontology load` still works, it just won't be facetable by domain.

---

## 4. A skill is linked but the agent never sees it

Deployment is a symlink, so a moved or deleted tap directory silently kills the link. Check it:

```bash
neoskills doctor
neoskills list --linked
```

`doctor` prints a link summary such as:

```
Taps: 1 registered (mySkills)
Skills in mySkills: 1
Links: 0 total, 0 healthy
  Unlinked skills in mySkills: 1
System is healthy.
```

Repair by re-linking instead of copying files:

```bash
neoskills link <skill_id> --target claude-code
```

Never copy a skill into `~/.claude/skills/` by hand — two copies drift and `neoskills doctor`
can no longer tell you which one is canonical.

---

## 5. CI fails on lint but tests pass locally

CI runs `ruff check src/` **and** `ruff format --check src/` before the test job, with
`line-length = 100` and `target-version = "py313"`. Run both locally:

```bash
uv run ruff check src/
uv run ruff format --check src/
uv run ruff format src/        # apply
```

Ruff also enforces `E741`, so single-letter names such as `l` are rejected — use `lnk` for link
items, as the rest of `core/linker.py` does.

---

## 6. `git push` rejected after working on a tap

`neoskills update`/`upgrade` run `git pull` inside `~/.neoskills/taps/<tap>`. If you edited the tap
directly and the upstream moved, pull with rebase, then push through the CLI:

```bash
git -C ~/.neoskills/taps/mySkills pull --rebase
neoskills push        # commits the tap and pushes it to its remote
```

A tap is a normal git repository: the same recovery rules apply as for any repo.
