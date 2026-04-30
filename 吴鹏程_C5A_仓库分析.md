# neoskills 仓库分析文档

**分析人：** 吴鹏程  
**仓库：** https://github.com/wuhaha55/neoskills  
**分析日期：** 2026-04-30  
**仓库版本：** v0.4.1  

---

## 1. 这个仓库是做什么的？

**一句话概括：**  
neoskills 是一个 Homebrew 风格的 AI 编程代理技能管理器，用于跨多个 AI 代理生态系统（Claude Code、OpenCode、OpenClaw）统一管理、部署和发现技能（Skills）。

---

## 2. 仓库目录结构

```
neoskills/
├── src/neoskills/          # 核心源代码（Python 包）
│   ├── cli/                 # Click CLI 命令集
│   │   ├── main.py          # 入口点，命令注册（懒加载）
│   │   ├── create_cmd.py    # 技能脚手架
│   │   ├── ontology_cmd.py  # 17 个本体子命令
│   │   └── ...             # tap、link、list、doctor 等
│   ├── core/                # 核心模块
│   │   ├── cellar.py        # ~/.neoskills/ 工作区管理
│   │   ├── tap.py          # Tap 管理（Git 克隆的技能仓库）
│   │   ├── linker.py        # 符号链接管理（零拷贝部署）
│   │   ├── frontmatter.py   # YAML frontmatter 解析
│   │   ├── checksum.py      # SHA256 校验和（去重检测）
│   │   └── models.py       # SkillSpec 数据模型
│   ├── ontology/            # 本体层（v0.4 核心特性）
│   │   ├── models.py        # 枚举 + 数据类（SkillNode, OntologyEdge）
│   │   ├── graph.py         # SkillGraph 内存属性图
│   │   ├── loader.py        # 文件系统 → 图（遍历 taps + plugins）
│   │   ├── writer.py        # 图 → 文件系统（ontology.yaml）
│   │   ├── engine.py        # 高级 API（OntologyEngine）
│   │   ├── taxonomy.py      # 领域分类法 + 推理
│   │   ├── lifecycle.py     # 状态机转换
│   │   ├── versioning.py    # 语义化版本操作
│   │   ├── composition.py   # 技能组合/分解
│   │   ├── export.py        # Mermaid、DOT、JSON、ASCII 导出
│   │   └── scaffold.py      # 基于模板的技能创建
│   └── runtime/             # 代理运行时集成
│       └── claude/
│           └── plugin.py     # MCP 插件（12+ 工具）
├── tests/                   # 测试套件（172 个测试）
│   ├── unit/                # 单元测试
│   │   ├── test_ontology.py  # 47 个本体层测试
│   │   └── ...
│   └── integration/         # 端到端工作流测试
├── skills/                  # 内置技能（打包在 PyPI 包中）
│   ├── bank-status/          # 技能库状态报告
│   │   └── SKILL.md
│   └── skill-dedup/         # 重复技能检测与清理
│       ├── SKILL.md
│       └── scripts/dedup_scan.py
├── agents/                  # 自主代理定义（Markdown + YAML frontmatter）
│   ├── skill-scanner.md      # 扫描目标并发现技能
│   ├── skill-importer.md     # 从各种来源导入技能
│   ├── skill-deployer.md    # 部署技能到目标
│   └── skill-dedup.md       # 识别并解决重复技能
├── commands/                # 插件命令
│   └── ns.md               # /ns 命令路由器
├── docs/                    # 文档
│   └── ontology-design.md   # 本体设计文档
├── README.md                # 项目文档（完整用户手册）
├── CLAUDE.md                # Claude Code 项目指南
├── TASKS.md                 # 任务状态（已完成 + 未来计划）
├── main.py                  # 入口点（Hello World，占位符）
├── pyproject.toml           # Python 项目配置（构建系统：hatchling）
├── uv.lock                  # uv 依赖锁文件
├── Dockerfile               # Docker 起步套件
├── LICENSE                  # MIT 许可证
├── neoskills_v0_1.md       # v0.1 需求规格
├── neoskills_v0_2.md       # v0.2 需求规格
├── neoskills_v0_21.md      # v0.21 命名空间和插件架构设计
└── neoskills_v0_3.md       # v0.3 需求规格（Homebrew 风格重构）
```

