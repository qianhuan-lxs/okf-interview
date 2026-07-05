---
type: question
id: ml-ai/agent/skill-self-evolution-hermes
title: Skill 自进化 / 自净化 (Hermes + GEPA)
category: ml-ai
subcategory: agent
difficulty: hard
tags: [skill, self-evolution, hermes, gepa, dspy, self-improving]
languages: []
role: [ai-app, sde, backend]
companies: [OPPO, 有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-07-05
---

# Skill 自进化 / 自净化 (Hermes + GEPA)

## 问题描述

Skill 的自净化 / 自进化怎么实现？有什么可参照的工程实现？

## 思路

"自进化"不是营销词，Hermes（Nous Research，2026-02 开源，4 个月 175k stars）给了可参照的工程实现。分三层理解。

## 解答

### 第一层：在线 distill-validate-prune（Hermes Agent 原生）

Hermes 不只是"跑 skill"，它**从自己的执行轨迹里写新 skill**：完成一次 ≥5 工具调用的复杂任务后，自动把可复用技术沉淀成 `SKILL.md`，零人工编写。内置 85 个 skill / 22 类，但关键数字是"人要写几个 before agent 开始自己加"——很少。skill 是可读 Markdown（合 agentskills.io 开放标准），可移植到其他兼容运行时。

闭环（也是"自净化"的工程答案）：
1. **Detect** — 用 transcript/工具调用信号识别复杂工作（如 ≥5 tool call + 文件编辑累积）。
2. **Nudge** — 在对的时机提醒 agent 蒸馏（CC 插件用 `Stop` hook，**每段工作只阻塞一次**；declined 后不重复，只在新工作再达阈值才重触发）。
3. **Write/patch** — 专门 subagent 写 `~/.claude/skills/*/SKILL.md`，**优先 patch 既有 skill → 归并到 umbrella skill → 加 reference 文件 → 实在不行才新建 class-level skill**。description 合 Anthropic skill-creator 规范（第三人称情境匹配 + 具体触发短语）。
4. **Validate & rollback** — 自动校验 malformed 编辑，挂了就回滚。
5. **Track usage / 自净化** — 不用的 agent-created skill **30 天标 stale、90 天归档**（可恢复）；被反复使用（`use_count >= 3`）的 skill 老化速度减半。`/curate-skills` 用 LLM 做 umbrella 合并，先 plan 后批准才 apply。
6. **Share** — proven skill 通过 git repo 共享给团队，opt-in、review-gated、永不覆盖个人定制。

### 第二层：离线进化（hermes-agent-self-evolution，DSPy + GEPA）

`NousResearch/hermes-agent-self-evolution` 是**独立仓库，作用于 hermes-agent 而非其内部**。用 **DSPy + GEPA（Genetic-Pareto Prompt Evolution，ICLR 2026 Oral）** 反思式进化 skill 文本：

- GEPA **读执行轨迹理解"为什么失败"**（不只是"失败了"），提针对性突变；Pareto 选择最优变体。
- **无需 GPU**，全走 API call，~$2-10/run。
- **约束门**：pytest 通过、size 上限（skill ≤15KB、tool desc ≤500 字符）、caching 兼容（不能 mid-conversation 改）、语义保留（不偏原意）、**PR review（人在环里，永不直接 commit）**。
- 数据源：`sessiondb`（从 Claude Code / Copilot / Hermes 真实轨迹抽）或 `synthetic`（算法生成 eval case）。
- 分阶段：Phase 1 SKILL.md ✅ 已实现；Phase 2 tool 描述 / Phase 3 system prompt / Phase 4 tool 代码（Darwinian Evolver, AGPL）/ Phase 5 连续闭环 —— 规划中。

```bash
python -m evolution.skills.evolve_skill --skill github-code-review --iterations 10 --eval-source sessiondb
```

### 第三层：把 Hermes 能力 port 进 Claude Code（社区插件）

CC 原生 skill 是**人写 / 装市场**的，不会从轨迹自己写——这正是 Hermes 填的缺口。三个插件把 Hermes 自学习引擎 embed 进 CC：

| 插件 | 机制 | 命令 |
| --- | --- | --- |
| `UniM0cha/claude-self-improving-skills` | Stop hook nudge + distiller subagent + curator loop | `/distill-skill`、`/curate-skills` |
| `Stealthy-McStealth/self-evolve` | skill 进化 + **adherence enforcement / drift 防护**（重读已加载 skill 防 mid-trajectory 漂移） | `/improve-urself`（非全自动） |
| `galixiaomaohan/claude-code-hermes-plugin` | Skills Hub / Auto-Skill / Skill Optimization / Memory / Context 压缩 / Trajectory 日志 | `/hermes:create-skill`、`/hermes:optimize-skill` 等 |

### 诚实的边界

- 自生成 skill 是**草稿需人工审**，不是可信自动化——给 unreviewed 访问敏感资源要警惕。
- `hermes-agent-self-evolution` 是 **human-initiated + review-gated**（人在环里），不是无人值守。
- **非单调收益**：中游模型从 evolved skill 获益最大；很弱的模型即使 skill 完美也无法可靠调用/遵循；很强的模型本就能即兴发挥。
- `self-evolve` 自己说：全自动化从对话轨迹进化 skill 需要更多基建，是 future work。

## 易错点

- 把"自进化"当无人值守自动化——实际都是 human-in-loop / review-gated。
- 以为 CC 原生 skill 会自进化——不会，CC 只加载人写的；自进化要接 Hermes 类插件/外接进化管线。

## 延伸

## 延伸

- 关联题：[[ml-ai/agent/skill-what-and-why]]
- 关联题：[[ml-ai/agent/skill-loading-mechanism]]
- 关联题：[[ml-ai/observability/claude-code-hooks-implementation]]
- 关联题：[[ml-ai/mcp/mcp-vs-skill-difference]]
