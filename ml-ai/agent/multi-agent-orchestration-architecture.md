---
type: question
id: ml-ai/agent/multi-agent-orchestration-architecture
title: Multi-Agent 编排架构设计
category: ml-ai
subcategory: agent
difficulty: hard
tags: [multi-agent, orchestration, adk, langgraph, architecture]
languages: []
role: [ai-app, sde, backend]
companies: [华大制造, 广州大娱, OPPO, 中泓一线, 北京用友, 有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Multi-Agent 编排架构设计

## 问题描述

面试官要求描述多 Agent 协作架构是怎么设计、怎么开发的：agent 之间如何交接、串行/并行/分支如何编排、上下文与文件如何在 agent 间流转。

> 来源：华大制造、广州大娱、OPPO、中泓一线、北京用友、有赞均深挖此题。

## 思路

先区分三种经典编排模式，再讲状态/上下文流转，最后讲工程落地。

**编排模式（业界共识的三种）：**

1. **Sequential（串行 / Pipeline）** — 上一个 agent 的输出作为下一个的输入。适合线性工序，如「抽取 → 校验 → 生成」。
2. **Parallel（并行 / Fan-out & Fan-in）** — 多个无依赖子 agent 同时跑，聚合结果。适合多视角分析、多源检索。
3. **Hierarchical / Supervisor（层级 / 路由）** — 一个 supervisor agent 决定把任务路由给哪些 worker agent，可多轮调度。适合开放式任务、工具选择。

**状态与上下文流转：**
- **共享 State**：一个全局 state 对象（dict / dataclass / TypedDict），各 agent 读写。LangGraph 的 `State` + reducer 是典型实现。
- **消息传递**：agent 间通过 message list 交接，保留历史。
- **文件 / 大对象**：不宜放进 LLM context，应落盘到沙箱或对象存储，agent 之间只传**引用（路径 / 句柄）**，由沙箱内的代码 agent 真正消费。

**工程落地要点：**
- 每个子 agent 是独立 `Agent` 实例，有自己的 system prompt、tools、model 配置。
- 编排层负责调度、超时、重试、失败聚合、可观测（trace 每一步的 input/output/token）。
- agent 间交接的数据格式用 **schema 约束**（Pydantic / JSON Schema），让上游输出可被下游解析。

## 解答（以 LangGraph + Google ADK 思路）

```python
# LangGraph: supervisor 路由 + parallel workers
from langgraph.graph import StateGraph, END
from typing import TypedDict, Literal

class State(TypedDict):
    query: str
    docs: list[str]
    answer: str

def retriever(state): ...      # 写 state["docs"]
def writer(state): ...         # 读 docs，写 state["answer"]

g = StateGraph(State)
g.add_node("retriever", retriever)
g.add_node("writer", writer)
g.add_edge("retriever", "writer")
g.add_edge("writer", END)
app = g.compile()
```

Google ADK 的 `SequentialAgent / ParallelAgent / LoopAgent` 是声明式封装，对应上述三种模式；底层仍是 state 在 agent 间流转。

## 易错点

- **把文件塞进 context** 而不是传引用——上下文爆炸且不可复用。
- **并行模式不处理失败聚合**——一个子 agent 失败就整体崩，缺少 partial-success 策略（见 [[ml-ai/agent/parallel-agent-failure-handling]]）。
- **状态 schema 不固定**——下游 agent 解析上游输出时频繁报错。

## 延伸

## 延伸

- 关联题：[[ml-ai/agent/parallel-agent-failure-handling]]
- 关联题：[[ml-ai/agent/agent-framework-selection]]
- 关联题：[[ml-ai/agent/multi-agent-common-architectures]]