---

## 3. 仓库中的技能（Skills）

### 3.1 内置技能（打包在 PyPI 包中）

| 技能 ID | 名称 | 功能描述 |
|---------|------|---------|
| `bank-status` | 技能库状态 | 显示 neoskills 技能库的当前状态：技能总数、标签分布、最后更新时间、已配置的目标、当前已嵌入的技能（符号链接）、最近导入的 5 个技能及其来源。 |
| `skill-dedup` | 技能去重 | 跨技能库和代理目标（Claude Code、OpenCode、插件）识别并解决重复和近似重复的技能。支持三种重复类别：精确重复（相同 SHA256）、发散副本（相同技能 ID 但内容不同）、名称相似组（不同技能 ID 但名称描述相似）。提供自动解析（替换为符号链接）和手动解析选项。 |

### 3.2 技能目录结构示例

```
skills/skill-dedup/
├── SKILL.md              # 技能定义（YAML frontmatter + Markdown 指令）
└── scripts/
    └── dedup_scan.py     # 可执行代码（重复扫描算法）
```

### 3.3 通过 Tap 管理的技能

neoskills 采用 Homebrew 风格的 Tap 模型，技能存储在 Git 克隆的仓库中（默认 Tap：`~/.neoskills/taps/mySkills/`）。用户可以通过 `neoskills tap <url>` 添加更多 Tap。

**典型 Tap 结构：**
```
~/.neoskills/taps/mySkills/
├── tap.yaml              # Tap 元数据（名称、描述、版本）
├── skills/
│   ├── agent-factory/    # 自定义技能（tags: [first-party]）
│   ├── remotion/         # 外部技能（tags: [external, video]）
│   └── ...              # 更多技能
└── plugins/              # 插件仓库（未来）
```

---

## 4. 仓库中的自主代理（Agents）

neoskills 附带 4 个自主代理，定义在 `agents/` 目录中。这些代理可以被 `neoskills agent run <name> --task '...'` 调用。

| 代理 ID | 名称 | 颜色 | 功能描述 |
|---------|------|------|---------|
| `skill-scanner` | 技能扫描器 | cyan | 扫描代理目标（如 `~/.claude/skills/`）并发现技能。生成技能清单，包括路径、元数据和平校验和。用于初始化或定期审计。 |
| `skill-importer` | 技能导入器 | green | 从各种来源导入技能到技能库：1) 从代理目标导入（`import from-target`）；2) 从 Git 仓库导入（`import from-git`）；3) 从 Web URL 导入（`import from-web`）。保留完整目录结构（scripts、references、assets）。 |
| `skill-deployer` | 技能部署器 | blue | 将技能从技能库部署到代理目标。创建符号链接（零拷贝、可反转）。支持单个技能、批量技能或整个 Bundle 的部署。 |
| `skill-dedup` | 技能去重器 | yellow | 自主识别跨技能库和目标的重复技能。扫描三种重复类别，生成重复组报告，并执行用户选择的解析策略（删除、符号链接、合并）。 |

### 代理文件格式示例

```yaml
---
name: skill-dedup
description: |
  Use this agent when identifying and resolving duplicate skills...
model: inherit
color: yellow
tools: ["Read", "Bash", "Grep", "Glob"]
---

You are the neoskills skill-dedup agent. Your job is to...
```

---

## 5. 哪个技能/代理最有意思？为什么？

### 我最感兴趣的：🏆 `skill-dedup`（技能去重器）

**理由：**

