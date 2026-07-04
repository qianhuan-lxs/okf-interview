---
type: question
id: ml-ai/agent/agent-framework-selection
title: Agent 框架选型 (ADK / LangChain / LangGraph / Spring AI)
category: ml-ai
subcategory: agent
difficulty: medium
tags: [agent-framework, langchain, langgraph, google-adk, spring-ai, selection]
languages: []
role: [ai-app, sde, backend]
companies: [华大制造, 广州大娱, OPPO, 安克创新, 北京用友]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Agent 框架选型 (ADK / LangChain / LangGraph / Spring AI)

## 问题描述

你熟悉的标准 Agent 框架有哪些？整个架构是什么？LangChain 和 Google ADK 是同时用吗？ADK 的优缺点？能实现三种编排功能吗？

## 思路：按"控制粒度 vs 开箱即用"光谱定位

| 框架 | 语言 | 定位 | 控制粒度 | 优势 | 劣势 |
| --- | --- | --- | --- | --- | --- |
| **LangChain** | Py/JS | 工具/集成大杂烩 | 中 | 集成最全、社区大 | 抽象反复 break change、黑盒 |
| **LangGraph** | Py/JS | 状态图编排 | 高 | 显式状态机、可观测、可控 | 学习曲线、样板代码 |
| **Google ADK** | Py | 声明式多 agent | 中高 | `Sequential/Parallel/LoopAgent` 开箱、与 Gemini/Vertex 深度集成 | 绑定 Google 生态、灵活性弱于 LangGraph |
| **Spring AI** | Java | Spring 风格 AI | 中 | 与 Spring Boot 无缝、Java 团队友好 | 生态新、复杂编排能力弱 |
| **Coze/Dify/n8n** | 低代码 | 可视化 | 低 | 快速搭 demo | 难定制、难版本控制 |

**选型建议：**
- 要 **细粒度状态机 + 可观测** → LangGraph
- 要 **快速搭多 agent + 用 Gemini** → Google ADK
- 要 **Java 后端无缝集成** → Spring AI
- 要 **原型快速验证** → Coze/Dify
- 生产严肃编排不建议只用裸 LangChain（太黑盒）

## 易错点

- 同时混用 LangChain 和 ADK 仅为了"功能拼凑"——会引入两套抽象、两套依赖，维护成本翻倍。混用应只在边界（如 LangChain 做 retriever，ADK 做编排）。

## 延伸

## 延伸

- 关联题：[[ml-ai/agent/multi-agent-orchestration-architecture]]
- 关联题：[[ml-ai/mcp/mcp-protocol-understanding]]
