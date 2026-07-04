---
type: question
id: ml-ai/observability/opentelemetry-genai-semantic-conventions
title: OpenTelemetry GenAI 语义约定 (Agent 可观测的通用语)
category: ml-ai
subcategory: observability
difficulty: hard
tags: [opentelemetry, genai, semantic-conventions, openinference, openllmetry, tracing]
languages: []
role: [ai-app, sde, backend, devops, ml-engineer]
companies: [探迹]
source: ""
status: reviewed
timestamp: 2026-05-26
---

# OpenTelemetry GenAI 语义约定 (Agent 可观测的通用语)

## 问题描述

Agent 可观测性的"通用语"是什么？OpenTelemetry GenAI 约定、OpenInference、OpenLLMetry 三者什么关系？为什么应该收敛到 OTel GenAI？

## 一、为什么 Agent 可观测性需要"通用语"

早期 LLM tracer 各自发明字段名（Langfuse / Arize Phoenix / OpenLLMetry / LangSmith 各一套）。后果：

- 换后端 = 重写 instrumentation。
- 跨框架无法建统一 dashboard、无法算 per-agent 指标、无法关联 trace。

**OpenTelemetry GenAI 语义约定**（`gen_ai.*` 命名空间）就是来解决这个的：一套共享的 span 名 + 属性词表，让任何库产出的 trace 在任何后端都能读。**Langfuse / Phoenix / OpenLLMetry / Laminar 已全部收敛到它**——按标准 instrumentation 是不锁定的做法。

## 二、OTel GenAI 约定的核心

### Operation（span 名）
| Span | operation | 含义 |
| --- | --- | --- |
| 模型调用 | `chat` | 一次 LLM 调用 |
| Agent / 子 agent | `invoke_agent` | 一次 agent 运行 |
| 工具调用 | `execute_tool` | 一次 tool 执行 |
| Embedding | `embeddings` | 向量化调用 |
| Agent 构造 | `create_agent` | agent 实例化 |

### 关键属性（挂在对应 span 上）
| Span | 属性 |
| --- | --- |
| 模型调用 | `gen_ai.request.model` / `gen_ai.usage.input_tokens` / `gen_ai.usage.output_tokens` / `gen_ai.response.finish_reasons` / `gen_ai.provider.name` |
| Agent | `gen_ai.agent.name` / `gen_ai.agent.id` / `gen_ai.conversation.id` |
| 工具 | `gen_ai.tool.name` / `gen_ai.tool.call.id` + arguments + result |

`finish_reasons` 是数组（`["stop"]` / `["tool_calls"]`），区分"答完"还是"要调工具"——agent 调试的关键。

## 三、三大约定对比

| 维度 | OTel GenAI SemConv | OpenInference (Arize) | OpenLLMetry (Traceloop) |
| --- | --- | --- | --- |
| 定位 | OTel 官方标准 | 专为 LLM/agent 设计的约定 | 自动 instrumentation 库 + 约定 |
| 命名空间 | `gen_ai.*` | `llm.*` / `retriever.*` / `tool.*` | `llm.*` |
| Span 类型粒度 | operation 维度 | span kind: LLM/TOOL/AGENT/CHAIN/RETREVER | 类似 OpenInference |
| 自动 instrumentation 覆盖 | 官方 ~7 库 | 30+ 库（LangChain/LlamaIndex/OpenAI/ADK/Mastra/Strands/CrewAI） | 30+ 库（OpenAI/Anthropic/LangChain/向量库） |
| Retrieval/Rerank 一等公民 | 较弱 | ✅ 一等公民 | ✅ |
| 治理 | OTel 社区（慢但稳） | Arize 主导（迭代快） | Traceloop 主导 |

### 选型
- **生产 agent + RAG 重 + 现在就要可调试细节** → OpenInference（full prompt/completion 捕获、retrieval 一等公民、span 类型粒度细、自动 instrumentation 覆盖广）。
- **要厂商中立、不锁定、面向未来** → 直接 OTel GenAI SemConv。
- **现实最佳路径** → 用 OpenInference/OpenLLMetry 自动 instrumentation **产出**，再用 **genainormalizer** 归一化到 OTel GenAI，后端收到的就是 canonical 数据。

## 四、genainormalizer（桥接器）

OTel Collector 的 processor（PR #48062，target semconv v1.41.0），把 OpenInference / OpenLLMetry 属性映射到 OTel GenAI：

```yaml
processors:
  genainormalizer:
    profiles: [openinference, openllmetry]
    remove_originals: true
service:
  pipelines:
    traces:
      processors: [genainormalizer]
```

映射示例：
- `llm.usage.prompt_tokens` (OpenLLMetry) → `gen_ai.usage.input_tokens`
- `llm.token_count.prompt` (OpenInference) → `gen_ai.usage.input_tokens`
- `openinference.span.kind: "LLM"` → `gen_ai.operation.name: "chat"`
- `llm.response.finish_reason: "stop"` → `gen_ai.response.finish_reasons: ["stop"]`（含类型转换 string → string[]）

34 个属性映射跨 2 个 profile，已对 OTel GenAI SemConv registry 验证。

## 五、Agent 一次 turn 的标准 trace 树

```
invoke_agent (root)
├── chat (LLM 调用，决定要调工具)
│   └── finish_reasons: ["tool_calls"]
├── execute_tool (search)
│   └── gen_ai.tool.name=search, args, result
├── chat (基于工具结果再调 LLM)
└── chat (最终回答，finish_reasons: ["stop"])
```

实践中 OpenLLMetry 自动给 OpenAI/Anthropic/LangChain/向量库 instrumentation，OpenAI Agents SDK 默认开 tracing 就发这棵树。

## 易错点

- 自己造字段名 → 后端不认识，dashboard 空。
- `finish_reason` 写成 string 而非 string[] → 不合 semconv。
- 用 OpenInference 又不归一化 → 换后端要重写。

## 延伸

## 延伸

- 关联题：[[ml-ai/observability/agent-trace-span-model]]
- 关联题：[[ml-ai/observability/langfuse-observability-design]]
- 关联题：[[system-design/vertical-observation-pipeline]]