1. **解决实际痛点**  
   在管理大量 AI 代理技能时，重复技能是一个真实存在的问题。用户可能从多个来源导入技能（GitHub、Web、其他代理），导致相同技能有多个副本。`skill-dedup` 直接解决了这个问题。

2. **智能算法**  
   它不仅做简单的校验和比较，还识别三种重复类别：
   - **精确重复**（相同 SHA256）→ 安全合并
   - **发散副本**（相同 ID，不同内容）→ 推荐"更丰富"的副本
   - **名称相似组**（不同 ID，相似名称）→ 需要人工审查

   这种分层方法体现了对不同重复场景的细致理解。

3. **包含可执行代码**  
   与纯 Markdown 指令的技能不同，`skill-dedup` 包含一个实际的 Python 脚本（`scripts/dedup_scan.py`），实现了重复检测算法。这使得它既是一个"技能"（给代理的指令），也是一个"工具"（可执行的代码）。

4. **自主代理 + 技能的组合**  
   `skill-dedup` 既作为一个**技能**（`skills/skill-dedup/SKILL.md`）存在，也作为一个**自主代理**（`agents/skill-dedup.md`）存在。这种双重身份展示了 neoskills 架构的灵活性：同一个功能可以通过不同方式调用。

5. **体现核心价值**  
   neoskills 的核心使命是"技能管理"。`skill-dedup` 是这个使命的集中体现：它帮助用户理解他们的技能库、识别问题、并提供解决方案。这是 neoskills 价值的"旗舰示例"。

### 次感兴趣：`ontology` 层（v0.4 新特性）

虽然不是一个"技能"，但本体层是 neoskills v0.4 的核心特性，非常有趣：

- **属性图**：在技能之上构建属性图（节点 + 类型化边），在运行时从 `ontology.yaml` 文件实例化。
- **渐进式丰富**：技能不需要在第一天就有完整的元数据。它们可以从 L0（纯 SKILL.md）逐步演进到 L3（受治理的、版本化的、有生命周期的）。
- **图导出**：支持导出为 Mermaid、DOT（Graphviz）、JSON 和 ASCII 树，用于可视化技能关系。

这体现了对"技能生态系统"的深层思考：技能不是孤立的，它们有依赖、扩展、组合和冲突关系。本体层捕捉了这些关系。

---

## 6. 项目技术架构亮点

### 6.1 Homebrew 风格的设计

neoskills v0.3 引入了 Homebrew 风格的设计，这是一个巧妙的类比：

| Homebrew 概念 | neoskills 等价物 |
|--------------|------------------|
| Tap（Git 仓库） | mySkills GitHub 仓库 |
| Formula（包定义） | 带 YAML frontmatter 的 SKILL.md |
| Cellar（安装包） | `~/.neoskills/taps/mySkills/`（Tap 就是 Cellar） |
| 符号链接（`/usr/local/bin/`） | `~/.claude/skills/foo →` Tap 技能 |
| `brew tap` | `neoskills tap <url>` |
| `brew install` | `neoskills install <skill>` |
| `brew update` | `neoskills update`（Git pull taps） |
| `brew upgrade` | `neoskills upgrade`（更新 + 刷新链接） |
| `brew doctor` | `neoskills doctor`（健康检查） |

这种设计的好处：
- **零拷贝部署**：技能只存储在一个地方（Tap），通过符号链接"安装"到代理目录。
- **Git 原生**：Tap 是 Git 仓库，所以版本控制、协作和备份都是免费的。
- **简单心智模型**：用户可以直观地理解"Tap = 技能仓库"、"install = 符号链接"。

### 6.2 符号链接部署模型

```
~/.claude/skills/kstar-loop  -->  ~/.neoskills/taps/mySkills/skills/kstar-loop
```

