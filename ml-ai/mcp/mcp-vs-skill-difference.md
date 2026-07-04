---
type: question
id: ml-ai/mcp/mcp-vs-skill-difference
title: MCP vs Skill 区别
category: ml-ai
subcategory: mcp
difficulty: medium
tags: [mcp, skill, comparison, prompt-engineering]
languages: []
role: [ai-app, sde, backend]
companies: [安克创新, 有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# MCP vs Skill 区别

## 问题描述

MCP 跟 skill 什么区别？MCP 和 Skill 就是约束和 model 吧？各自用在什么场景？如果 Skill 只是约束+prompt，直接在 System Prompt 里写不行吗？

## 解答

**一句话：MCP 管"能调什么工具"，Skill 管"怎么干活的方法论"。**

| 维度 | MCP | Skill |
| --- | --- | --- |
| 本质 | 协议（接入层） | 工作流封装（认知层） |
| 内容 | tool schema + 调用接口 | description + prompt + tools + examples + guardrails |
| 解决 | "工具怎么被发现、被调用" | "任务该怎么想、怎么做" |
| 粒度 | 单个工具/资源 | 一类任务的方法论 |
| 复用 | 工具跨 agent 复用 | 工作流跨场景复用 |
| 类比 | API 网关 | 一份 SOP 手册 |

### 关系（不是替代）

Skill **可以包含** 一组 MCP tools。即 Skill 在 description 里声明"我这个活儿要用这几个 MCP 工具"，加载 skill 时把对应 MCP tools 一起挂上。

### "Skill 只是 prompt 行不行"

不行（见 [[ml-ai/agent/skill-meaning-loading-evolution]]）：
1. **渐进式披露** — 全塞 system prompt 会 token 爆炸；skill 按需加载。
2. **可组合** — skill 是模块，可跨 agent 复用、可 diff、可版本化。
3. **绑定工具** — skill 不只是文字，还绑 tools/guardrails，纯 prompt 没有这层。

### 场景选择

- 要让 agent 调外部系统（数据库/API/文件） → **MCP**
- 要把一类任务的最佳实践固化（如"做代码评审的标准流程"） → **Skill**
- 严肃 agent 通常 **两者都用**：Skill 定义"怎么做"，MCP 提供"用什么"。

## 延伸

## 延伸

- 关联题：[[ml-ai/agent/skill-meaning-loading-evolution]]
- 关联题：[[ml-ai/mcp/mcp-protocol-understanding]]
