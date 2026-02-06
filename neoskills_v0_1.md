Below is a **single, unified, authoritative Requirements & Implementation Plan** for **neoskills**, consolidating **all prior clarifications** into one coherent document.

This is the version you can hand to **Claude Code / Codex-CLI** as *the* build spec.

No placeholders. No omissions. No contradictions.

---

# **neoskills**

**Cross-Agent Skill Bank, Transfer System, and Embedded Skill Substrate**

**Version:** v0.1 (Foundational, Claude-first)

**Author:** Richard Tong

**License:** MIT

---

## **1\. Mission**

Build **neoskills** as a **Python package \+ CLI** (PyPI) and **Docker starter-kit** that:

1. Manages **skills as the common denominator** across:

   * multiple agent ecosystems (Claude Code, Claude Cowork, Claude Desktop VM, OpenCode, OpenClaw, Codex-style setups)

   * multiple **instances and versions** of those agents

   * multiple machines

2. Maintains a **canonical, portable master skill bank** (LTM) that you can:

   * view in one place

   * sync to GitHub

   * deploy selectively to different agents/instances/workflows

3. Supports **bidirectional transfer**:

   * agent → bank (import / capture)

   * bank → agent (deploy / map)

4. Supports **web acquisition** of skills (GitHub repos, zip URLs, file URLs, marketplaces).

5. Reuses **existing meta-skills you already built** (skill-manager skills) instead of re-implementing them.

6. Can run in **three modes**:

   * external orchestrator (CLI)

   * agent-invoked tool

   * **embedded plugin mode** (inside Claude Code / OpenCode, zero-copy, symlink-based)

7. Uses **Claude Agent SDK for Python** as the v0.1 execution substrate, installed via:

uv pip install claude-agent-sdk

7. 

8. Supports **dual authentication**:

   * .env with API key

   * reuse of existing Claude subscription/client token (Claude Code / Desktop / Cowork)

neoskills is **not**:

* a new agent framework

* a new skill schema

* a replacement for Claude/OpenCode/OpenClaw

* a NotebookLM manager (explicitly excluded)

It is a **skill bank \+ mapping \+ deployment substrate**.

---

## **2\. Core Design Principles (Locked)**

1. **Skills are the interoperability unit**

    Everything else (plugins, MCPs, commands, hooks, teams, subagents) exists *around* skills.

2. **Convention adoption, not reinvention**

    ClaudeCode / OpenCode / OpenClaw conventions are treated as authoritative.

    neoskills does not invent replacement schemas.

3. **Canonical bank \+ adapters**

   * One canonical master inventory

   * Per-agent/per-instance adapters translate and deploy

4. **LTM / STM memory separation**

    Long-term portable knowledge vs short-term runtime artifacts.

5. **Claude-first, OpenCode next**

    Claude Agent SDK is a dependency for v0.1; OpenCode support validates neutrality.

6. **External \+ embedded modes**

    neoskills can run outside agents *or* become the embedded skill system inside them.

---

## **3\. License**

* **License:** MIT

* **Copyright:**

Copyright (c) Richard Tong

Repository must include:

* LICENSE (MIT text)

* pyproject.toml license \= "MIT"

---

## **4\. Authentication Model (Mandatory)**

neoskills must support **two authentication modes**, resolved automatically:

### **Mode A — API key (.env)**

* Load .env from:

  1. current directory

  2. .neoskills/

  3. \~/.neoskills/.env

* Supported variables:

CLAUDE\_API\_KEY=...  
CLAUDE\_MODEL=sonnet

* 

* Used in CI, servers, headless environments.

### **Mode B — Subscription reuse (default)**

* When no API key is present:

  * reuse existing Claude subscription/client token

  * works inside Claude Code, Claude Cowork, Claude Desktop VM

* No API key required.

### **Resolution order**

1. .env API key

2. subscription reuse via Claude Agent SDK

3. disable LLM-assisted features (non-LLM features still work)

---

## **5\. Three Operating Modes**

### **Mode 1 — External Orchestrator (default)**

* neoskills CLI runs independently

* scans/imports/deploys across agents and machines

### **Mode 2 — Agent-invoked Tool**

* Claude Code / OpenCode calls neoskills as a tool

* used for generate / enhance / deploy workflows

### **Mode 3 —** 

### **Embedded Plugin Mode**

###  **(critical)**

* neoskills installs itself as a **plugin inside Claude Code / OpenCode**

* host agent delegates **all skill/command/tool management** to neoskills

* implemented via **symlink-based projection**

* zero-copy, reversible, native-looking

---

## **6\. Canonical Workspace & Memory Model**

All neoskills state lives under:

.neoskills/

### **6.1 Final Directory Structure**

.neoskills/  
├── LTM/  
│   ├── myMemory/  
│   │   ├── AGENTS.md  
│   │   ├── SOUL.md  
│   │   ├── TOOLS.md  
│   │   ├── BOOTSTRAP.md  
│   │   ├── IDENTITY.md  
│   │   └── USER.md  
│   │  
│   ├── bank/  
│   │   ├── skills/  
│   │   ├── plugins/  
│   │   └── bundles/  
│   │  
│   ├── mappings/  
│   │   ├── targets/  
│   │   └── translators/  
│   │  
│   └── sources/  
│       ├── markets/  
│       └── web/  
│  
├── STM/  
│   ├── sessions/  
│   ├── runs/  
│   ├── logs/  
│   └── scratch/  
│  
├── targets/  
│   ├── machine/  
│   └── agents/  
│  
├── registry.yaml  
├── config.yaml  
└── state.yaml  
---

## **7\. myMemory (User-Editable Long-Term Memory)**

Location:

.neoskills/LTM/myMemory/

Files (never auto-overwritten):

