---
type: question
id: ml-ai/agent/skill-loading-mechanism
title: Skill 何时调用哪个 / 加载机制 (two-stage 路由)
category: ml-ai
subcategory: agent
difficulty: medium
tags: [skill, loading, routing, progressive-disclosure, framework]
languages: []
role: [ai-app, sde, backend]
companies: [华大制造, 广州大娱, 安克创新, OPPO, 北京用友, 有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Skill 何时调用哪个 / 加载机制 (two-stage 路由)

## 问题描述

Skill 怎么知道什么时候应该调用哪个 skill？Skills 加载机制是自己写的还是框架自带？

## 解答

### 何时调用哪个 skill —— two-stage 路由

不是"自动知道"，而是 **two-stage**：
- **Stage 1（路由）**：把所有 skill 的 **description** 拼进 context，让模型选一个 skill（或由 router agent 选）。
- **Stage 2（加载执行）**：选中后，**才把该 skill 的完整 prompt + tools 加载进 context**（渐进式披露，省 token）。

这正是 Claude Skills / Cursor Skills / Agent Skills 的共同设计：**description 是"门牌"，加载是"进屋"**。

### 加载机制：自写 vs 框架自带

- **Claude Code / Cursor Skills**：框架自带——扫 `.cursor/skills/*/SKILL.md`，按 description 注入。
- **Google ADK**：通过 `Agent` 的 `tools` + `sub_agents` 声明，框架调度。
- **自研框架**：常见做法是 skill registry（YAML/MD 文件目录）+ router prompt + 动态拼装。

### 框架自带的细节（Claude Code / Cursor）

- 扫描约定目录下的 `SKILL.md`，解析 frontmatter（name + description + 可选 triggers）。
- 把所有 skill 的 description（不是正文）拼进 system prompt 供模型路由。
- 模型选中后框架把对应 `SKILL.md` 正文 + 声明的 tools 注入当前 context。
- 文件系统监听 + 热重载：人工新增/删除/改 skill 文件，框架感知后下一轮路由生效（无需重启会话）。

## 易错点

- 把"何时调用"寄托于模型自由判断——必须靠 description 做 Stage 1 路由信号。
- 自研框架把所有 skill 正文全量注入——丢失渐进式披露的核心收益。

## 延伸

## 延伸

- 关联题：[[ml-ai/agent/skill-what-and-why]]
- 关联题：[[ml-ai/agent/skill-self-evolution-hermes]]
- 关联题：[[ml-ai/agent/agent-function-call-mechanism]]
