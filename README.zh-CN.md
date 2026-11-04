# neoskills（中文速览）

> 本文是 `README.md` 的中文速览，方便中文读者 5 分钟理解这个项目。原文以英文 README 为准。

**给 AI 编程智能体用的 Homebrew 式技能管理器。**

neoskills 在 Claude Code、OpenCode、OpenClaw 等不同智能体生态之间管理可移植的技能定义：在一处浏览技能、同步到 GitHub、用软链接按需部署、并通过内置本体图（ontology）发现技能之间的关系。

## 安装

```bash
pip install neoskills      # 推荐
uv tool install neoskills  # 或使用 uv
```

要求：Python 3.13+、Git（tap 操作需要）。

## 快速开始

```bash
neoskills init                          # 1. 初始化工作区
neoskills tap https://github.com/your-org/my-skills   # 2. 添加一个技能源
neoskills list                          # 3. 浏览
neoskills list --linked                 #    看看已经部署了什么
neoskills search "document processing"  #    跨源搜索
neoskills install kstar-loop            # 4. 安装并软链接到你的智能体
neoskills create my-new-skill -d "它做什么" --type task   # 5. 创建自己的技能
neoskills doctor                        # 6. 体检
```

## 工作原理

`neoskills init` 创建 `~/.neoskills/` 工作区与默认 tap。`install` 在 tap 中找到技能，并在智能体的技能目录（如 `~/.claude/skills/`）里创建软链接——**单源真相，不复制副本**。

```
~/.neoskills/
├── config.yaml          # 目标、tap、默认值
├── taps/                # git 克隆下来的技能仓库
│   └── mySkills/skills/<skill-id>/
│       ├── SKILL.md      # 技能定义（frontmatter + 正文）
│       ├── ontology.yaml # 图元数据（可选，建议有）
│       └── scripts/      # 可执行代码（可选）
```

## 目录速查

| 目录 | 作用 |
|------|------|
| `src/neoskills/cli/` | Click 命令行层：init / tap / install / link / update / list / doctor / create / push / ontology 等 |
| `src/neoskills/core/` | 领域内核：tap、cellar、manifest、checksum、linker、index、resolver、namespace、frontmatter |
| `src/neoskills/adapters/` | Claude / OpenCode / OpenClaw 适配器与工厂 |
| `src/neoskills/ontology/` | 本体层：图、分类、组合、生命周期、版本、导出 |
| `agents/` | 4 个子智能体：scanner / importer / deployer / dedup |
| `commands/ns.md` | 会话内 `/ns` 斜杠命令 |
| `skills/` | 自带技能样例：`bank-status`、`skill-dedup` |

## 阅读建议

1. 先看 `skills/bank-status/SKILL.md`——它暴露了 `registry.yaml` / `state.yaml` / `LTM/mappings/targets/` 三个真实数据文件；
2. 再看 `skills/skill-dedup/SKILL.md` 与其 `scripts/dedup_scan.py`——"技能 = 说明 + 确定性脚本"的范例；
3. 最后读 `src/neoskills/core/linker.py` 与 `adapters/factory.py`——"单源 + 软链接"和"可扩展适配"两个核心设计。

---

中文分析（含评价与改进建议）：见 `贾静文_C5A_仓库分析.md`。
