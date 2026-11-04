# neoskills 仓库分析（C5A Level 4 深度分析报告）

- 分析对象：https://github.com/neolaf2/neoskills （我的 Fork：https://github.com/ZayneWenner/neoskills）
- 分析人：贾静文
- 分析日期：2026-11-04
- 分析依据：仓库 README.md、CLAUDE.md、TASKS.md、pyproject.toml、`.claude-plugin/plugin.json`、`agents/*.md`、`commands/ns.md`、`skills/*/SKILL.md`、`src/neoskills/**` 目录与关键模块源码（共 141 个受版本控制的路径）

---

## 一、一句话概括

**neoskills 是一个"给 AI 编程智能体用的 Homebrew"——把散落在 Claude Code、OpenCode、OpenClaw 等不同智能体里的技能（Skill）统一收进一个本地技能仓库（bank），用 tap 拉取、用软链接部署、用本体图（ontology）描述技能之间的关系，从而做到"一处管理、多处复用"。**

它要解决的痛点很具体：现在每个 AI 编程工具都有自己的技能目录和技能格式，同一个技能会在 `~/.claude/skills/`、插件目录、别的工具目录里各存一份，改了一处另外两处不会同步，时间一长就说不清"我到底有哪些技能、哪份是最新的"。这不是"文件管理"问题，而是**包的版本与分发问题**，所以作者直接借用了 Homebrew 的心智模型：tap（仓库源）、cellar（本地仓库）、install/upgrade（安装升级）、symlink（部署）、doctor（体检）、dedup（去重）。

## 二、目录结构

| 路径 | 作用 | 关键内容 |
|------|------|----------|
| `README.md` | 门面文档 | 安装、快速开始、架构图、本体层、Agent 目标、运行模式、CLI 参考 |
| `CLAUDE.md` | 给 AI 读的项目说明书 | 约束 AI 在本仓库里怎么写代码、怎么改结构 |
| `TASKS.md` | 任务/路线图 | 分阶段实现的待办 |
| `pyproject.toml` | Python 打包配置 | 包名 neoskills、Python 3.13+、入口点 |
| `Dockerfile` | 容器化 | 便于在干净环境复现 |
| `main.py` | 顶层占位脚本 | 目前只有 `print("Hello from neoskills!")`，真正的入口在 `src/neoskills/cli/main.py` |
| `neoskills_v0_1.md` / `v0_2` / `v0_21` / `v0_3` | 设计文档快照 | 能看出项目是"先写设计、再写代码"的迭代节奏 |
| `.claude-plugin/plugin.json` | Claude Code 插件清单 | 把整个仓库当作一个可安装插件 |
| `commands/ns.md` | 斜杠命令 `/ns` | 在会话内调用 CLI，部分子命令转交专门 agent |
| `agents/` | 4 个专用子智能体定义 | `skill-scanner`、`skill-importer`、`skill-deployer`、`skill-dedup` |
| `skills/` | 仓库自带的技能 | `bank-status`、`skill-dedup`（含 `scripts/dedup_scan.py`） |
| `docs/` | 设计文档 | `ontology-design.md` + `plans/` 下两份组织方案 |
| `src/neoskills/cli/` | 命令行层 | `main.py` 用 Click 组装子命令，另有 `init/ tap/ brew_install/ link/ update/ list/ doctor/ create/ push/ migrate/ config/ enhance/ agent/ plugin/ schedule/ ontology` 等指令模块 |
| `src/neoskills/core/` | 领域内核 | `tap`（源）、`cellar`（本地仓库）、`manifest`、`checksum`、`linker`（软链接）、`index`、`resolver`、`namespace`、`frontmatter`、`mode`、`auth`、`config`、`workspace`、`models` |
| `src/neoskills/adapters/` | 多智能体适配层 | `base.py` 抽象 + `claude/`、`opencode/`、`openclaw/` 三个实现 + `factory.py` 工厂 |
| `src/neoskills/ontology/` | 本体层 | `engine`、`graph`、`loader`、`taxonomy`、`composition`、`lifecycle`、`versioning`、`writer`、`scaffold`、`export`、`templates/*.yaml.template` |
| `src/neoskills/meta/` | 技能增强 | `enhancer.py`：用大模型给技能补描述/元数据 |
| `src/neoskills/plugin/` | 插件运行时 | `schema.py`、`plugin_context.py` |
| `src/neoskills/runtime/` | 运行时装配 | `deps.py`、`claude/plugin.py` |
| `src/neoskills/translators/` | 格式翻译 | 在不同 agent 的技能格式之间转换 |
| `.github/workflows/` | CI/CD | `ci.yml` 测试、`release.yml` 发布到 PyPI |

