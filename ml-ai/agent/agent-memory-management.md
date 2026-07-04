---
type: question
id: ml-ai/agent/agent-memory-management
title: Agent 上下文记忆管理 (Memory)
category: ml-ai
subcategory: agent
difficulty: medium
tags: [memory, short-term, long-term, context-management]
languages: []
role: [ai-app, sde, backend]
companies: [中泓一线, 有赞]
source: _interviews/2026-05-louis-ai-java
status: reviewed
timestamp: 2026-05-26
---

# Agent 上下文记忆管理 (Memory)

## 问题描述

Spring AI 用什么实现 memory？基于 mysql？记忆分几个部分？哪几种记忆？每个存储在哪、以什么方式？OpenClaw 核心定位？

## 解答

### 记忆的三层划分

| 类型 | 别名 | 存储位置 | 实现 |
| --- | --- | --- | --- |
| **Short-term / Working** | 会话内 | 进程内 / 内存 / Redis | 对话历史 message list，window 截断 |
| **Long-term / Episodic** | 跨会话事实 | 向量库 / 关系库 | 用户画像、偏好、过往事件，召回注入 |
| **Semantic / Knowledge** | 共享知识 | 向量库 / 知识图谱 | RAG 知识库 |

### Spring AI 的 Memory

- `ChatMemory` 接口，默认 `InMemoryChatMemory`，可换 `RedisChatMemory` / `JdbcChatMemory`（MySQL/Postgres）。
- 按 `conversationId` 维度存 message 列表，注入时取最近 N 条。

### OpenClaw（OpenClaudeMemory 类）

核心定位：**跨会话的个人长期记忆层**。把对话中提取的事实（"用户喜欢用 Go"、"用户在准备面试"）结构化存到向量库 / KV，下次会话开始时召回相关记忆注入 system prompt，实现"记得你"。

### 工程要点

- **窗口策略**：token 超限时，要么滑窗截断、要么摘要压缩、要么向量化旧消息再召回。
- **事实提取**：用一个轻量 model 在每轮结束后抽取"值得长期记住的事实"。
- **隐私 / 衰减**：长期记忆要有 TTL 和用户可删除。

## 延伸

## 延伸

- 关联题：[[ml-ai/rag/rag-full-pipeline]]
- 关联题：[[ml-ai/agent/agent-function-call-mechanism]]
