---
type: question
id: ml-ai/agent/multi-agent-common-architectures
title: 多 Agent 常见架构有哪些
category: ml-ai
subcategory: agent
difficulty: medium
tags: [multi-agent, architecture, taxonomy]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线, 华大制造]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 多 Agent 常见架构有哪些

## 问题描述

"多 agent 的架构一般常见的架构有哪些？"（中泓一线）

## 解答

业界常见四类：

| 架构 | 别名 | 特征 | 适用 |
| --- | --- | --- | --- |
| **Sequential** | Pipeline / Waterfall | 串行接力 | 线性工序、确定性流程 |
| **Parallel** | Fan-out / Map-Reduce | 并行 + 聚合 | 无依赖子任务、多源召回 |
| **Supervisor / Router** | Hierarchical / Orchestrator-Worker | 中心调度者路由 | 开放任务、动态选工具 |
| **Network / Conversational** | Peer-to-Peer / Debate | agent 间自由对话、可辩论 | 复杂推理、辩论/反思 |

补充模式：
- **Reflection（反思）** — agent A 生成，agent B 批判，A 修订，迭代。
- **ReAct** — 单 agent 内的 Thought-Action-Observation 循环（不算 multi-agent，但是 multi-agent 的基本积木）。
- **Plan-and-Execute** — Planner 拆解 → Executor 执行。

## 易错点

- 把 ReAct 当成 multi-agent 架构——ReAct 是单 agent 内的循环。
- 认为 Network 架构一定更好——它最难控制 token 成本和终止条件。

## 延伸

## 延伸

- 关联题：[[ml-ai/agent/multi-agent-orchestration-architecture]]