一句话读结构：**`cli` 只是壳，`core` 才是引擎，`adapters` 负责"跟谁对接"，`ontology` 负责"技能之间是什么关系"，`translators` 负责"换一种说法"。** 这种分层说明作者不是写脚本，而是在做一个可长期演进的产品。

## 三、仓库里有哪些技能

仓库 `skills/` 目录在**这个仓库自身**里只放了两个技能样例，但它的意义不在于数量，而在于展示 bank 的典型技能形态：

### 1. `skills/bank-status` —— "只读型"技能
- 触发条件：用户问"我的技能仓库里有什么、状态如何"。
- 做法：读 `~/.neoskills/registry.yaml`（技能目录）→ 读 `state.yaml`（当前已部署哪些）→ 读 `LTM/mappings/targets/`（配置了哪些目标智能体）→ 汇总输出"仓库总数 / 目标 / 已嵌入 / 最近导入 5 条"。
- 特点：**不修改任何东西**，只做投影和汇报，属于查询类技能。它顺带告诉用户下一步能跑哪些命令（`scan` / `import` / `embed`），把"看"和"做"接上。

### 2. `skills/skill-dedup` —— "带脚本的执行型"技能
- 触发条件：用户提到重复技能、要清理、要审计技能库存、刚导入完技能。
- 做法：调用同目录下的 `scripts/dedup_scan.py`，把重复分成三类：
  1. **精确重复（Exact）**：内容 SHA256 完全一致 → 安全，可把各处副本换成指向 bank 的软链接；
  2. **分叉副本（Diverged）**：技能名相同但内容不同 → 自动挑"更丰富"的那份（文件数更多）建议导入 bank，而不是粗暴覆盖；
  3. **名称相近（Name-Similar）**：名字像但不是同一个技能 → 交给人工判断，不自动合并。
- 安全设计：`--dry-run` 先预览、真正执行时把原副本备份成 `.<skill>.dedup-backup`、支持 `--json` 给程序消费、支持 `--threshold` 调相似度阈值（默认 0.80）、支持 `--repos` 扫远程仓库、`--no-plugins` 跳过插件目录。
- 特点：**这是"技能调用脚本"的范式**：SKILL.md 负责"什么时候用、怎么用"，脚本负责确定性执行，把 LLM 的不确定性挡在判断之外。

### 3. `agents/` 里四个子智能体是"技能的执行者"
`agents/skill-scanner.md`、`skill-importer.md`、`skill-deployer.md`、`skill-dedup.md` 是子智能体定义（带触发示例、工具白名单、职责、流程），配合 `commands/ns.md`：`/ns dedup` 这类命令会被路由到对应 agent 跑多步自主流程；而 `/ns validate`、`/ns embed` 这类确定性命令直接调 CLI。**该用模型的地方用模型，该用脚本的地方用脚本**，这个边界划得很清楚。

## 四、最有意思的技能：`skill-dedup`

如果只挑一个，我选 `skill-dedup`，理由有三层：

1. **它解决的是真问题，而且是这个仓库存在的前提。** neoskills 的核心承诺是"多智能体共用一套技能"，但共用必然带来"同一技能多份副本"。如果不去重，bank 越大越乱，用户最后还是会退回各自为政。去重不是附属功能，而是这套架构能不能自洽的地基。
2. **它的三类划分体现了对"重复"的正确理解。** 新手做去重只会比文件名；比文件名会把"同名不同版"误删（数据丢失），也会漏掉"名字不同其实同源"。作者区分"完全相同 / 同名分叉 / 名字相近"，分别对应"自动合并 / 择优选入 / 人工裁决"，这正是包管理器处理冲突的标准做法。
3. **它的工程细节可复用到我自己的项目。** `--dry-run` + 自动备份 + JSON 输出 + 可调阈值，四件事加起来就是"可安全重复运行的运维脚本"模板。我在 C10 里写自己的技能时，也照这个模板加了"先预览再执行"。

顺带一句：`bank-status` 虽然简单，但它暴露了 neoskills 的真实数据结构（`registry.yaml` / `state.yaml` / `LTM/mappings/targets/`），是理解整个系统最快的入口。两个技能一"读"一"写"，刚好构成最小闭环。

## 五、代码分层怎么读