* AGENTS.md — operating instructions \+ accumulated memory

* SOUL.md — persona, boundaries, tone

* TOOLS.md — user tool notes and conventions

* BOOTSTRAP.md — one-time first-run ritual (deleted after completion, never recreated)

* IDENTITY.md — agent name, vibe, emoji

* USER.md — user profile and preferences

---

## **8\. What neoskills Manages (First-Class Constructs)**

* Skills (primary)

* Plugins (bundles)

* MCPs / tools (Claude Agent SDK convention)

* Commands

* Hooks

* Teams

* Subagents

### **Plugin rule (important)**

A **plugin** is a bundle that **must include skills and MCPs**, and may also include commands, hooks, teams, and subagents.

---

## **9\. Canonical Skill Bank Model**

Each skill in the bank supports **multiple variants**:

bank/skills/\<skill\_id\>/  
  canonical/  
  variants/  
    claude-code/  
    opencode/  
    openclaw/  
  metadata.yaml  
  provenance.yaml

* Files are stored verbatim.

* Variants are mapped to agent conventions by adapters.

---

## **10\. Targets & Instances**

A **target** represents a concrete deployment destination:

* machine \+ agent \+ instance

Examples:

* claude-code-project

* claude-code-user

* claude-desktop-vm

* opencode-local

* openclaw-custom

* openclaw-builtins (read-only discovery)

Target definitions live in:

LTM/mappings/targets/

Each target defines:

* discovery paths

* install paths

* writable/read-only rules

* transport (local FS, ssh, rsync, zip)

---

## **11\. Adapters (Per Agent / Instance)**

Adapters must implement:

1. discover(target)

2. export(target, selection)

3. install(target, selection, mapping)

4. translate(skill, target)

Adapters must **not invent schemas**; they map native layouts.

---

## **12\. Web & Marketplace Acquisition**

Supported source types:

* Git repositories

* Zip URLs

* Single file URLs

* Existing skill marketplaces

Imported content is stored in:

LTM/sources/

and then normalized into the bank.

---

## **13\. Bundles (Skill Sets)**

Bundles are named collections of skills/plugins used for:

* machines

* workflows

* teams

* sub-agents

Stored in:

LTM/bank/bundles/

Deployable via:

neoskills deploy bundle \<bundle\_id\> \--to \<target\>  
---

## **14\. Embedded Plugin Mode (Key Capability)**

### **14.1 Concept**

neoskills can install itself as a **plugin inside Claude Code / OpenCode**, becoming the **authoritative skill system**.

### **14.2 Mechanism**

* Use **symbolic links** to project:

\~/.claude/skills  →  \~/.neoskills/LTM/bank/skills/.../variants/claude-code  
.opencode/skills  →  \~/.neoskills/LTM/bank/skills/.../variants/opencode

* 

* No copying.

* Fully reversible.

### **14.3 Behavior**

* Host agent believes skills are native.

* neoskills controls updates and mappings.

* Commands, MCPs, hooks, teams are exposed dynamically.

---

## **15\. Meta-Skill Integration (Self-Improving)**

You already have **skill-manager capabilities implemented as skills**.

neoskills must:

* import these meta-skills into the bank

* invoke them via Claude Agent SDK

* apply outputs (with \--apply) to:

  * normalize skills

  * generate variants

  * migrate conventions

  * add tests/docs

Command:

neoskills enhance \<operation\> \[--skill \<id\>\] \[--apply\]  
---

## **16\. CLI Commands (v0.1)**

Core commands:

* neoskills init

* neoskills config set

* neoskills target add | list

* neoskills scan target \<id\>

* neoskills import from-target \<id\>

* neoskills import from-git \<url\>

* neoskills import from-web \<url\>

* neoskills deploy skill|bundle ...

* neoskills sync pull | status | commit | push

* neoskills enhance ...

* neoskills embed | unembed

---

## **17\. Implementation Architecture (Python)**

src/neoskills/  
  core/  
  bank/  
  bundles/  
  mappings/  
  adapters/  
    claude/  
    opencode/  
    openclaw/  
  translators/  
  meta/  
  runtime/claude/  
  cli/

Dependencies:

* claude-agent-sdk

* uv

* PyYAML

* jinja2

* rich

* git (or GitPython)

---

## **18\. Docker Starter-Kit**

* Base: python:3.12-slim

* Install: uv, claude-agent-sdk, neoskills

* No credentials baked in

* Supports .env or subscription reuse

---

## **19\. CI/CD**

* CI: uv sync, pytest

* Release: PyPI on v\*

* Docker: GHCR on v\*

---

## **20\. Acceptance Criteria (v0.1)**

neoskills is complete when it can:

1. Create the full .neoskills structure with myMemory.

2. Discover skills from two different agent ecosystems.

3. Import skills into the canonical bank with provenance.

4. Deploy a bundle to a different agent/instance.

5. Sync bank with a GitHub repo.

6. Run inside Claude Code **without API key**.

7. Run outside Claude Code **with .env API key**.

8. Embed into Claude Code and expose skills natively via symlinks.

9. Invoke at least one existing meta-skill and apply its output.

---

## **21\. Final Build Handoff (Single Instruction)**

Build neoskills as specified above.  
It is a cross-agent, cross-instance skill bank and deployment system with an optional embedded plugin mode.  
Skills are the common denominator.  
Use MIT license.  
Depend on Claude Agent SDK.  
Support .env API keys and subscription reuse.  
Do not invent new agent schemas.  
Deliver PyPI package, Docker image, and CI/CD workflows.  
---

Next step:

* generate **example target definitions** for Claude/OpenCode/OpenClaw,

* design the **exact symlink layouts** per agent,

* Create a “which \-a” type of skill search order to resolve potential skill conflict or overwrite/inheritance/specialized

