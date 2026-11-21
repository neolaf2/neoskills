# neoskills

[![PyPI version](https://img.shields.io/pypi/v/neoskills.svg)](https://pypi.org/project/neoskills/)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**面向 AI 编程智能体的「Homebrew 式」技能管理器。**

neoskills 管理跨智能体生态（Claude Code、OpenCode、OpenClaw）的可移植技能定义。你可以在一个地方浏览技能、同步到 GitHub、通过符号链接有选择地部署，并通过内置的本体图（ontology graph）发现技能之间的关系。

---

## 目录

- [安装](#安装)
- [快速开始](#快速开始)
- [工作原理](#工作原理)
- [本体层](#本体层)
- [智能体目标](#智能体目标)
- [运行模式](#运行模式)
- [CLI 参考](#cli-参考)

---

## 安装

### 从 PyPI 安装（推荐）

```bash
pip install neoskills
```

或使用 [uv](https://github.com/astral-sh/uv)：

```bash
uv tool install neoskills
```

### 从源码安装

```bash
git clone https://github.com/neolaf2/neoskills
cd neoskills
uv sync --dev
uv run neoskills --help
```

### 环境要求

- **Python 3.13+**（必需）
- **Git**（用于 tap 操作）
- **uv**（推荐用于开发）

---

## 快速开始

```bash
# 1. 初始化工作区
neoskills init

# 2. 添加一个 tap（一个托管在 git 上的技能仓库）
neoskills tap https://github.com/your-org/my-skills

# 3. 浏览和搜索
neoskills list                          # 列出 tap 中的所有技能
neoskills list --linked                 # 已部署到智能体的技能
neoskills search "document processing"  # 跨 tap 搜索

# 4. 部署一个技能到你的智能体
neoskills install kstar-loop            # 复制到 tap + 符号链接到智能体

# 5. 创建你自己的技能
neoskills create my-new-skill -d "What it does" --type task

# 6. 检查系统健康状态
neoskills doctor
```

### 刚刚发生了什么？

`neoskills init` 创建了 `~/.neoskills/` 并带有一个默认 tap。`install` 在某个 tap 中找到了技能，并在你的智能体技能目录（如 `~/.claude/skills/`）中创建了一个符号链接。你的智能体现在就能使用这个技能了。`create` 生成一个包含 `SKILL.md` + `ontology.yaml` 的新技能脚手架。

---

## 工作原理

### 架构

```
~/.neoskills/                         # 工作区根目录
├── config.yaml                       # 目标、tap、默认值
├── taps/                             # 用 git 克隆的技能仓库
│   ├── mySkills/                     # 默认 tap
│   │   └── skills/
│   │       └── <skill-id>/
│   │           ├── SKILL.md          # 技能定义（frontmatter + 正文）
│   │           ├── ontology.yaml     # 图元数据（可选，推荐）
│   │           ├── scripts/          # 可执行代码（可选）
│   │           ├── references/       # 支持文档（可选）
│   │           └── assets/           # 媒体/模板（可选）
│   └── <other-taps>/                 # 额外的技能来源
└── cache/                            # 备份和临时存储
```

### 部署模型

技能通过 **逐技能符号链接**（零拷贝、即时可逆）部署到智能体：

```
~/.claude/skills/kstar-loop  -->  ~/.neoskills/taps/mySkills/skills/kstar-loop
```

这意味着：

- **单一事实来源** 在你的 tap 中（用 git 做版本控制）
- **多个智能体** 可以同时链接同一个技能
- **零拷贝** —— 对 tap 的修改会立即反映出来
- **可逆** —— `neoskills unlink` 只移除符号链接，不涉及其他任何东西

### 技能结构

每个技能都是一个目录，至少包含一个 `SKILL.md`：

```yaml
# SKILL.md frontmatter
---
name: my-skill
description: "What this skill does"
author: "Your Name"
tags: [productivity, automation]
targets: [claude-code]
---

# My Skill

智能体将读取的指令、提示词和文档。
```

可选地，一个 `ontology.yaml` 附属文件添加图元数据（类型、领域、生命周期、边、版本控制）。参见 [本体层](#本体层)。

---

## 本体层

本体在你的技能之上添加了一个 **属性图** —— 以 `ontology.yaml` 附属文件形式存储的节点和带类型边。没有外部数据库，图在运行时从文件系统物化而来。

### 渐进式丰富

技能不需要第一天就有完整的元数据：

| 级别 | 包含什么 | 如何达到 |
|-------|---------------|-----------------|
| **L0 -- 裸** | 仅 SKILL.md | 所有现有技能的默认状态 |
| **L1 -- 打标签** | + 带类型/领域/标签的 ontology.yaml | `neoskills ontology enrich <id>` |
| **L2 -- 已连接** | + 边（requires, extends, composes, conflicts） | 作者声明关系 |
| **L3 -- 受治理** | + 生命周期状态、版本、能力清单 | 随时间维护 |

### 发现

```bash
# 分面搜索
neoskills ontology discover --domain agent-architecture --state operational
neoskills ontology discover --type meta --text "compiler"

# 加载并检查完整图
neoskills ontology load     # 打印摘要：技能、边、领域
neoskills ontology stats    # JSON 统计
```

### 依赖

```bash
neoskills ontology deps kstar-loop --transitive    # 它依赖什么
neoskills ontology rdeps kstar-planner --tree       # 什么依赖它
neoskills ontology add-edge skill-a skill-b -t requires
```

边类型：`requires`、`extends`、`composes_with`、`conflicts_with`、`supersedes`、`derived_from`。

### 生命周期

技能会经历一个状态机：

```
candidate --> validated --> operational --> refined --> deprecated --> archived
```

```bash
neoskills ontology lifecycle                                          # 按状态列出所有技能
neoskills ontology transition my-skill validated --reason "tested"    # 改变状态
```

### 组合

```bash
# 把技能组合成流水线
neoskills ontology compose source-text-to-markdown research-md-to-latex \
  --mode pipeline --name md-to-paper

# 规划拆分
neoskills ontology split monolithic-skill sub-a sub-b sub-c
```

### 版本控制

```bash
neoskills ontology version kstar-loop --bump minor   # 0.1.0 -> 0.2.0
```

### 可视化与导出

```bash
neoskills ontology graph kstar-loop --depth 2 --format mermaid
neoskills ontology export --format json --output graph.json
neoskills ontology export --format dot                              # Graphviz
```

### 校验

```bash
neoskills ontology validate   # 检查断边、环、冲突
```

### 自动丰富

```bash
neoskills ontology enrich my-skill              # 单个技能，L0 -> L1
neoskills ontology enrich --all --level L1 --dry-run   # 预览批量
neoskills ontology enrich --all --level L1             # 执行批量
```

### 领域分类

技能被归类到一个两级层级：agent-architecture、education、document-processing、business、knowledge-work、meta 等。领域在可能时会从技能名自动推断。

完整设计文档见 [docs/ontology-design.md](docs/ontology-design.md)。

---

## 智能体目标

内置目标：

| 目标 | 智能体 | 技能路径 |
|--------|-------|-----------|
| `claude-code` | Claude Code | `~/.claude/skills` |
| `opencode` | OpenCode | `~/.config/opencode/skills` |

添加自定义目标：

```bash
neoskills config set targets.my-agent.skill_path /path/to/skills
```

---

## 运行模式

1. **CLI**（默认）—— `neoskills` 作为独立命令行工具运行
2. **智能体调用工具** —— Claude Code 或 OpenCode 以编程方式调用 neoskills
3. **嵌入式 MCP 插件** —— neoskills 作为 MCP 服务器运行在 Claude Code 内部，暴露 12+ 个工具，包括本体操作

### 认证（用于 Claude 相关功能）

neoskills 自动解析认证：

1. **.env API key** —— 从 `./`、`.neoskills/` 或 `~/.neoskills/.env` 加载
2. **SDK 订阅复用** —— 在 Claude Code/Desktop 内部无需 key 即可工作
3. **禁用** —— 非 LLM 功能无需任何 key（tap、link、list、ontology 等）

---

## CLI 参考

### 工作区

| 命令 | 描述 |
|---------|-------------|
| `neoskills init` | 创建 `~/.neoskills/` 工作区 |
| `neoskills config set\|get\|show` | 管理配置 |
| `neoskills doctor` | 健康检查（符号链接、配置、tap） |
| `neoskills migrate` | 从 v0.2 结构迁移到 v0.3+ |

### Taps

| 命令 | 描述 |
|---------|-------------|
| `neoskills tap <url>` | 添加一个 tap（git clone） |
| `neoskills untap <name>` | 移除一个 tap |
| `neoskills update [name]` | 从 tap 拉取最新 |
| `neoskills upgrade` | 更新所有 tap + 刷新链接 |
| `neoskills push` | 提交并推送 tap 到 GitHub |

### 技能

| 命令 | 描述 |
|---------|-------------|
| `neoskills list [--linked\|--available]` | 列出技能 |
| `neoskills search <query>` | 跨 tap 搜索 |
| `neoskills info <skill_id>` | 技能详细信息 |
| `neoskills create <skill_id>` | 生成新技能（SKILL.md + ontology.yaml） |
| `neoskills install <skill_id>` | 一步部署（复制 + 链接） |
| `neoskills uninstall <skill_id>` | 移除（解除链接 + 可选删除） |
| `neoskills link <skill_id>` | 创建符号链接（tap -> 目标） |
| `neoskills unlink <skill_id>` | 移除符号链接 |

---

> 本中文文档由社区贡献者翻译，以英文 [README.md](README.md) 为准；如有出入，请以原文为准。
