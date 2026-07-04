---
type: question
id: ml-ai/observability/agent-trace-span-model
title: Agent trace span 模型 (一棵标准 trace 长什么样)
category: ml-ai
subcategory: observability
difficulty: medium
tags: [tracing, span-model, agent, opentelemetry, observability]
languages: [python, typescript]
role: [ai-app, sde, backend, ml-engineer]
companies: [探迹]
source: ""
status: reviewed
timestamp: 2026-05-26
---

# Agent trace span 模型 (一棵标准 trace 长什么样)

## 问题描述

Agent 一次运行的 trace 该怎么结构化？span 树长什么样？每类 span 挂什么属性？

## 一、为什么需要标准 span 模型

Agent 不像普通服务"一个请求一个 span"。一次 agent run 包含：多次 LLM 调用、多次工具调用、可能的 RAG 检索、子 agent 嵌套。没有标准 span 模型，调试 agent 失败时无法定位"是哪次 LLM 调用选错工具"还是"工具返回错"还是"检索召回差"。

## 二、canonical span 树

```
invoke_agent (root span, agent 名/会话 id)
├── embeddings (query 向量化, RAG 入口)
├── retriever (向量/BM26 召回, recall@k)
│   └── reranker (cross-encoder 重排)
├── chat (LLM 调用 1: 决定调工具)
│   └── finish_reasons=["tool_calls"], input_tokens, output_tokens
├── execute_tool (search_tool)
│   └── gen_ai.tool.name, args, result, latency
├── execute_tool (db_query)
├── chat (LLM 调用 2: 基于工具结果)
├── invoke_agent (子 agent: code_reviewer)
│   ├── chat
│   └── execute_tool
└── chat (最终回答, finish_reasons=["stop"])
```

## 三、span 类型与属性

| Span 类型 | operation / kind | 关键属性 |
| --- | --- | --- |
| **Agent 根** | `invoke_agent` | `gen_ai.agent.name` / `gen_ai.agent.id` / `gen_ai.conversation.id` |
| **LLM 调用** | `chat` | `gen_ai.request.model` / `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens` / `gen_ai.response.finish_reasons` / `gen_ai.provider.name` |
| **工具调用** | `execute_tool` | `gen_ai.tool.name` / `gen_ai.tool.call.id` / args / result |
| **检索** | `retriever` (OpenInference kind) | query / retrieved docs / scores |
| **重排** | `reranker` | input docs / output docs / model |
| **Embedding** | `embeddings` | model / vector dim / token count |
| **链/编排** | `chain` (OpenInference) | 编排步骤 |

## 四、为什么是嵌套树而非扁平列表

- **父 子关系表达因果**：LLM 调用产出的 tool_calls → 对应的 execute_tool span 作为子 span，能追溯"哪次 LLM 决定触发了哪次工具"。
- **子 agent 嵌套**：`invoke_agent` 套 `invoke_agent`，反映 multi-agent 编排结构。
- **代价归因**：子 span 的 token/cost 汇总到父 agent span，算出"这个子 agent 这次 run 花了多少"。
- **延迟分解**：父 span 总时长 = Σ 子 span + 编排开销，定位瓶颈。

## 五、对 agent 调试的价值

| 故障现象 | 看哪类 span |
| --- | --- |
| Agent 选错工具 | `chat` span 的 `finish_reasons` + tool_calls 字段 |
| 工具调用超时 | `execute_tool` span 的 latency |
| RAG 召回差 | `retriever` span 的 retrieved docs vs 期望 |
| 成本暴涨 | `chat` span 的 token usage 聚合 |
| 子 agent 死循环 | 嵌套 `invoke_agent` 深度 + 重复 `chat` |
| 幻觉 | 对比 `chat` 的 input context vs output claim |

## 六、自动 instrumentation

不要手写每个 span。用：
- **OpenInference** instrumentation（LangChain/LlamaIndex/ADK/CrewAI 自动埋点）
- **OpenLLMetry**（OpenAI/Anthropic/向量库自动埋点）
- **OpenAI Agents SDK** 默认开 tracing 就发这棵树
- 自研框架：在编排层包一层 `start_as_current_observation`，工具调用 wrapper 自动建 execute_tool span

## 易错点

- 把所有 LLM 调用平铺成兄弟 span 而非嵌套 → 丢失因果链。
- 不记 `finish_reasons` → 无法区分"答完"和"要调工具"。
- 检索 span 不记 retrieved docs 内容 → 召回差时无法回放。

## 延伸

## 延伸

- 关联题：[[ml-ai/observability/opentelemetry-genai-semantic-conventions]]
- 关联题：[[ml-ai/observability/langfuse-observability-design]]
- 关联题：[[ml-ai/agent/multi-agent-orchestration-architecture]]
