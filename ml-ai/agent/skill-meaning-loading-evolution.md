---
type: question
id: ml-ai/agent/skill-meaning-loading-evolution
title: Skill 的含义 / 加载机制 / 自进化
category: ml-ai
subcategory: agent
difficulty: medium
tags: [skill, prompt-engineering, loading, self-evolution]
languages: []
role: [ai-app, sde, backend]
companies: [华大制造, 广州大娱, 安克创新, OPPO, 北京用友, 有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Skill 的含义 / 加载机制 / 自进化

## 问题描述

你怎么理解 skill？skill 怎么知道什么时候应该调用哪个 skill？skills 加载机制是自己写的还是框架自带？Skill 的自净化？Skill 的优点？Skill 为什么不能只是 prompt？

## 思路

**Skill = 一份"给模型看的工作说明书"**，比裸 prompt 更结构化、可组合、可按需加载。

## 解答

### Skill 通常包含什么

1. **Description（入口描述）** — 渐进式披露的关键：模型先看到所有 skill 的 description，决定加载哪个。
2. **System prompt / Instructions** — 该 skill 的工作方式、约束、输出格式。
3. **Tools** — 这个 skill 可调用的工具集合。
4. **Examples / Few-shot** — 示例输入输出。
5. **Guardrails** — 边界条件、禁止行为。

### 何时调用哪个 skill

不是"自动知道"，而是 **two-stage**：
- **Stage 1（路由）**：把所有 skill 的 **description** 拼进 context，让模型选一个 skill（或由 router agent 选）。
- **Stage 2（加载执行）**：选中后，**才把该 skill 的完整 prompt + tools 加载进 context**（渐进式披露，省 token）。

这正是 Claude Skills / Cursor Skills / Agent Skills 的共同设计：description 是"门牌"，加载是"进屋"。

### 加载机制：自写 vs 框架自带

- **Claude Code / Cursor Skills**：框架自带——扫 `.cursor/skills/*/SKILL.md`，按 description 注入。
- **Google ADK**：通过 `Agent` 的 `tools` + `sub_agents` 声明，框架调度。
- **自研框架**：常见做法是 skill registry（YAML/MD 文件目录）+ router prompt + 动态拼装。

### 自进化 / 自净化

指 skill 库随使用反馈迭代：失败 case 自动回流、评测、改写 description 或 prompt。OPPO/有赞问的"自净化"通常指自动剔除低效 skill 或修正其 description。

### 为什么不能只是 system prompt

- **Token 成本**：所有 skill 全塞 system prompt 会爆炸；渐进式披露按需加载才省。
- **可组合性**：skill 是模块化单元，可跨 agent 复用；裸 prompt 难复用。
- **可观测 / 可版本化**：skill 是独立文件，可 diff、可评测、可回滚。

## 易错点

- description 写成给人看的标签，而不是给模型看的"何时调用我"判断依据。
- 把所有 skill 全量注入——丢失渐进式披露的核心收益。

## 延伸

## 延伸

- 关联题：[[ml-ai/mcp/mcp-vs-skill-difference]]
- 关联题：[[ml-ai/agent/agent-function-call-mechanism]]
