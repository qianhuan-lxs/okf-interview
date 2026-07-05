---
type: question
id: ml-ai/agent/agent-function-call-mechanism
title: Agent 工具调用机制 (Function Call 原理)
category: ml-ai
subcategory: agent
difficulty: medium
tags: [function-call, tool-calling, llm, json-schema]
languages: []
role: [ai-app, sde, backend]
companies: [华大制造, 广州大娱, 中泓一线]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Agent 工具调用机制 (Function Call 原理)

## 问题描述

大模型输出都是文字，它是怎么有能力去调用一个接口的？谁去调的 MCP 工具？是大模型调的吗？Function Call 内部机制是什么？

## 思路

**关键澄清：大模型本身不"执行"任何东西，它只产出结构化指令；执行的是 agent runtime（你的代码）。**

## 解答

完整流程：

1. **注册阶段**：你把工具的 JSON Schema（name / description / parameters）放进 system prompt 或 `tools` 字段一起送给模型。
2. **决策阶段**：模型根据用户问题，决定是否需要调工具。若需要，它在响应里产出一段 **结构化 JSON**（`tool_calls` 字段），内容是 `{"name": "search", "arguments": {...}}`——注意这是**文字输出**，不是动作。
3. **解析阶段**：agent runtime（LangChain / ADK / 你的代码）解析这段 JSON，校验 schema。
4. **执行阶段**：runtime 用反射/分发调用真正的函数（本地函数 / HTTP 接口 / MCP tool）。
5. **回填阶段**：把函数返回值作为 `tool` role message 拼回对话历史，再次送给模型。
6. **生成阶段**：模型基于工具结果生成最终自然语言回答。

训练侧支撑：现代模型（GPT-4/Claude/Gemini）经过了 **function-calling fine-tuning**，学会在合适时机产出符合 schema 的 JSON，而不是自由文本。

```
User ──→ LLM ──→ tool_calls(JSON) ──→ Runtime 执行 ──→ tool result ──→ LLM ──→ Answer
```

## 易错点

- 以为"模型直接调用了接口"——是 runtime 调的，模型只产出意图。
- 不做 schema 校验——模型偶尔产出非法 JSON 会导致 runtime 崩。
- 工具 description 写得含糊——模型选错工具或根本不调（见 [[ml-ai/mcp/mcp-vs-skill-difference]]）。

## 延伸

## 延伸

- 关联题：[[ml-ai/mcp/mcp-protocol-understanding]]
- 关联题：[[ml-ai/agent/skill-what-and-why]]
