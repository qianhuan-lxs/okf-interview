---
type: question
id: ml-ai/agent/parallel-agent-failure-handling
title: 并行 Agent 失败处理 (部分成功 vs 整体失败)
category: ml-ai
subcategory: agent
difficulty: medium
tags: [multi-agent, parallel, failure-handling, resilience]
languages: []
role: [ai-app, sde, backend]
companies: [北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# 并行 Agent 失败处理 (部分成功 vs 整体失败)

## 问题描述

Luna-AI 框架并行模式多个子 Agent 并发执行机制是什么？聚合结果时如果其中一个 Agent 失败了，Parallel 模式是部分成功还是整体失败？

## 思路

不是二选一，而是 **策略可配置**，默认应是"部分成功 + 标记降级"。

## 解答

### 并发执行机制

- 用 `asyncio.gather` / `ThreadPoolExecutor` / `concurrent.futures` 并发拉起子 agent。
- 每个子 agent 独立调用 LLM、独立超时、独立重试。
- 主流程 `gather(return_exceptions=True)` 收集，避免一个失败导致全崩。

### 失败策略（应支持可配）

| 策略 | 行为 | 适用 |
| --- | --- | --- |
| **Fail-Fast（整体失败）** | 任一失败即抛出、取消其余 | 强一致性任务（如金融汇总） |
| **Partial Success（部分成功）** | 成功的结果照常聚合，失败的位标记 null/降级 | 容忍缺失（多源召回、多视角分析） |
| **Retry-then-Skip** | 单 agent 内重试 N 次仍失败才 skip | 抖动场景 |
| **Quorum** | 成功数 ≥ 阈值才整体成功 | 投票/共识类 |

### 聚合

聚合器根据策略处理：填充默认值、记录失败原因到 trace、给下游 agent 一个"哪些子任务缺了"的元信息，让下游能降级处理。

## 易错点

- 用 `gather()` 不带 `return_exceptions=True`——一个失败全崩，丢失已成功的结果。
- 失败信息不进 trace——后续无法排查为什么聚合结果"少了一块"。

## 延伸

## 延伸

- 关联题：[[ml-ai/agent/multi-agent-orchestration-architecture]]
