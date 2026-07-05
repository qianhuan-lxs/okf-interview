---
type: question
id: ml-ai/agent/skill-what-and-why
title: Skill 是什么 / 包含什么 / 为什么不只是 system prompt
category: ml-ai
subcategory: agent
difficulty: medium
tags: [skill, prompt-engineering, progressive-disclosure]
languages: []
role: [ai-app, sde, backend]
companies: [华大制造, 广州大娱, 安克创新, OPPO, 北京用友, 有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-07-05
---

# Skill 是什么 / 包含什么 / 为什么不只是 system prompt

## 问题描述

你怎么理解 skill？Skill 通常包含什么？Skill 的优点？Skill 为什么不能只是 prompt？

## 思路

**Skill = 一份"给模型看的工作说明书"**，比裸 prompt 更结构化、可组合、可按需加载。

## 解答

### Skill 通常包含什么

1. **Description（入口描述）** — 渐进式披露的关键：模型先看到所有 skill 的 description，决定加载哪个。
2. **System prompt / Instructions** — 该 skill 的工作方式、约束、输出格式。
3. **Tools** — 这个 skill 可调用的工具集合。
4. **Examples / Few-shot** — 示例输入输出。
5. **Guardrails** — 边界条件、禁止行为。

### 为什么不能只是 system prompt

- **Token 成本**：所有 skill 全塞 system prompt 会爆炸；渐进式披露按需加载才省。
- **可组合性**：skill 是模块化单元，可跨 agent 复用；裸 prompt 难复用。
- **可观测 / 可版本化**：skill 是独立文件，可 diff、可评测、可回滚。
- **可进化**：skill 是独立基因，GEPA 这类算法才有优化着力点——monolithic system prompt 只有一个基因，没法做反思式进化。

## 易错点

- description 写成给人看的标签，而不是给模型看的"何时调用我"判断依据。
- 把所有 skill 全量注入——丢失渐进式披露的核心收益。

## 延伸

## 延伸

- 关联题：[[ml-ai/agent/skill-loading-mechanism]]
- 关联题：[[ml-ai/agent/skill-self-evolution-hermes]]
- 关联题：[[ml-ai/mcp/mcp-vs-skill-difference]]
