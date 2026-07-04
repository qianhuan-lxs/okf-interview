---
type: question
id: ml-ai/mcp/mcp-protocol-understanding
title: MCP 协议理解 (解决什么问题)
category: ml-ai
subcategory: mcp
difficulty: easy
tags: [mcp, protocol, tool-calling, standardization]
languages: []
role: [ai-app, sde, backend]
companies: [华大制造, 北京用友, 安克创新, 中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# MCP 协议理解 (解决什么问题)

## 问题描述

MCP 主要解决什么问题？MCP 的工具到工具调用这一套技术流程大概怎样？

## 解答

**MCP (Model Context Protocol)** 是 Anthropic 2024 年底开源的**开放协议**，把"模型 ↔ 外部工具/数据源"的接入标准化。类比：**USB-C 之于硬件，MCP 之于 LLM 工具接入**。

### 解决什么问题

- **N×M → N+M**：以前每个 Agent 框架 × 每个工具都要单独写适配；MCP 之后，工具写一份 MCP server，任何支持 MCP 的 client（Claude/Cursor/Cline/自研 agent）都能用。
- **协议统一**：tool 列表发现、调用、参数校验、结果回传都有标准 JSON-RPC 格式。
- **解耦**：工具方和 agent 方独立演进。

### 核心概念

- **MCP Server**：暴露 `tools` / `resources` / `prompts` 三类能力。
- **MCP Client**：agent 侧，连接 server，发现工具，把 tool schema 暴露给 LLM。
- **Transport**：stdio（本地）/ SSE / HTTP。

### 流程

1. Client 启动时连 server，调 `tools/list` 拿到工具 schema 列表。
2. Client 把 schema 转成 LLM 的 `tools` 字段。
3. LLM 决定调工具 → 产出 `tool_call`。
4. Client 调 server 的 `tools/call`，拿结果。
5. 结果回填 LLM。

## 易错点

- 把 MCP 等同于 Function Call——Function Call 是 **模型能力**，MCP 是 **接入协议**，MCP 之上仍走 Function Call。
- 以为 MCP server 必须本地——可远程 HTTP/SSE，正是网关场景的来源（见 [[ml-ai/mcp/mcp-gateway-architecture]]）。

## 延伸

## 延伸

- 关联题：[[ml-ai/mcp/mcp-gateway-architecture]]
- 关联题：[[ml-ai/agent/agent-function-call-mechanism]]
- 关联题：[[ml-ai/mcp/mcp-vs-a2a-difference]]
