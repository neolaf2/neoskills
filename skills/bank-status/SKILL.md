---
name: bank-status
description: Use when user asks about skill bank status, inventory, or what skills are available in neoskills. 当用户询问技能库状态、库存或可用技能时使用。
author: Richard Tong
tags: [neoskills, bank, status, monitoring]
---

# Bank Status / 技能库状态

Display the current status of the neoskills skill bank.
显示 neoskills 技能库的当前状态。

## Instructions / 操作指引

1. Read `~/.neoskills/registry.yaml` to get the skill catalog
   读取 `~/.neoskills/registry.yaml` 获取技能目录
2. Count total skills, their tags, and when they were last updated
   统计技能总数、标签及最后更新时间
3. Check `~/.neoskills/state.yaml` for any currently embedded skills
   检查 `~/.neoskills/state.yaml` 获取当前已嵌入的技能
4. Read target definitions from `~/.neoskills/LTM/mappings/targets/` to show configured targets
   从 `~/.neoskills/LTM/mappings/targets/` 读取目标定义以显示已配置的目标

## Output Format / 输出格式

Present a summary (展示摘要):
- **Bank / 技能库**: Total skills, last updated timestamp (总技能数、最后更新时间戳)
- **Targets / 目标**: List configured targets with skill counts (已配置的目标及技能数量)
- **Embedded / 已嵌入**: Any currently embedded skills (symlinked) (当前已嵌入的技能)
- **Recent / 最近导入**: Last 5 imported skills with provenance (最近 5 个导入的技能及来源)

## Quick Commands / 快捷命令

If the user wants to take action, suggest (如果用户希望执行操作，建议):
- `neoskills scan <target>` to discover new skills (发现新技能)
- `neoskills import from-target <target> --all` to import everything (导入全部)
- `neoskills embed --target <target>` to embed bank into agent (将技能库嵌入智能体)
