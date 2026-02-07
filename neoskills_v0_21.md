**Neoskills Requirement for V0.21**

Got it. What you’re really asking for is **clean separation \+ deterministic wiring** between:

1. **neoskills as a first-class agent**, and

2. **neoskills embedded inside other agents (Claude Code, OpenCode, etc.) as a plugin subsystem**,

    while preserving *all* the previously built skill-management capabilities.

Below is a **coherent integration \+ packaging design** that resolves all of that cleanly.

---

## **1\. Re-integrating the existing skill-management skills**

All the earlier work (find, discover, evolve, migrate, audit, etc.) should **not live as ad-hoc scripts**. They should be formalized as a **Skill Management Capability Layer**.

### **Canonical skill groups**

skill\_management/  
├── discover/  
│   ├── find\_skills  
│   ├── index\_skills  
│   ├── validate\_skills  
│  
├── lifecycle/  
│   ├── install\_skill  
│   ├── uninstall\_skill  
│   ├── upgrade\_skill  
│   ├── migrate\_skill  
│  
├── evolution/  
│   ├── skill\_creator  
│   ├── skill\_refactor  
│   ├── skill\_specialize  
│  
├── registry/  
│   ├── local\_registry  
│   ├── remote\_registry  
│   ├── sync\_registry  
│  
├── governance/  
│   ├── version\_check  
│   ├── compatibility\_check  
│   ├── policy\_enforce

These are **agent-agnostic skills**. The *same code* must work in:

* standalone neoskills agent

* embedded plugin mode

The difference is **where they are mounted and how they’re invoked**.

---

## **2\. Master repo \+ target skill database validation at init time**

This is a **hard requirement** and should be enforced at init, not runtime.

### **neoskills init**

###  **should do the following**

#### **2.1 Resolve configuration hierarchy**

Priority:  
1\. Project-local config (.neoskills/config.yaml)  
2\. User config (\~/.neoskills/config.yaml)  
3\. Default embedded config (package defaults)

#### **2.2 Mandatory checks at init**

required:  
  skill\_registry:  
    type: local | remote | hybrid  
    path: /absolute/or/relative/path  
    writable: true

  Master\_repo: for skill  
    url: https://github.com/neolaf2/mySkills  
    branch: main  
    pinned\_commit: optional

Init must fail **loudly** if:

* registry is missing

* registry is read-only when mutation is required

* master repo cannot be resolved

* schema version mismatch

This gives you **deterministic reproducibility**.

---

## **3\. Dual execution mode: Agent vs Plugin**

This is the core architectural pivot.

### **Mode A — neoskills as a top-level agent (it has its own core skills and utility skills for its own purpose)**

neoskills/  
├── agent.yaml  
├── skills/  
│   ├── skill\_management/  
│   ├── default/  
│   ├── operation/  
│   └── meta/

Invocation:

neoskills run find\_skills

* Skills are **first-class**

* Skill creator is **global**

* Full mutation rights

---

### **Mode B — neoskills embedded as a plugin**

Here, **neoskills expose its own skills into the host agent’s global namespace as a plugin**.

plugins/  
└── neoskills/  
    ├── plugin.yaml  
    ├── skills/  
    │   └── skill\_management/  
    │       ├── discover/  
    │       ├── lifecycle/  
    │       └── evolution/  
    └── registry/

Invocation becomes:

plugin/neoskills/skill\_management.find\_skills

or internally:

call:  
  plugin: neoskills  
  skill: skill\_management.find\_skills

### **Why this matters**

* No collision with Cloud Code’s own skill\_creator and utility skills using sub-namespace

* No accidental override of host capabilities

* Explicit context boundary

---

## **4\. Namespacing rules (non-negotiable)**

This is where most systems fail. Yours won’t.

### **Absolute rule**

**Anything that mutates or manages skills MUST live under a plugin namespace when embedded.**

#### **Correct**

plugin/neoskills/skill\_creator  
plugin/neoskills/skill\_management.find\_skills

#### **No Conflict with Host Agents’ top level skills**

skill\_creator  
find\_skills

This avoids:

* semantic collision

* cognitive confusion

* accidental invocation by host agent heuristics

---

## **5\. Plugin-scoped Skill Creator**

You explicitly called this out, and you’re right.

### **Two distinct skill creators**

| Context | Skill creator |
| ----- | ----- |
| Host agent | skill\_creator |
| neoskills plugin | plugin/neoskills/skill\_creator |

### **Behavioral difference**

**Plugin skill creator or skill deployment tool**

* Should be called after the Host’s default skill-creator skill has generated the skill, so that it will maintain the synchronization and collision management and other controls for the user’s “Global” skill subsystems and be much more configurable for the user.

* Uses plugin registry

* Obeys host agent capability constraints

* Cannot escalate privileges

This is a **sandboxed meta-agent**, also behaves cleanly.

---

## **6\. Packaging implications (PyPI / Docker / plugin)**

### **Python package layout**

neoskills/  
├── core/  
├── agent/  
├── plugin/  
│   └── neoskills/  
│       ├── plugin.yaml  
│       └── skills/  
├── cli/  
└── templates/

At install time:

* agent mode exposes neoskills

* plugin mode exposes neoskills.plugin

### **Docker**

You get **two images from the same codebase**:

neoskills:agent  
neoskills:plugin

Same bits, different entrypoints and mounts.

---

## **7\. Context hygiene (the subtle but critical part)**

When running as a plugin:

* Skill discovery is **scoped**

* Memory writes are **namespaced**

* Registry sync is **explicitly authorized**

* Still needs tool access

This guarantees:

* host agent safety

* reproducibility

* explainability

---

## **8\. Mental model (this is the unifying idea)**

Think of neoskills as:

**A portable cognitive organ**  
that can operate as:

* a full organism, or

* a transplanted subsystem

Same DNA. Different nervous system attachment.

---

If you want, next step I’d recommend:

* formalize plugin.yaml schema

* define the exact invocation contract (call, return, capabilities)

* lock the init-time validation state machine

That’s where this turns from “clean design” into something bulletproof.