**好处：**
- **单一真相源**：Tap 中的技能是规范版本。
- **多代理共享**：同一个技能可以同时链接到 Claude Code 和 OpenCode。
- **无拷贝**：Tap 的更改立即反映在所有链接的代理中。
- **可反转**：`neoskills unlink` 只删除符号链接，不影响其他东西。

### 6.3 本体层（v0.4）

v0.4 引入的本体层是一个高级特性，它在技能之上构建了一个**属性图**：

**节点类型：**
- `skill` - 技能
- `domain` - 领域（如 `agent-architecture`、`education`）
- `meta` - 元技能（管理其他技能的技能）

**边类型：**
- `requires` - 技能 A 需要技能 B
- `extends` - 技能 A 扩展技能 B
- `composes_with` - 技能 A 可以与技能 B 组合
- `conflicts_with` - 技能 A 与技能 B 冲突
- `supersedes` - 技能 A 取代技能 B
- `derived_from` - 技能 A 派生自技能 B

**渐进式丰富：**

| 级别 | 存在什么 | 如何达到 |
|------|---------|---------|
| **L0 -- 裸** | 只有 SKILL.md | 所有现有技能的默认状态 |
| **L1 -- 已标记** | + ontology.yaml（type、domain、tags） | `neoskills ontology enrich <id>` |
| **L2 -- 已连接** | + 边（requires、extends、composes、conflicts） | 作者声明关系 |
| **L3 -- 受治理** | + 生命周期状态、版本、能力清单 | 随时间维护 |

这种设计的巧妙之处：技能不需要在第一天就有完整的元数据。它们可以从简单的 SKILL.md 开始，然后逐步丰富。这降低了采用门槛。

---

## 7. 项目演进历史

### v0.1 → v0.2 → v0.3 → v0.4

| 版本 | 核心变化 |
|------|---------|
| **v0.1** | 初始版本。LTM/STM 内存模型、bank/registry/mappings 架构、三个操作模式（CLI、代理调用工具、嵌入式插件）。 |
| **v0.2** | PyPI 发布。完整目录导入（保留 scripts/references/assets）。内在校验和（去重检测）。结构验证（5 个检查 + 自动修复）。一步安装工作流。4 个自主代理。 |
| **v0.3** | **重大重构**。用 Homebrew 风格的 tap/cellar/link 模型替换深层 bank/registry/mappings 架构。所有元数据在 SKILL.md frontmatter 中。删除 3580 行代码，净减少 812 行。迁移命令从 v0.2 结构到 v0.3。 |
| **v0.4** | **本体层**。在技能之上构建属性图。17 个 CLI 本体子命令。渐进式丰富（L0-L3）。生命周期状态机。语义化版本。组合/分解。图导出（Mermaid、DOT、JSON、ASCII）。 |

**演进趋势：**
1. **简化**：v0.3 删除了复杂的 LTM/STM 层次结构，采用扁平的 tap 模型。
2. **生态系统中立性**：支持多个代理生态系统（Claude Code、OpenCode、OpenClaw）。
3. **渐进式采用**：技能不需要完整的元数据就能工作（L0），可以逐步丰富（L1-L3）。
4. **Git 原生**：Tap 是 Git 仓库，所以版本控制、协作和备份都是免费的。

---

## 8. 总结

neoskills 是一个设计精良的 AI 代理技能管理工具。它采用 Homebrew 风格的设计，使用符号链接实现零拷贝部署，并提供了本体层来捕捉技能之间的复杂关系。

**核心价值：**
1. **跨代理生态系统**：管理 Claude Code、OpenCode、OpenClaw 的技能。
2. **单一真相源**：技能存储在 Git 仓库（Tap）中，通过符号链接部署到代理。
3. **智能去重**：`skill-dedup` 识别并解决重复技能。
4. **本体层**：在技能之上构建属性图，支持依赖分析、组合和生命周期管理。

**最有趣的技能：** `skill-dedup` -- 因为它解决实际问题，包含智能算法，并体现了 neoskills 的核心使命。

---

**文档结束**