读完 `src/neoskills/cli/main.py` 能看清作者的组装方式：用 Click 建一个 group，先注册 `init`，其余命令放在 `_register_later_commands()` 里"能导入就注册、没实现就静默跳过"。这种写法在项目早期很实用——**CLI 帮助里不会出现半成品命令，但代码可以分阶段落地**。同时它也暴露了一个风险：如果某个模块 import 失败（比如依赖缺失），命令会静默消失而不是报错，排查时容易误判成"这个版本没这个功能"。

整个数据流可以概括为一条链：

```
用户/Agent 请求
   ↓ commands/ns.md（会话内） 或 neoskills <cmd>（终端）
cli/*_cmd.py          参数解析、交互提示、输出格式
   ↓
core/*                领域逻辑：tap 拉源 → cellar 落盘 → manifest/checksum 记账 → linker 软链接
   ↓
adapters/<agent>      把统一技能表示翻译成 Claude / OpenCode / OpenClaw 各自的目录与格式
   ↓
ontology/*            读取每技能的 ontology.yaml，建图、算组合、管生命周期与版本
```

这里最关键的一个设计判断是**用软链接而不是复制来"部署"**。复制会产生多份真相，改一处另几处过期，正是它想消灭的问题；软链接让 `~/.claude/skills/x` 永远指向 bank 里的那一份，天生单源。代价是跨平台问题——Windows 上创建符号链接默认需要管理员权限或开发者模式，这也是这套工具在 Windows 上最容易踩的坑。

## 六、我的评价：它做对了什么，还缺什么

**做对的：**
1. **抽象选得准。** 把"技能"当成"包"来处理，于是 Homebrew 那一整套（tap / cellar / install / upgrade / doctor / dedup）可以整块借过来，不用重新发明概念。
2. **单源 + 软链接**，从机制上避免多副本漂移。
3. **可移植性靠适配器**，新增一个智能体只要写一个 adapter，不用改内核。
4. **本体层（ontology）是加分项**：技能之间"谁依赖谁、谁和谁组合、什么时候该退役"，这些关系光靠文件夹表达不了，用图才表达得了。
5. **工程纪律**：CI + release workflow 自动发 PyPI、`doctor` 自检、`--dry-run` 预览、备份后再改。

**我看到的不足 / 风险：**
1. `main.py` 还是 `print("Hello from neoskills!")` 的占位，说明入口还没收敛，新读者第一次跑容易困惑"到底该跑哪个"。
2. **Python 3.13+ 门槛偏高**，很多机器默认还是 3.10/3.11，会挡住一部分人。
3. **Windows 软链接权限**没有看到明显的降级方案（比如 junction 或复制 + 校验提示），跨平台体验会打折。
4. **双源真相风险**：技能既有 `SKILL.md` 里的 frontmatter，又有 `ontology.yaml`；两边都描述名字/描述时，谁是权威？需要明确"以哪边为准、另一边怎么校验"，否则去重和索引会互相打架。
5. **缺少显式的版本锁定**：有 `manifest` / `checksum`，但从 README 看不出类似 `lockfile` 的"我这套环境钉在这几个版本"的机制，多人协作时复现性会弱一些。
6. 版本设计文档堆了 `v0_1 / v0_2 / v0_21 / v0_3` 四份在根目录，长期应移进 `docs/versions/`，根目录只留 README。

## 七、我在这个仓库里做的贡献（Level 3）

- 新建分支 `docs/zh-analysis-jiajingwen`，不直接改主干；
- 新增 `贾静文_C5A_仓库分析.md`（本文件）：中文深度分析，补上原仓库没有的中文入口；
- 新增 `README.zh-CN.md`：把英文 README 的核心段落翻成中文速览，方便中文读者 5 分钟上手；
- Commit 后 Push 到我的 fork，并向原仓库发起 Pull Request（可选动作，做了更好）。

## 八、对 C10 的启发

1. **技能要能被"发现"，不只是被"写出来"**：`description` 里写清触发场景（什么时候用我），比写"我能做什么"更重要。
2. **确定性的事交给脚本，判断的事交给模型**：这是 `skill-dedup` 教给我的最重要一条，我在 C10 的五个技能里都按这个原则拆了 `SKILL.md` + 脚本。
3. **改动前先预览、改完能回滚**：`--dry-run` 和备份应该成为默认习惯。
4. **长期性来自结构，不来自记忆**：neoskills 用 registry / state / ontology 三个文件把"我现在有什么"写下来，而不是靠模型记住。我的第二大脑也用同样的思路做持久化。
