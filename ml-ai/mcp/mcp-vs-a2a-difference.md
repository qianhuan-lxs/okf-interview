---
type: question
id: ml-ai/mcp/mcp-vs-a2a-difference
title: MCP vs A2A 区别
category: ml-ai
subcategory: mcp
difficulty: medium
tags: [mcp, a2a, agent2agent, protocol, comparison]
languages: []
role: [ai-app, sde, backend]
companies: [北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# MCP vs A2A 区别

## 问题描述

MCP 跟 ATA（A2A）有什么差别？

## 解答

| 维度 | MCP | A2A (Agent2Agent) |
| --- | --- | --- |
| 全称 | Model Context Protocol | Agent2Agent Protocol |
| 提出方 | Anthropic (2024.11) | Google (2025.04) |
| 解决 | Agent ↔ **工具/数据源** | Agent ↔ **Agent** |
| 通信方 | LLM client ↔ tool server | agent ↔ agent |
| 暴露 | tools / resources / prompts | agent card（能力声明 + 任务接口） |
| 范例 | Cursor 调本地文件工具 | 两个 agent 互相委派任务 |

**一句话区别：MCP 给 agent 装"手"（调工具），A2A 让 agent 之间"对话协作"。**

### 互补关系

- A2A 协作过程中，单个 agent 仍可用 MCP 调工具。
- 例：agent A 收到任务 → 通过 A2A 委派给 agent B → B 用 MCP 调数据库 → 结果沿 A2A 回 A。

## 易错点

- 把 A2A 当成 MCP 的替代——它们解决不同层问题，常常共存。

## 延伸

## 延伸

- 关联题：[[ml-ai/mcp/mcp-protocol-understanding]]
- 关联题：[[ml-ai/agent/multi-agent-orchestration-architecture]]
