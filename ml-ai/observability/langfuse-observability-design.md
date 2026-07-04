---
type: question
id: ml-ai/observability/langfuse-observability-design
title: Langfuse 可观测性设计 (v4 observation-centric)
category: ml-ai
subcategory: observability
difficulty: hard
tags: [langfuse, observability, clickhouse, otel, trace-model, llmops]
languages: [python, typescript]
role: [ai-app, sde, backend, devops, ml-engineer]
companies: [探迹]
source: ""
status: reviewed
timestamp: 2026-05-26
---

# Langfuse 可观测性设计 (v4 observation-centric)

## 问题描述

Langfuse 的可观测设计是怎样的？trace / observation / session 模型？存储架构？SDK 怎么用？为什么 v4 改成 observation-centric？

## 一、数据模型：v4 observation-centric（2026-03）

Langfuse v4 把"trace 和 observation 两张表"合并成**单张不可变 observations 宽表**。

| 维度 | Classic 模型 | v4 observation-centric |
| --- | --- | --- |
| 存储 | 独立可变 Traces 表 + Observations 表 | 单张不可变 Observations 表 |
| 上下文属性 | 存在 trace 上，查询时 join | SDK 侧 propagate 到每个 observation |
| Trace input/output | 直接设在 trace 上 | 移除，用 observation IO（旧 LLM-as-judge 依赖 trace IO 的可用 deprecated `set_trace_io`） |
| 可变性 | trace 和 observation 都可变 | observation 不可变（写一次） |

### 关键转变：trace_id 从"顶层实体"降为"关联句柄"

> "The `trace_id` becomes a correlation handle—like `session_id` or `user_id`—rather than its own top-level entity."

一次 agentic trace 现在能含**数千个 operation**，有意思的很少在顶层。把 trace_id 当过滤列（同 session_id / user_id / score）来 group 相关 observation，比"按 trace 浏览"更有力。

## 二、为什么这么改（动机）

1. **agentic trace 太大**：单 trace 含上千 operation，trace 顶层浏览找不到重点。
2. **join 贵**：trace 属性 + observation 分两表，查询要 join，ClickHouse 不擅长。
3. **可变 + 多事件/span**：旧 SDK 一次 span 发多条事件（先发 model+input，后发 output+cost），逼着 Langfuse 用可变表 + 频繁 dedup。不可变宽表消除这个。
4. **实时性**：旧模型 trace 元数据存 S3，慢；AggregatingMergeTree 在 ClickHouse 原生聚合，快。

## 三、存储架构

```
SDK / OTel endpoint
   │  (events)
   ▼
Redis queues → S3 → async workers
   │
   ▼
ClickHouse (analytical engine)
   ├─ observations 宽表 (AggregatingMergeTree, 不可变)
   └─ staging 表 + 微批 job (每 3min + 5min 延迟，把 trace 元数据 join 到 observation)
Postgres (metadata: users/sessions/scores 元信息)
```

- 2024-12 (v3)：trace 数据从 Postgres 迁到 ClickHouse，查询延迟从分钟级降到近实时。
- v4：再进一步，宽表 + 不可变 + AggregatingMergeTree，内存降 3x、分析查询快 20x。
- 兼容老 SDK：后台 job 回填 legacy 数据到新 schema，新 SDK 直接写不可变表。

## 四、SDK v4 用法

### propagate_attributes()（替代 update_current_trace()）
```python
from langfuse import Langfuse
langfuse = Langfuse()

with langfuse.propagate_attributes(user_id="u123", session_id="s456", tags=["prod"]):
    # 在此作用域内创建的所有 observation 自动继承这些属性
    with langfuse.start_as_current_observation(name="agent_run", as_type="span") as obs:
        gen = obs.start_observation(name="llm_call", as_type="generation", model="gpt-4")
        # ... 调模型 ...
        gen.end(output=result)
```

属性通过 **OTel Context + Baggage** 传播到子 observation，无需 join。

### 统一 start_observation(as_type=...)
| v3 | v4 |
| --- | --- |
| `langfuse.start_span(name="x")` | `langfuse.start_observation(name="x")` |
| `langfuse.start_generation(name="x", model="m")` | `langfuse.start_observation(name="x", as_type="generation", model="m")` |

`as_type` 取 `span` / `generation` / `event`，替代 v3 三个独立方法。

## 五、Observation API v2 + Metrics API v2

- 单表查询、强制时间过滤、细粒度字段选择、token 分页（配合 ClickHouse 数据剪枝）。
- **observation 级评测秒级执行**（不用再为每个评测查 ClickHouse）。

## 六、Saved Views（保存的视图）

| 视图 | 配置 |
| --- | --- |
| 关键操作 | 按 observation `name`/`type` 过滤 |
| 最贵 LLM 调用 | `type=generation`，按 `total_cost` 降序 |
| 某用户报错 | `user_id` + `level=ERROR` |
| 某会话慢操作 | `session_id`，按 `latency` 降序 |

## 七、与 OTel 的关系

Langfuse 用 **OTel 做数据 ingestion**（OTLP endpoint），自身 trace 模型是 OTel 兼容的。SDK 基于 OTel Context + Baggage 传播属性。所以 Langfuse 既是 OTel 后端，又在其上叠了 LLM 专属的查询/评测/Score 体系。

## 易错点

- v3 SDK 升 v4 没改 `update_current_trace()` → 属性不会 propagate，查询缺维度。
- 还依赖 trace input/output 做评测 → 用 `set_trace_io` deprecated 方法过渡，或改评测逻辑读 observation IO。
- 老 SDK 不升 → 后台回填有延迟，实时性差。

## 延伸

## 延伸

- 关联题：[[ml-ai/observability/opentelemetry-genai-semantic-conventions]]
- 关联题：[[ml-ai/observability/agent-trace-span-model]]
- 关联题：[[ml-ai/observability/claude-code-hooks-observability]]
